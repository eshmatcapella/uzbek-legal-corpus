#!/usr/bin/env python
"""
Score citation_extractor.py against the persisted, hand-verified gold set
(gold_citations.json) -- the annotation/scoring layer the "Build the gold
set" backlog item asked for on top of build_gold_sample.py's raw sampler.
See DAILY_REVIEW.md 2026-09-20 for the full reasoning behind each record's
verdict.

Each gold_citations.json record is one hand-judged anchor occurrence (a
row_id + field + exact anchor position), carrying the human-verified
"expected" citations -- what extract() SHOULD produce for that specific
anchor -- rather than just a snapshot of what it happened to produce when
the sample was drawn. Re-run any time citation_extractor.py changes, to get
a real, comparable precision/recall number instead of a fresh ad hoc sample
every session.

Two different scopes, on purpose:
  - PRECISION is scored per-anchor: recompute exactly the citations THIS
    anchor occurrence produces (same position-bounded partition
    build_gold_sample.py itself uses: [anchor_start, next_anchor_start or
    anchor_end+WINDOW)) and compare against "expected". A citation this
    anchor produces that isn't expected is a false positive.
  - RECALL is scored against the FULL field text's extract() output, not
    just this anchor's bucket. Lesson from 2026-09-17 (see DAILY_REVIEW.md):
    a per-anchor window's local bucket is a *display* slice, not proof of a
    miss -- a citation just past one anchor's window limit gets attributed
    to the *next* anchor occurrence in the same text, not lost. Scoring
    recall against the whole-field output avoids re-manufacturing that same
    false alarm here.
  qism is tracked (grain_mismatch) but excluded from both headline numbers
  -- see gold_citations.json's _meta.description for why.

Drift detection: each gold record stores the exact window text it was
annotated against. If a future corpus update changes that row's text, the
freshly recomputed window won't match -- such records are reported as
DRIFT and excluded from the score (their old verdict no longer applies to
new text), not silently miscounted.

Run: python score_gold.py [--gold gold_citations.json]
Exit: 0 if the gold file loads and every record's identity still resolves
(even if precision/recall are imperfect -- this is a measurement tool, not
a hard CI gate. No fixed target has been set; see DAILY_REVIEW.md).
"""
from __future__ import annotations

import argparse
import json
import sys

import duckdb

import citation_extractor as cx

PARQUET = "articles/train-00000-of-00001.parquet"
FIELD_INDEX = {"article_text": 0, "cross_references": 1, "amendment_note": 2}
SIG_FIELDS = ("target_kind", "article", "struct_number", "section_number", "listing")


def signature(c: dict) -> tuple:
    return tuple(c[f] for f in SIG_FIELDS)


def citation_to_dict(c: cx.Citation) -> dict:
    return {
        "target_kind": c.target_kind,
        "article": c.article,
        "struct_number": c.struct_number,
        "section_number": c.section_number,
        "listing": c.listing,
        "qism": c.qism,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="gold_citations.json")
    args = ap.parse_args()

    gold = json.load(open(args.gold, encoding="utf-8"))
    records = gold["records"]

    con = duckdb.connect(":memory:", read_only=False)
    raw = f"read_parquet('{PARQUET}', file_row_number=true)"
    alias_docs = {r[0] for r in con.execute(f"""
        SELECT DISTINCT doc_id FROM {raw}
        WHERE regexp_matches(coalesce(article_text, ''), 'bundan buyon matnda FK deb')
    """).fetchall()}

    row_ids = sorted({r["row_id"] for r in records})
    rows = {r[0]: r for r in con.execute(f"""
        SELECT file_row_number, article_text, cross_references, amendment_note
        FROM {raw} WHERE file_row_number IN ({",".join(str(i) for i in row_ids)})
    """).fetchall()}

    tp_p = fp = 0          # precision: per-anchor bucket vs expected
    tp_r = fn = 0          # recall: expected vs whole-field extract() output
    grain_mismatch = 0
    drift = []
    mismatches = []

    for rec in records:
        row = rows.get(rec["row_id"])
        if row is None:
            drift.append((rec["gold_id"], "row_id not found in parquet"))
            continue
        text = row[1 + FIELD_INDEX[rec["field"]]]
        if text is None:
            drift.append((rec["gold_id"], "field is now empty"))
            continue

        is_code = rec["is_the_code"]
        allow_alias = rec["doc_id"] in alias_docs
        anchors = cx._anchors(text, allow_fk_alias=allow_alias, is_the_code=is_code)
        a_start, a_end, kind = rec["anchor_start"], rec["anchor_end"], rec["anchor_kind"]
        if (a_start, a_end, kind) not in anchors:
            drift.append((rec["gold_id"], "anchor no longer found at recorded position"))
            continue

        idx = anchors.index((a_start, a_end, kind))
        limit = min(a_end + cx.WINDOW, anchors[idx + 1][0] if idx + 1 < len(anchors) else len(text))
        window_text = text[max(0, a_start - 20):limit]
        if window_text != rec["window"]:
            drift.append((rec["gold_id"], "window text changed"))
            continue

        all_cites = cx.extract(text, allow_fk_alias=allow_alias, is_the_code=is_code)
        cites_here = [citation_to_dict(c) for c in all_cites
                      if a_start <= c.start < limit]
        full_sigs = [signature(c) for c in (citation_to_dict(c) for c in all_cites)]

        expected = rec["expected"]
        expected_sigs = [signature(e) for e in expected]
        got_sigs = [signature(c) for c in cites_here]

        # Precision: does everything this anchor produced belong there?
        remaining = list(expected_sigs)
        for c, sig in zip(cites_here, got_sigs):
            if sig in remaining:
                remaining.remove(sig)
                tp_p += 1
            else:
                fp += 1
                mismatches.append((rec["gold_id"], "FP", sig))

        # Recall: does every expected citation show up ANYWHERE in the
        # full-text extraction (not just this anchor's bucket)?
        remaining_full = list(full_sigs)
        for e, sig in zip(expected, expected_sigs):
            if sig in remaining_full:
                remaining_full.remove(sig)
                tp_r += 1
            else:
                fn += 1
                mismatches.append((rec["gold_id"], "FN", sig))

        # qism: only meaningful to compare when the article/listing matched.
        got_qism = {(c["article"], c["listing"]): c["qism"] for c in cites_here}
        for e in expected:
            key = (e["article"], e["listing"])
            if key in got_qism and got_qism[key] != e["qism"]:
                grain_mismatch += 1

    n_scored = len(records) - len(drift)
    precision = tp_p / (tp_p + fp) if (tp_p + fp) else float("nan")
    recall = tp_r / (tp_r + fn) if (tp_r + fn) else float("nan")

    print(f"gold set: {len(records)} records ({n_scored} scored, {len(drift)} drift)")
    print(f"precision: {tp_p}/{tp_p + fp} = {precision:.3f}")
    print(f"recall:    {tp_r}/{tp_r + fn} = {recall:.3f}")
    print(f"qism grain mismatches (not in headline score): {grain_mismatch}")
    if mismatches:
        print("\nmismatches:")
        for gid, kind, sig in mismatches:
            print(f"  gold_id={gid} {kind} {sig}")
    if drift:
        print("\nDRIFT (corpus changed since annotation, excluded from score):")
        for gid, why in drift:
            print(f"  gold_id={gid}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
