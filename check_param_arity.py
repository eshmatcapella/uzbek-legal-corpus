"""Static placeholder/argument-count check for every parameterized SQL call.

The project's existing schema checks -- check_sql_bindings.py (PREPARE against
the live schema) and check_fstring_interp.py (f-string interpolation safety) --
both validate the SQL TEXT. Neither one ever binds real parameter values:
check_sql_bindings.py calls PREPARE/DEALLOCATE only, deliberately never EXECUTE,
so it proves every table/column name resolves but says nothing about whether
the number of `?` placeholders in a query matches the number of values the
call site actually supplies. That mismatch only surfaces at real EXECUTE time
(confirmed directly: `PREPARE ... AS SELECT ... WHERE a = ? AND b = ?` followed
by `EXECUTE ...(1)` -- one value for two placeholders -- raises "Values were
not provided for the following parameters", something PREPARE alone never
catches) -- the same "invisible until that exact code path actually runs"
shape check_sql_bindings.py/check_fstring_interp.py were each built to close
for schema typos and f-string safety respectively, just one level down: a
column that exists but whose bound value silently comes from the wrong
position (or is missing entirely) in a Streamlit page nobody has clicked
through yet, or a con.executemany() row tuple that's one element short of its
own INSERT's column list.

This is purely syntactic -- no live `?` count vs. supplied-argument count ever
depends on runtime data, so unlike check_sql_bindings.py this needs no DuckDB
connection and checks every *.py file, including build_corpus_db.py/
build_links.py/build_okoz.py/build_llc.py (out of scope for check_sql_bindings.py
only because PREPARE-ing a CREATE-TABLE-dependent statement in isolation fails
on schema grounds that have nothing to do with arity).

For q()/qdf()/execute(sql, params) the row is `params` itself: resolves to a
List/Tuple literal's own element count directly, or via assigns_by_name's
same intra-function Assign chase the sibling checks already use. For
con.executemany(sql, rows), each element of `rows` is its own row: resolves
List literals of List/Tuple elements directly, a ListComp's `elt` shape (one
arity for every generated row), or an empty-list-then-`.append(<tuple>)`
pattern (collects the arity of every literal-shaped append call in the same
function). Any branch that isn't literal-shaped -- a parameter, a function
call, a dynamically-sized list -- is left unresolved and skipped entirely,
same conservative precedent as the sibling checks: this only ever flags a
PROVABLE mismatch, never a guess.

The placeholder count itself also needs more than a bare literal string: four
real call sites (`link_edge`/29, `article_amendment`/13, `llc_norm`/11,
`repeal_clause`/10 -- all wide INSERTs) build their `?, ?, ...` column list via
`",".join("?" * n)` rather than typing it out, which a plain Constant-string
resolver can't see through. Extends the literal resolver with `str * int`
(BinOp Mult) and `str.join(...)` of a resolvable separator/iterable so those
four resolve too, instead of silently falling outside this check's coverage.
"""
from __future__ import annotations

import ast
import re
import sys

from ast_scope import assigns_by_name, build_scope_map

CALL_SINGLE = {"q", "qdf", "execute"}
CALL_MANY = {"executemany"}

_STRIP_STR_LITERAL = re.compile(r"'(?:[^'\\]|\\.)*'")


def count_placeholders(sql: str) -> int:
    """Count `?` outside quoted SQL string literals (e.g. a LIKE '...?...')."""
    return _STRIP_STR_LITERAL.sub("''", sql).count("?")


def _resolve_strs(node: ast.AST, assigns: dict, seen: frozenset) -> list[str] | None:
    """Resolve node to every literal string it could be, or None if any
    reachable branch isn't provably a plain string (mirrors check_sql_bindings.py's
    _literal_str, extended with str*int repetition and str.join())."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        lefts = _resolve_strs(node.left, assigns, seen)
        rights = _resolve_strs(node.right, assigns, seen)
        if lefts is None or rights is None:
            return None
        return [l + r for l in lefts for r in rights]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        str_side, int_side = (node.left, node.right)
        strs = _resolve_strs(str_side, assigns, seen)
        if strs is None:
            strs = _resolve_strs(int_side, assigns, seen)
            int_side = node.left if strs is not None else None
        n = int_side.value if isinstance(int_side, ast.Constant) and isinstance(int_side.value, int) else None
        if strs is None or n is None:
            return None
        return [s * n for s in strs]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "join" \
            and len(node.args) == 1:
        seps = _resolve_strs(node.func.value, assigns, seen)
        if seps is None:
            return None
        arg = node.args[0]
        pieces = _resolve_strs(arg, assigns, seen)
        if pieces is None and isinstance(arg, (ast.List, ast.Tuple)):
            resolved_elts = [_resolve_strs(e, assigns, seen) for e in arg.elts]
            if all(r is not None and len(r) == 1 for r in resolved_elts):
                pieces = ["".join(r[0] for r in resolved_elts)]
        if pieces is None:
            return None
        out = []
        for sep in seps:
            for whole in pieces:
                out.append(sep.join(whole))  # str.join(str) iterates characters
        return out
    if isinstance(node, ast.JoinedStr):
        return None
    if isinstance(node, ast.Name):
        if node.id in seen:
            return None
        rhses = assigns.get(node.id)
        if not rhses:
            return None
        out = []
        for rhs in rhses:
            resolved = _resolve_strs(rhs, assigns, seen | {node.id})
            if resolved is None:
                return None
            out.extend(resolved)
        return out
    return None


def _literal_arity(node: ast.AST, assigns: dict, seen: frozenset) -> int | None:
    """If node is provably a fixed-length List/Tuple (directly, or via a
    single resolvable assignment), return its element count. No attempt to
    resolve the *values* -- only the shape, which is all arity-checking needs."""
    if isinstance(node, (ast.List, ast.Tuple)):
        return len(node.elts)
    if isinstance(node, ast.Name):
        if node.id in seen:
            return None
        rhses = assigns.get(node.id)
        if not rhses or len(rhses) != 1:
            return None
        return _literal_arity(rhses[0], assigns, seen | {node.id})
    return None


def _append_arities(scope: ast.AST, target: str, assigns: dict) -> list[int]:
    """Every `target.append(<literal-shaped row>)` call anywhere in `scope`."""
    out = []
    for node in ast.walk(scope):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "append" and isinstance(node.func.value, ast.Name)
                and node.func.value.id == target and len(node.args) == 1):
            arity = _literal_arity(node.args[0], assigns, frozenset())
            if arity is not None:
                out.append(arity)
    return out


def _row_arities_many(node: ast.AST, assigns: dict, scope: ast.AST) -> list[int]:
    """Every resolvable per-row arity for a con.executemany() rows argument."""
    if isinstance(node, ast.List):
        arities = [_literal_arity(e, assigns, frozenset()) for e in node.elts]
        return [a for a in arities if a is not None]
    if isinstance(node, ast.ListComp) and len(node.generators) == 1:
        a = _literal_arity(node.elt, assigns, frozenset())
        return [a] if a is not None else []
    if isinstance(node, ast.Name):
        rhses = assigns.get(node.id)
        if not rhses or len(rhses) != 1:
            return []
        rhs = rhses[0]
        if isinstance(rhs, ast.List) and len(rhs.elts) == 0:
            return _append_arities(scope, node.id, assigns)
        return _row_arities_many(rhs, assigns, scope)
    return []


def check_file(path: str) -> list[tuple]:
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src, filename=path)
    scope_of = build_scope_map(tree)
    findings = []
    checked = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else None)
        if name not in CALL_SINGLE | CALL_MANY or not node.args:
            continue
        scope = scope_of.get(id(node), tree)
        assigns = assigns_by_name(scope)
        sqls = _resolve_strs(node.args[0], assigns, frozenset())
        if not sqls:
            continue
        for sql in sqls:
            if not sql.strip():
                continue
            n_q = count_placeholders(sql)
            if n_q == 0:
                checked += 1
                continue
            if len(node.args) < 2:
                findings.append((path, node.lineno, n_q, "(no params argument)", sql.strip()[:150]))
                continue
            if name in CALL_MANY:
                arities = sorted(set(_row_arities_many(node.args[1], assigns, scope)))
            else:
                a = _literal_arity(node.args[1], assigns, frozenset())
                arities = [a] if a is not None else []
            if not arities:
                continue  # unresolvable rows/params shape -- skip, same precedent as the sibling checks
            checked += 1
            bad = [a for a in arities if a != n_q]
            if bad:
                findings.append((path, node.lineno, n_q, bad, sql.strip()[:150]))

    return findings, checked


def main() -> int:
    files = sys.argv[1:] or sorted(
        p for p in __import__("glob").glob("*.py")
        if p not in {"check_param_arity.py"}
    )
    total_checked = 0
    all_findings = []
    for path in files:
        findings, checked = check_file(path)
        total_checked += checked
        all_findings.extend(findings)

    print(f"checked {total_checked} parameterized SQL calls (with >=1 placeholder, "
          f"resolvable row shape) across {len(files)} files")
    if all_findings:
        print(f"\n{len(all_findings)} ARITY MISMATCH(ES):")
        for path, lineno, n_q, found, sql in all_findings:
            print(f"  {path}:{lineno}  {n_q} placeholder(s), row shape gives {found}")
            print(f"    {sql}")
        return 1
    print("every resolvable call's row shape matches its own query's placeholder count")
    return 0


if __name__ == "__main__":
    sys.exit(main())
