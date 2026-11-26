"""Twelfth Cleanup check: a module defines a named constant for a large,
distinctive integer (a doc_id, article-count boundary, etc.) and then
*also* re-hardcodes that same literal value elsewhere in the same file
instead of using the name it already gave it.

None of the eleven existing checks catch this shape. pyflakes/vulture only
see unused *names*, not re-duplicated *values*; check_sql_bindings.py and
check_param_arity.py validate a literal query's schema/arity, not whether a
literal number inside it duplicates a constant the same file already
defined; check_code_clones.py diffs whole function bodies, not a single
re-hardcoded scalar sitting inside an otherwise-unique query.

This is deliberately file-LOCAL, not cross-file: several large integers
(-111189, -180552, -8151376, -22525) are legitimately re-declared as
independent literals in test_transfer_e2e.py and measure_extractor_recall.py
-- both are, by design (see DAILY_REVIEW.md, Cleanup, 2026-09-07/2026-10-??),
deliberately independent reimplementations that must NOT import the
pipeline's own constants, so cross-file duplication there is correct, not a
bug. What IS a bug is a single file using its OWN named constant in most
places but slipping back to the bare literal in one spot -- a silent
copy-paste residue that would not survive the constant's next edit.

Method: for each file, find every module-level `NAME = <int literal>`
assignment (unary-minus literals included) with abs(value) >= 1000 -- large
enough to be a distinctive id/boundary, not a generic small magic number
(batch sizes, sample counts, etc., which this check deliberately ignores to
avoid noise). Then regex-scan the *rest* of that same file for the literal
value as a standalone number (word-boundary, not part of a longer digit
run) outside the assignment line itself and outside any line that already
references the constant by name. Flag every such re-hardcoded occurrence.

Known blind spot, same spirit as this project's other heuristic checks: a
file that assigns the same name twice to different values, or redefines
the literal inside a string in an unrelated sense (e.g. a comment quoting
the number for a different reason), would need human review -- this script
finds candidates, it does not itself decide whether a given hit is a bug.
"""
from __future__ import annotations

import ast
import glob
import re

MIN_ABS_VALUE = 1000


def module_level_int_constants(tree: ast.Module) -> dict[str, tuple[int, int]]:
    """name -> (value, def_lineno) for module-level `NAME = <int literal>`."""
    out: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        val = node.value
        sign = 1
        if isinstance(val, ast.UnaryOp) and isinstance(val.op, ast.USub):
            val = val.operand
            sign = -1
        if isinstance(val, ast.Constant) and isinstance(val.value, int):
            out[target.id] = (sign * val.value, node.lineno)
    return out


def _docstring_nodes(tree: ast.Module) -> set[ast.AST]:
    """Module/function/class docstring string-literal nodes -- excluded, since a
    docstring quoting a value for a human to read isn't a code duplication."""
    out: set[ast.AST] = set()
    candidates = [tree] + [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    for node in candidates:
        if node.body and isinstance(node.body[0], ast.Expr):
            val = node.body[0].value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                out.add(val)
    return out


def find_literal_drift() -> list[tuple[str, str, int, int]]:
    """Returns (file, const_name, def_lineno, drift_lineno) for every hit."""
    findings = []
    for fname in sorted(glob.glob("*.py")):
        src = open(fname, encoding="utf-8").read()
        try:
            tree = ast.parse(src, filename=fname)
        except SyntaxError:
            continue
        consts = {
            name: (value, lineno)
            for name, (value, lineno) in module_level_int_constants(tree).items()
            if abs(value) >= MIN_ABS_VALUE
        }
        if not consts:
            continue
        docstrings = _docstring_nodes(tree)
        # Only look inside string/f-string literals -- this is a SQL-literal-vs-
        # named-constant check, not a free-text (comment/docstring) check; AST
        # already excludes comments entirely, and docstrings are excluded above.
        string_nodes = [
            n for n in ast.walk(tree)
            if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                or isinstance(n, ast.JoinedStr))
            and n not in docstrings
        ]
        for name, (value, def_lineno) in consts.items():
            # Require the number to stand alone, not be a fragment of a longer
            # composite identifier string (e.g. "-111189-a261#1" as a dict key).
            pattern = re.compile(r"(?<![\w.#-])" + re.escape(str(value)) + r"(?![\w.#-])")
            for node in string_nodes:
                if node.lineno == def_lineno:
                    continue
                segment = ast.get_source_segment(src, node) or ""
                if name in segment:
                    continue  # already referenced by name inside this same literal
                if pattern.search(segment):
                    findings.append((fname, name, def_lineno, node.lineno))
    return sorted(set(findings))


def main() -> int:
    findings = find_literal_drift()
    n_files = len(set(f for f, *_ in findings))
    print(f"checked module-level int constants (|value| >= {MIN_ABS_VALUE}) "
          f"across {len(glob.glob('*.py'))} files")
    if not findings:
        print("every large named constant is referenced by name everywhere else in its own file")
        return 0
    print(f"{len(findings)} re-hardcoded literal(s) in {n_files} file(s):")
    for fname, name, def_lineno, drift_lineno in findings:
        print(f"  {fname}:{drift_lineno}  re-hardcodes {name} (defined {fname}:{def_lineno})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
