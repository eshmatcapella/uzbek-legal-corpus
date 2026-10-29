"""Dead/write-only view check -- check_dead_columns.py's column-grain idea,
one level up at the view grain.

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

Method: list every view in corpus.duckdb's live schema (`information_schema.
tables WHERE table_type = 'VIEW'`), then grep each view name as a whole word
across every *.py file. A hit is classified as:
  - "def"    the view's own `CREATE [OR REPLACE] VIEW <name> AS` line
  - "query"  the name directly preceded by FROM/JOIN on the same line -- a
             real SQL consumer, whether that's an app query, a
             verify_transfer.py check, or another view's own definition
             (composition still counts as downstream use)
  - "mention" anything else -- a docstring index entry, a code comment
             explaining the view, a log message naming it in prose. Not a
             query, so not counted as use (same reasoning
             check_dead_columns.py applies to its own docstring: naming a
             thing while explaining it isn't reading it back).
A view with zero "query" hits outside its own def is flagged as dead.

Known blind spots, same spirit as this project's other heuristic checks:
(1) genuinely transitive dead views (view B is only ever queried by view A,
and A itself is dead) would still mark B as "used" here -- this script
checks one level of consumption, not a reachability closure from the app
layer down. Checked by hand for today's run: not the shape of anything
found. (2) a view queried only through a Python string built up across
multiple lines (not a single `FROM <name>`/`JOIN <name>` on one line) would
be invisible -- not a pattern this codebase uses today (checked by hand),
same acknowledged limit as check_dead_columns.py's `row[3]` positional-read
blind spot.

Found and hand-verified one real dead view as of 2026-10-29:
`v_llc_skeleton` (build_llc.py) -- defined once, queried nowhere. app_llc.py
re-derives the exact same `llc_stage LEFT JOIN llc_norm` join it encodes, by
hand, at five separate call sites (lines 105/110/131/143/149/200/336) instead
of querying the view meant to serve it. Not a live bug (the app's own
separately-issued queries return correct data), but a wasted build step and
a missed single-source-of-truth opportunity -- see DAILY_REVIEW.md for the
full trace and the decision on whether to wire it in or retire it.
"""
from __future__ import annotations

import glob
import re
import sys

import duckdb

DB_PATH = "corpus.duckdb"

DEF_RE_TMPL = r"CREATE\s+(OR\s+REPLACE\s+)?VIEW\s+{v}\b"
QUERY_RE_TMPL = r"\b(FROM|JOIN)\s+{v}\b"


def view_names(con: duckdb.DuckDBPyConnection) -> list[str]:
    rows = con.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'main' AND table_type = 'VIEW'
        ORDER BY table_name
    """).fetchall()
    return [r[0] for r in rows]


def main() -> int:
    con = duckdb.connect(DB_PATH, read_only=True)
    views = view_names(con)

    # Exclude this script's own file for the same reason check_dead_columns.py
    # excludes itself: the module docstring names the one flagged view while
    # explaining it, which would otherwise register as a hit and mask it.
    files = sorted(f for f in glob.glob("*.py") if f != "check_dead_views.py")
    file_lines = {f: open(f, encoding="utf-8").read().splitlines() for f in files}

    flagged = []
    for v in views:
        word_re = re.compile(rf"\b{re.escape(v)}\b")
        def_re = re.compile(DEF_RE_TMPL.format(v=re.escape(v)))
        query_re = re.compile(QUERY_RE_TMPL.format(v=re.escape(v)))
        query_hits = []
        other_hits = []
        for f, lines in file_lines.items():
            for i, line in enumerate(lines, 1):
                if not word_re.search(line):
                    continue
                if query_re.search(line):
                    query_hits.append((f, i, "query", line.strip()))
                elif def_re.search(line):
                    other_hits.append((f, i, "def", line.strip()))
                else:
                    other_hits.append((f, i, "mention", line.strip()))
        if not query_hits:
            flagged.append((v, other_hits))

    print(f"checked {len(views)} views across {len(files)} files")
    if flagged:
        print(f"\n{len(flagged)} flagged -- defined but never queried:")
        for v, hits in flagged:
            print(f"  {v}")
            for f, i, kind, line in hits:
                print(f"      [{kind}] {f}:{i}  {line}")
        print("\n(each flagged view needs a human read, same as "
              "check_dead_columns.py's findings -- a flag here is a "
              "candidate, not an automatic defect)")
    else:
        print("every view is queried somewhere")
    return 0


if __name__ == "__main__":
    sys.exit(main())
