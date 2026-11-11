"""Shared intra-function scope resolution for the AST-based Cleanup checks.

check_fstring_interp.py and check_sql_bindings.py each need the same two
primitives to chase a bare name back to its own assignment(s) before
deciding whether a SQL-bearing argument is safe/resolvable: (1) map every
AST node to its nearest enclosing function (or the module itself), so a
name is only resolved against assignments in ITS OWN scope, never a
same-named variable in an unrelated function; (2) collect every `Assign`
to a given name within one scope. Both scripts built this identically and
independently (check_sql_bindings.py's 2026-11-04 fix to trace plain-literal
indirection copied check_fstring_interp.py's 2026-10-16 version verbatim) --
check_code_clones.py flagged the resulting pair at 1.000 similarity the same
day, the exact duplicated-helper shape this project has already extracted
out from under itself once before (gold_sampling.py, 2026-11-01). Extracted
here rather than left as a second copy.
"""
from __future__ import annotations

import ast


def build_scope_map(tree: ast.AST) -> dict[int, ast.AST]:
    """Map id(node) -> nearest enclosing FunctionDef/AsyncFunctionDef, or the
    module `tree` itself for anything at module level."""
    scope_of: dict[int, ast.AST] = {}

    def walk(node: ast.AST, scope: ast.AST):
        scope_of[id(node)] = scope
        for child in ast.iter_child_nodes(node):
            next_scope = child if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else scope
            walk(child, next_scope)

    walk(tree, tree)
    return scope_of


def assigns_by_name(scope: ast.AST) -> dict[str, list[ast.AST]]:
    """Every `Assign`/`AnnAssign` right-hand side within `scope`, keyed by the
    assigned name. Only single-target `Name = ...` (or annotated `Name: T =
    ...`) assignments count -- the shape every call site in this codebase
    actually uses for a query/SQL/row-accumulator variable.

    `AnnAssign` (`rows: list[list] = []`) is a distinct AST node from `Assign`
    (it has one bare `.target`, not a `.targets` list) and was missed
    entirely before 2026-11-11 -- every `name: list[...] = []` initializer in
    this codebase (e.g. build_corpus_db.py's `assignments`/`updates`/`report`,
    build_links.py's `edges`/`clauses`/`amend_rows`, build_llc.py's `rows`)
    resolved to "no assignment found" rather than "resolves to an empty
    list", silently treating a real, later-populated accumulator the same as
    an unassigned name. Found while building check_param_arity.py (7/59
    parameterized-call sites unresolved, all seven exactly this pattern);
    fixed here since both check_sql_bindings.py and check_fstring_interp.py
    import this same helper and would hit the identical gap the moment either
    one's own file scope grows a type-annotated accumulator."""
    out: dict[str, list[ast.AST]] = {}
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            out.setdefault(node.targets[0].id, []).append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            out.setdefault(node.target.id, []).append(node.value)
    return out
