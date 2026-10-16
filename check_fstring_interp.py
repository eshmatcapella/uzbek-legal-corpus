"""AST-based audit of every f-string SQL interpolation, replacing the
grep-based "third Cleanup check" (`grep -n 'execute(f"' *.py`, added
2026-09-26) with something that can't miss a call site just because its
opening paren and its f-string literal sit on different lines.

Measured gap (2026-10-12): the grep pattern is a single-line literal match,
so `conn.execute(\n    f"...")` -- a multi-line call, where the f-string
isn't on the same source line as `execute(` -- is invisible to it. That
shape turned out to be real, not hypothetical: `test_transfer_e2e.py` has
20 such call sites, none of which any prior Cleanup rotation's grep audit
ever saw (the file never showed up in the grep's own output). One of those
20 turned out to be an actual violation of the project's own f-string-SQL
rule -- `query_db_article_text_en()`'s `else` branch interpolated `norm_id`,
a value derived at runtime from parsing the English markdown fixture, not a
hardcoded constant -- fixed in the same commit that added this script by
parameterizing it (`article_number = ?` + a bound param) rather than adding
it to this script's allowlist.

Measured gap (2026-10-16): the original version of this script only
matched calls whose first *argument* was literally an `ast.JoinedStr` --
`conn.execute(f"...")` -- so `query = f"..."` followed by
`conn.execute(query)` on a later line was invisible to it, not merely
unresolved: the call never even entered `find_calls()`'s result set, so it
didn't count toward "checked N calls" either. Proved with a mutation test
(see the 2026-10-16 log entry): a scratch copy of `test_transfer_e2e.py`
with a runtime-derived value spliced into exactly this indirected shape
passed clean, with the same "checked 19 calls" count before and after the
mutation. Measuring the real population across the whole codebase found
exactly 6 `execute(<bare name>)` call sites total: the 4 `q()`/`qdf()`
helper definitions in `app_hierarchy.py`/`app_llc.py` (already excluded by
name from `check_sql_bindings.py`'s own scope, not this script's concern),
one in `measure_extractor_recall.py` whose variable holds a fully literal
string with zero interpolation, and one real f-string-via-variable case in
`test_transfer_e2e.py::test_r3_alignment_key_matching` (`query = f"...
{PARQUET_PATH}..."` then `self.conn.execute(query)`) -- safe today
(`PARQUET_PATH` is a SCREAMING_CASE module constant) but reachable from
this script's own blind spot before the fix below, exactly the way the
`query_db_article_text_en()` bug this script was built to catch would have
been invisible too, had it been written one assignment away from its
`execute(` call instead of inline.

Method: AST-walk every `*.execute(...)` call whose first argument is an
f-string (`ast.JoinedStr`) *or* a bare name that traces back (through the
same intra-function `Assign` resolution used below) to at least one
f-string, regardless of line layout, and recursively resolve each
top-level interpolated expression (or, for the indirected case, the whole
traced value):
  - a SCREAMING_CASE name/attribute (this project's own consistent
    convention for a module-level constant, e.g. `CC_GENERAL_PART`,
    `cx.DOC_GENERAL`) is safe;
  - a plain string literal is safe;
  - an f-string is safe iff every one of ITS interpolations is (recursively);
  - a call whose own callable chain resolves to a SCREAMING_CASE root
    (`PARQUET.as_posix()`) is safe;
  - a `+`-concatenation is safe iff both sides are;
  - a bare name with no safe resolution is traced to every `Assign` to that
    name *within the same function*; if every one of those right-hand sides
    resolves safe (recursively), so does the name -- this is what lets
    `raw`/`where_clause` be proven safe from their own source instead of
    trusted by name (see the mutation test in the 2026-10-12 log entry: an
    earlier draft of this script allowlisted the bare name `where_clause`
    and failed to catch the pre-fix `norm_id` bug, since the name was
    unchanged -- that's why resolution is structural, not name-based).
A handful of shapes this can't resolve at all without inter-procedural
analysis (a parameter, a loop variable, this tool's own internal plumbing)
are listed in IRREDUCIBLE below, each with a one-line reason hand-verified
against every call site, not trusted by name alone.

This check does not replace check_sql_bindings.py (which validates
*non*-f-string literal SQL against the live schema) -- it covers the
complementary f-string half that tool's own docstring explicitly defers.

Run: python check_fstring_interp.py [FILE ...]
"""
from __future__ import annotations

import ast
import glob
import sys

EXCLUDE_FILES = {"check_fstring_interp.py"}

# bare names that can't be resolved by this script's intra-function Assign
# trace alone (a parameter, a loop variable, a counter) -> why they're safe
# anyway, hand-verified against every call site, not trusted by name.
IRREDUCIBLE = {
    "doc_id": "build_links.py loop variable; ranges only over the fixed "
              "2-tuple CC_DOCS, never external input (audited 2026-10-01)",
    "parquet_path": "test_transfer_e2e.py parameter; its one call site "
                     "always passes the PARQUET_PATH constant",
    "stmt_name": "check_sql_bindings.py's own internal PREPARE/DEALLOCATE "
                 "name, generated from a counter, never external input",
    "sql": "check_sql_bindings.py's own internal PREPARE target: the "
           "already-parsed literal SQL text of the call site under test, "
           "not external input",
    "','.join('?' * len(REPEALED_COMPANY_ARTICLES))": "build_llc.py; "
        "generates bound-parameter placeholders from a hardcoded "
        "constant's length, not interpolated data (audited 2026-10-03)",
}


def _screaming_root(node: ast.AST) -> bool:
    """True for a SCREAMING_CASE name/attribute access, or a method call on one
    (PARQUET.as_posix()) -- calling a method never changes what the SQL text
    says, only a *value substituted into* it would."""
    if isinstance(node, ast.Call):
        return _screaming_root(node.func)
    if isinstance(node, ast.Attribute):
        if node.attr.isidentifier() and node.attr == node.attr.upper() and any(c.isalpha() for c in node.attr):
            return True
        return _screaming_root(node.value)
    if isinstance(node, ast.Name):
        return node.id.isidentifier() and node.id == node.id.upper() and any(c.isalpha() for c in node.id)
    return False


def _is_safe(node: ast.AST, assigns_by_name: dict[str, list[ast.AST]], seen: set[str]) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    if ast.unparse(node) in IRREDUCIBLE:
        return True
    if _screaming_root(node):
        return True
    if isinstance(node, ast.JoinedStr):
        return all(_is_safe(v.value, assigns_by_name, seen) for v in node.values
                   if isinstance(v, ast.FormattedValue))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _is_safe(node.left, assigns_by_name, seen) and _is_safe(node.right, assigns_by_name, seen)
    if isinstance(node, ast.Name):
        if node.id in IRREDUCIBLE:
            return True
        if node.id in seen:
            return False  # cycle guard
        rhses = assigns_by_name.get(node.id)
        if not rhses:
            return False  # a parameter or otherwise-unassigned name, not in IRREDUCIBLE
        return all(_is_safe(rhs, assigns_by_name, seen | {node.id}) for rhs in rhses)
    return False


def _contains_joinedstr(node: ast.AST, assigns_by_name: dict[str, list[ast.AST]], seen: set[str] | None = None) -> bool:
    """True if resolving `node` passes through at least one f-string literal --
    i.e. this call is in this script's scope at all, independent of whether it
    turns out safe. Mirrors _is_safe's own traversal shape so a Name is chased
    through the same intra-function Assign chain."""
    seen = seen or set()
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _contains_joinedstr(node.left, assigns_by_name, seen) or _contains_joinedstr(node.right, assigns_by_name, seen)
    if isinstance(node, ast.Name):
        if node.id in seen:
            return False  # cycle guard
        return any(_contains_joinedstr(rhs, assigns_by_name, seen | {node.id})
                   for rhs in assigns_by_name.get(node.id, []))
    return False


def _assigns_by_name(func: ast.AST) -> dict[str, list[ast.AST]]:
    out: dict[str, list[ast.AST]] = {}
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            out.setdefault(node.targets[0].id, []).append(node.value)
    return out


def find_calls(path: str) -> list[tuple[int, list[ast.AST], dict[str, list[ast.AST]]]]:
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    # map every node to its nearest enclosing function (or the module itself)
    scope_of: dict[int, ast.AST] = {}
    def walk_scope(node: ast.AST, scope: ast.AST):
        scope_of[id(node)] = scope
        for child in ast.iter_child_nodes(node):
            next_scope = child if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else scope
            walk_scope(child, next_scope)
    walk_scope(tree, tree)

    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute" and node.args):
            continue
        scope = scope_of.get(id(node), tree)
        assigns = _assigns_by_name(scope)
        arg0 = node.args[0]
        if isinstance(arg0, ast.JoinedStr):
            exprs = [v.value for v in arg0.values if isinstance(v, ast.FormattedValue)]
        elif isinstance(arg0, ast.Name) and _contains_joinedstr(arg0, assigns):
            # indirected: the argument itself (not just one of its sub-expressions)
            # is what must resolve safe, via the same Name-chasing _is_safe already does.
            exprs = [arg0]
        else:
            continue
        found.append((node.lineno, exprs, assigns))
    return found


def main() -> int:
    paths = sys.argv[1:] or [p for p in sorted(glob.glob("*.py")) if p not in EXCLUDE_FILES]
    total_calls = 0
    flagged = []
    for path in paths:
        for lineno, exprs, assigns in find_calls(path):
            total_calls += 1
            for expr in exprs:
                if not _is_safe(expr, assigns, set()):
                    flagged.append((path, lineno, ast.unparse(expr)))

    print(f"checked {total_calls} f-string execute() calls across {len(paths)} files")
    if flagged:
        print(f"\n{len(flagged)} interpolated expression(s) that don't resolve to a hardcoded constant:")
        for path, lineno, expr in flagged:
            print(f"  {path}:{lineno}  {{{expr}}}")
        return 1
    print("every interpolated expression resolves to a hardcoded constant or a verified IRREDUCIBLE entry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
