"""Static schema-binding check for every SQL query the apps/scripts run.

pyflakes/vulture/bandit all operate on Python syntax -- none of them understand
SQL, so a query that references a column or table that doesn't exist (a stale
name after a rename, a typo, a copy-paste from a different view) is invisible
to all three. It's also invisible to verify_transfer.py, which only runs the
specific queries its own checks happen to use. For a Streamlit app, that means
a broken query can sit undetected on any page/widget the smoke test doesn't
click through to -- see DAILY_REVIEW.md 2026-10-03 for the fifth-tool
evaluation this script was built for.

This recovers every literal SQL string passed to q()/qdf() (app_hierarchy.py,
app_llc.py) or con.execute()/cur.execute() (the build/support scripts) via the
`ast` module -- so it sees exactly what Python sees, not a regex approximation
-- and validates each one with DuckDB's PREPARE statement against the live
corpus.duckdb schema. PREPARE type-checks and resolves every table/column
name without requiring bound parameter values, so a query with `?`
placeholders validates cleanly without needing real inputs.

Only plain (non f-string) string literals are checked -- f-string SQL is
already covered by the project's own `execute(f"` grep audit, and an f-string
assembles its table/column names at runtime, so this check would only ever
validate a query shaped by whatever constants happen to be active. Each
matched call's query text must be either a bare Str/Constant or a Str
concatenated with `+`/implicit adjacency, which covers every call site in this
codebase as of 2026-10-03.

Scope is deliberately the read-only analysis/app layer (the default file list
below), not build_corpus_db.py/build_links.py/build_okoz.py/build_llc.py.
Those scripts run CREATE TABLE/VIEW and rely on a CREATE TEMP TABLE from an
earlier statement in the same pipeline run (e.g. build_corpus_db.py's `uz`
temp table) -- PREPARE-ing one of their statements in isolation against a
bare schema throws on both counts, and neither is a real bug: a successful
`python build_*.py` run already proves every one of those queries parses and
binds, the same way a crash would reveal a typo immediately. The actual gap
this closes is the app layer: app_hierarchy.py/app_llc.py's queries only run
when a person clicks that exact page/widget, and the existing HTTP-200 smoke
test doesn't exercise most of them -- confirmed with a mutation test (see the
2026-10-03 log entry): a deliberately typo'd column in a scratch copy of
app_llc.py was caught immediately, with the exact line and query.
"""
from __future__ import annotations

import ast
import sys

import duckdb

DB_PATH = "corpus.duckdb"
CALL_NAMES = {"q", "qdf", "execute"}


def _literal_str(node: ast.AST) -> str | None:
    """Best-effort: a plain string constant, or a chain of string-literal concatenations."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal_str(node.left), _literal_str(node.right)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.JoinedStr):
        return None  # f-string: out of scope, covered by the separate grep audit
    return None


def find_queries(path: str) -> list[tuple[int, str]]:
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else (
            func.attr if isinstance(func, ast.Attribute) else None)
        if name not in CALL_NAMES or not node.args:
            continue
        sql = _literal_str(node.args[0])
        if sql is not None and sql.strip():
            found.append((node.lineno, sql))
    return found


def main() -> int:
    con = duckdb.connect(DB_PATH, read_only=True)
    files = sys.argv[1:] or [
        "app_hierarchy.py", "app_llc.py", "verify_transfer.py",
        "score_gold.py", "measure_extractor_recall.py",
        "build_gold_sample.py", "build_gold_sample_novel.py",
    ]
    total = 0
    failures = []
    for path in files:
        for lineno, sql in find_queries(path):
            total += 1
            stmt_name = f"chk_{total}"
            try:
                con.execute(f"PREPARE {stmt_name} AS {sql}")
                con.execute(f"DEALLOCATE {stmt_name}")
            except duckdb.Error as e:
                failures.append((path, lineno, str(e).splitlines()[0], sql.strip()[:200]))

    print(f"checked {total} literal SQL queries across {len(files)} files")
    if failures:
        print(f"\n{len(failures)} FAILED schema binding:")
        for path, lineno, err, sql in failures:
            print(f"  {path}:{lineno}  {err}")
            print(f"    {sql}")
        return 1
    print("all queries bind cleanly against the current schema")
    return 0


if __name__ == "__main__":
    sys.exit(main())
