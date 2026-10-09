"""Cross-file code-clone-drift check.

pyflakes/vulture/bandit/check_sql_bindings.py all look for a defect *within*
one piece of code. None of them catch the other real-world class this
project is especially exposed to: the same helper logic hand-copied into
several scripts (the `alias_docs` query, `_anchors()`/`extract()` call
sites, the gold-sample candidate builders all live in 4-5 files each, by
design -- see DAILY_REVIEW.md), where a later bug fix lands in one copy and
is silently never carried into the others. That's exactly the shape of bug
this project has found before in duplicated constants (`check_sql_bindings.py`
and `CC_DOCS`/`DOC_GENERAL` audits), just not yet checked for in duplicated
*functions*.

Method: AST-parse every top-level/nested function (>=4 body lines, to skip
trivial getters) in every *.py file, then diff every cross-file pair's
source text with difflib.SequenceMatcher. A SIMILAR-but-not-IDENTICAL pair
is the interesting signal -- it means someone copied a block and then
changed one side without the other, which could be a deliberate variant
(fine) or a forgotten fix (not fine). It still takes a human read to tell
those apart, same as a bandit finding; this script's job is only to surface
the candidates instead of leaving them to be found by accident.

A raw-SQL-block-level variant (diffing text inside triple-quoted f-string
SQL passed to execute(), rather than whole function bodies) was prototyped and
rejected 2026-10-09: on this codebase it produces ~54 cross-file pairs at a
similarity >= 0.5, almost all coincidental overlap from shared SQL
vocabulary ("SELECT ... FROM norm_unit WHERE ...") between queries that
aren't actually related, not real duplication. The whole-function version
below is precise enough to be worth re-running (4 candidate pairs out of 91
functions, zero noise, as of 2026-10-09) because requiring a shared
*surrounding* function body, not just a shared SQL fragment, filters out
that noise.

Run: python check_code_clones.py [--min-ratio 0.55]
"""
from __future__ import annotations

import argparse
import ast
import difflib
import glob

EXCLUDE = {"check_code_clones.py"}
MIN_LINES = 4


def collect_functions(paths: list[str]) -> list[tuple[str, str, int, str]]:
    funcs = []
    for path in paths:
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src, filename=path)
        lines = src.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_lines = lines[node.lineno - 1: node.end_lineno]
                if len(body_lines) < MIN_LINES:
                    continue
                funcs.append((path, node.name, node.lineno, "\n".join(body_lines)))
    return funcs


def find_pairs(funcs: list[tuple[str, str, int, str]], min_ratio: float):
    pairs = []
    for i in range(len(funcs)):
        for j in range(i + 1, len(funcs)):
            f1, f2 = funcs[i], funcs[j]
            if f1[0] == f2[0]:
                continue  # same file: not a cross-file drift risk
            ratio = difflib.SequenceMatcher(None, f1[3], f2[3]).ratio()
            if ratio >= min_ratio:
                pairs.append((ratio, f1, f2))
    pairs.sort(key=lambda p: -p[0])
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-ratio", type=float, default=0.55)
    args = ap.parse_args()

    paths = [p for p in sorted(glob.glob("*.py")) if p not in EXCLUDE]
    funcs = collect_functions(paths)
    pairs = find_pairs(funcs, args.min_ratio)

    print(f"{len(funcs)} functions (>={MIN_LINES} lines) parsed across {len(paths)} files")
    print(f"{len(pairs)} cross-file pairs with body similarity >= {args.min_ratio}\n")
    for ratio, f1, f2 in pairs:
        tag = "IDENTICAL" if ratio > 0.999 else ("NEAR-DUP " if ratio >= 0.85 else "SIMILAR  ")
        print(f"[{tag} {ratio:.3f}] {f1[0]}:{f1[1]}() L{f1[2]}  <->  {f2[0]}:{f2[1]}() L{f2[2]}")
    if not pairs:
        print("(none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
