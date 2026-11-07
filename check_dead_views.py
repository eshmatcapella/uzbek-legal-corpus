"""Dead/write-only view check -- check_dead_columns.py's column-grain idea,
one level up at the view grain, now with transitive closure.

check_dead_columns.py already asks "is this base-table column ever read back
by anything downstream?" for columns. It deliberately excludes views
(`CREATE ... AS SELECT` objects), treating their output columns as already
covered by check_sql_bindings.py's referential check. But nothing asks the
same read/write-asymmetry question about the *view itself*: a `CREATE OR
REPLACE VIEW` the build pipeline faithfully (re)builds on every run, that no
app, no verify_transfer.py check, and no other view ever actually queries
from. That's real wasted build-pipeline surface of exactly the same shape
check_dead_columns.py already looks for, just invisible to it because it
scopes to `table_schema = 'main'` base tables only.

Method, in two layers:

1. **View dependency graph.** Pull every view's authoritative SQL straight
   from `duckdb_views()` (not grepped Python source -- the live catalog's own
   text, immune to f-string/string-building formatting noise) and record
   `dep_graph[A] = {B, ...}` for every other real view `B` that `A`'s own
   definition selects from (`FROM`/`JOIN B` inside A's SQL). As of this
   session, corpus-wide, there is exactly one such edge:
   `v_llc_realization -> v_act_currency`.

2. **Root usage.** Grep every `*.py` file (this script's own excluded, same
   reason check_dead_columns.py excludes itself) for a `FROM`/`JOIN <view>`
   hit, exactly as before -- but a hit only counts as a genuine root use if
   it falls OUTSIDE every view's own `CREATE VIEW` definition block. Those
   blocks are located precisely via `ast.parse()` on each build script (not
   regex line-matching): find the `Constant`/`JoinedStr` string argument to
   `con.execute(...)` whose text contains `CREATE [OR REPLACE] VIEW <name>`,
   and take that node's `(lineno, end_lineno)` as the block -- a `FROM
   v_act_currency` on build_llc.py:285 (inside `v_llc_realization`'s own
   multi-line definition) is excluded from v_act_currency's root-use count
   for exactly this reason: it's a dependency-graph edge (layer 1 already
   captured it), not an independent consumer.

3. **Closure.** `live = root_used`; repeatedly add any `B` reachable via
   `dep_graph` from a live view, until fixed point. A view with zero root
   uses AND unreachable from any live view through the dependency graph is
   flagged dead -- whether it's queried directly by nothing, or only by a
   view that is itself only ever queried by nothing.

This replaces the one-level version's actual blind spot (closed 2026-11-07):
previously, "B is used" meant "some line somewhere matches FROM/JOIN B", with
no check on whether that line was itself just A's own (possibly equally dead)
view definition -- so a fully dead `A -> B` chain would have had the script
print "every view is queried somewhere" while being structurally unable to
say so correctly. Verified the fix actually changes behavior, not just
re-derives the same answer by a longer route: a toy graph (`dep_graph =
{"A": {"B"}}`, zero root uses for either) run through the SAME closure
function here correctly reports both A and B dead; a line-count of the kind
the old script effectively did on that same toy graph ("B appears after
FROM/JOIN somewhere" with no root-vs-internal distinction) would have called
B used. On the live schema today, `v_llc_realization` and `v_act_currency`
each independently have real, non-view root uses (`app_llc.py`,
`app_hierarchy.py`, `verify_transfer.py` for v_act_currency; `app_llc.py:218`
for v_llc_realization) -- so today's answer is unchanged (10/10 live), but it
is now an actually-checked guarantee instead of a hand-verified one; the
backlog question of whether this closure was worth building at all is
answered: yes, built, and it changes nothing on today's schema but will catch
the shape the moment any PR makes it real.

Remaining known blind spot, same spirit as this project's other heuristic
checks: a view queried only through a Python string built up across multiple
lines (not a single `FROM <name>`/`JOIN <name>` on one line) would be
invisible to the root-use grep -- not a pattern this codebase uses today
(checked by hand), same acknowledged limit as check_dead_columns.py's
`row[3]` positional-read blind spot. The dependency graph itself (layer 1)
has no such blind spot -- it reads the catalog's fully-rendered SQL, not
Python source.

Found and hand-verified one real dead view on 2026-10-29 (`v_llc_skeleton`,
since retired by a later session -- see DAILY_REVIEW.md); none found by this
closure as of 2026-11-07.
"""
from __future__ import annotations

import ast
import glob
import re
import sys

import duckdb

DB_PATH = "corpus.duckdb"

DEF_RE = re.compile(r"CREATE\s+(OR\s+REPLACE\s+)?VIEW\s+(\w+)\b")
QUERY_RE_TMPL = r"\b(FROM|JOIN)\s+{v}\b"


def view_sql(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    rows = con.execute("""
        SELECT view_name, sql FROM duckdb_views()
        WHERE schema_name = 'main' AND NOT internal
        ORDER BY view_name
    """).fetchall()
    return dict(rows)


def dependency_graph(views: list[str], sql_of: dict[str, str]) -> dict[str, set[str]]:
    """views[A] -> set of other real views A's own SQL selects FROM/JOINs."""
    graph: dict[str, set[str]] = {}
    for a in views:
        graph[a] = {
            b for b in views
            if b != a and re.search(QUERY_RE_TMPL.format(v=re.escape(b)), sql_of[a])
        }
    return graph


def view_def_blocks(views: set[str], file_lines: dict[str, list[str]]) -> dict[str, tuple[str, int, int]]:
    """view_name -> (file, start_lineno, end_lineno) of its own CREATE VIEW
    string literal, found via AST rather than regex line-matching so a
    def spanning many lines (every real one here does) is bounded exactly."""
    blocks: dict[str, tuple[str, int, int]] = {}
    for fname, lines in file_lines.items():
        try:
            tree = ast.parse("\n".join(lines), filename=fname)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
            elif isinstance(node, ast.JoinedStr):
                text = "".join(v.value for v in node.values
                                if isinstance(v, ast.Constant) and isinstance(v.value, str))
            else:
                continue
            m = DEF_RE.search(text)
            if m and m.group(2) in views:
                blocks[m.group(2)] = (fname, node.lineno, node.end_lineno)
    return blocks


def closure(root_used: set[str], graph: dict[str, set[str]], views: list[str]) -> set[str]:
    live = set(root_used)
    changed = True
    while changed:
        changed = False
        for a in list(live):
            for b in graph.get(a, ()):
                if b not in live:
                    live.add(b)
                    changed = True
    return set(views) - live


def main() -> int:
    con = duckdb.connect(DB_PATH, read_only=True)
    sql_of = view_sql(con)
    views = sorted(sql_of)
    graph = dependency_graph(views, sql_of)

    files = sorted(f for f in glob.glob("*.py") if f != "check_dead_views.py")
    file_lines = {f: open(f, encoding="utf-8").read().splitlines() for f in files}
    def_blocks = view_def_blocks(set(views), file_lines)

    def in_any_def_block(fname: str, lineno: int) -> bool:
        return any(f == fname and s <= lineno <= e for f, s, e in def_blocks.values())

    root_used: set[str] = set()
    hits_by_view: dict[str, list[tuple[str, int, str]]] = {v: [] for v in views}
    for v in views:
        query_re = re.compile(QUERY_RE_TMPL.format(v=re.escape(v)))
        for f, lines in file_lines.items():
            for i, line in enumerate(lines, 1):
                if query_re.search(line) and not in_any_def_block(f, i):
                    hits_by_view[v].append((f, i, line.strip()))
        if hits_by_view[v]:
            root_used.add(v)

    dead = closure(root_used, graph, views)

    print(f"checked {len(views)} views across {len(files)} files "
          f"(dependency graph: {sum(len(b) for b in graph.values())} view-on-view edge(s))")
    if dead:
        print(f"\n{len(dead)} flagged -- unreachable from any real caller "
              f"(directly, or transitively through another dead view):")
        for v in sorted(dead):
            print(f"  {v}")
            dep_on = [a for a in views if v in graph.get(a, ())]
            if dep_on:
                print(f"      only ever selected FROM/JOINed inside: {', '.join(dep_on)}")
        print("\n(each flagged view needs a human read, same as "
              "check_dead_columns.py's findings -- a flag here is a "
              "candidate, not an automatic defect)")
    else:
        print("every view is queried somewhere (directly or transitively)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
