"""Dead/write-only base-table column check.

pyflakes/vulture catch unused Python symbols; check_sql_bindings.py catches a
query that references a column that doesn't exist. None of the eight
existing checks catch the opposite shape: a column that *does* exist, is
faithfully populated by the build pipeline on every run, and is never read
back by anything -- no SELECT, no WHERE/JOIN/ORDER BY, no app display, no
verify_transfer.py check. That data isn't a Python-syntax defect and binds
cleanly against the schema, so it's invisible to every tool this project
already has.

Method: pull every DDL-declared column of every base table (not view) from
corpus.duckdb's live schema, then grep each column name as a whole word
across every *.py file. A hit is classified as:
  - "def"            the column's own `CREATE TABLE` declaration line
                      (name immediately followed by its SQL type keyword)
  - "write"           a parameterized `UPDATE ... SET col = ?` clause
  - "insert-collist"  inside an explicit `INSERT INTO tbl (col1, col2, ...)`
                      column list (paren-balance-tracked, since this spans
                      multiple source lines in this codebase's style)
  - "read"            anything else -- a SELECT list, WHERE/JOIN/ORDER BY/
                      QUALIFY, or a Python-side reference
A column with zero "read" hits is flagged: the pipeline writes it and
nothing ever reads it back.

Known blind spots, same spirit as this project's other heuristic checks
(check_code_clones.py's difflib threshold, check_sql_bindings.py's
literal-indirection gap): (1) a column read only via positional access
(`row[3]`, not by name) would be invisible here -- not a pattern this
codebase actually uses, checked by hand when this script was built
(2026-10-22), but not structurally guaranteed to stay that way. (2) the
word-match isn't table-scoped, so a genuinely dead column sharing its name
with a used column in another table would be masked (false negative, not
false positive -- the safer direction for a check whose findings get
hand-verified anyway). (3) deliberately scoped to DDL-declared base-table
columns, not `CREATE ... AS SELECT` derived tables/views, whose "columns"
are query-output aliases already covered by check_sql_bindings.py's
referential check, not this one's read/write-asymmetry question.

Every flagged column as of 2026-10-22 was hand-verified against
corpus.duckdb directly (non-null population rate + sample values) before
being recorded -- see DAILY_REVIEW.md for the full trace. All 15 are real,
populated, write-only columns; none is a live bug today (nothing downstream
is silently wrong), but they are real unused surface -- two inventoried in
Backlog as a possible future pickup (link_edge.ev_start/ev_end -- genuine
character offsets that could drive an evidence-highlighting feature, but
unusable as stored since they're relative to raw row text, not the
whitespace-collapsed/apparatus-stripped text the apps actually display).
"""
from __future__ import annotations

import glob
import re
import sys

import duckdb

DB_PATH = "corpus.duckdb"

DEF_RE_TMPL = r"^\s*{c}\s+[A-Z]"
WRITE_RE_TMPL = r"\b{c}\s*=\s*\?"
INSERT_OPEN = re.compile(r"INSERT\s+INTO\s+\w+\s*\(")


def _insert_collist_lines(lines: list[str]) -> set[int]:
    """1-indexed line numbers sitting inside an explicit
    `INSERT INTO tbl (col1, col2, ...)` column list -- a write target even
    though it names the column, and this codebase always spans it across
    several source lines."""
    flagged: set[int] = set()
    depth = 0
    in_collist = False
    for i, line in enumerate(lines, 1):
        if not in_collist and INSERT_OPEN.search(line):
            in_collist = True
            depth = line.count("(") - line.count(")")
            flagged.add(i)
            if depth <= 0:
                in_collist = False
            continue
        if in_collist:
            flagged.add(i)
            depth += line.count("(") - line.count(")")
            if depth <= 0:
                in_collist = False
    return flagged


def base_table_columns(con: duckdb.DuckDBPyConnection) -> list[tuple[str, str]]:
    rows = con.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'main'
        ORDER BY table_name, ordinal_position
    """).fetchall()
    return [(t, c) for t, c in rows if not t.startswith("v_")]


def main() -> int:
    con = duckdb.connect(DB_PATH, read_only=True)
    cols = base_table_columns(con)

    # Exclude this script's own file: its module docstring names flagged
    # columns by way of explaining them, and that mention would otherwise
    # register as a "read" hit and mask the very column it's documenting
    # (hit this for real on ev_start/ev_end while building the script).
    files = sorted(f for f in glob.glob("*.py") if f != "check_dead_columns.py")
    file_lines = {f: open(f, encoding="utf-8").read().splitlines() for f in files}
    collist_lines = {f: _insert_collist_lines(lines) for f, lines in file_lines.items()}

    flagged = []
    for t, c in cols:
        word_re = re.compile(rf"\b{re.escape(c)}\b")
        def_re = re.compile(DEF_RE_TMPL.format(c=re.escape(c)))
        write_re = re.compile(WRITE_RE_TMPL.format(c=re.escape(c)))
        read_hits = []
        other_hits = []
        for f, lines in file_lines.items():
            for i, line in enumerate(lines, 1):
                if not word_re.search(line):
                    continue
                if def_re.search(line):
                    other_hits.append((f, i, "def", line.strip()))
                elif write_re.search(line):
                    other_hits.append((f, i, "write", line.strip()))
                elif i in collist_lines[f]:
                    other_hits.append((f, i, "insert-collist", line.strip()))
                else:
                    read_hits.append((f, i, line.strip()))
        if not read_hits:
            flagged.append((t, c, other_hits))

    print(f"checked {len(cols)} base-table columns across {len(files)} files")
    if flagged:
        print(f"\n{len(flagged)} flagged -- written but never read back:")
        for t, c, hits in flagged:
            print(f"  {t}.{c}")
            for f, i, kind, line in hits:
                print(f"      [{kind}] {f}:{i}  {line}")
        print("\n(each flagged column needs a human read -- see this script's "
              "module docstring and DAILY_REVIEW.md for the hand-verification "
              "every one of today's findings got; a flag here is a candidate, "
              "not an automatic defect)")
    else:
        print("every base-table column is read somewhere")
    return 0


if __name__ == "__main__":
    sys.exit(main())
