#!/usr/bin/env python
"""
Sample anchor windows corpus-wide for hand annotation (the "gold set" backlog
item: no hand-verified ground truth exists yet for citation_extractor.py's
corpus-wide precision/recall, only synthetic self-tests and the naive-regex
recall check in measure_extractor_recall.py, which measures surface-form
coverage, not whether a resolved target is actually correct).

This script does NOT judge correctness. It draws a stratified, seeded random
sample of real anchor windows (the same anchors/windows citation_extractor.py
and build_links.py themselves use) and dumps them, with the extractor's own
output over each window, to a JSON file for a human/LLM annotator to read the
raw Uzbek text against and reason about by hand. The annotation-storage and
scoring layer lives separately, in gold_citations.json (committed,
hand-verified ground truth) and score_gold.py (the scorer) -- see that
script's docstring for why recall and precision are scored against
different scopes of extract()'s output. Each record here carries
anchor_start/anchor_end (added 2026-09-20) so the scorer can recompute
exactly which citations this specific anchor occurrence produced, without
relying on approximate window-text matching. What this script deterministically
reproduces (same --seed -> same sample, so it's never committed to git) has
already paid for itself once: reading the 2026-09-15 sample by hand found and
fixed three real corpus-wide bugs in one sitting (a missing "kodeksning"
stop-word, a bare-space "N modda" surface form, and a list containing an
embedded "N-M" sub-range) -- see the Log entry for the measured impact of
each. Continuing the "read a fresh sample, hypothesize, measure" loop each
session (a new --seed draws a disjoint sample) has now found a real, fixable
gap in every one of 8 sessions it's been tried.

Stratification: half the sample is windows where extract() produced at least
one citation ("hit" windows -- checks precision, e.g. is the resolved article
number/listing actually what the text says); half is windows where it
produced nothing at all ("empty" windows -- checks recall, e.g. did a real
citation get missed because of a stop-word/anchor/window-limit gap). Sampled
across all three source fields and all three anchor kinds where present.

Run: python build_gold_sample.py [--n 50] [--seed 20260915]
Output: gold_sample.json (raw windows + extractor output, read by hand, not
committed -- rerun to reproduce or pick a new --seed for a fresh sample)
"""
from __future__ import annotations

import argparse
import json
import random

import duckdb

import citation_extractor as cx

PARQUET = "articles/train-00000-of-00001.parquet"
SOURCE_FIELDS = ("article_text", "cross_references", "amendment_note")
CC_DOCS = (cx.DOC_GENERAL, cx.DOC_SPECIAL)


def citation_dict(c: cx.Citation) -> dict:
    return {
        "target_kind": c.target_kind,
        "article": c.article,
        "struct_number": c.struct_number,
        "section_number": c.section_number,
        "qism": c.qism,
        "anchor": c.anchor,
        "listing": c.listing,
        "evidence": c.evidence,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260915)
    ap.add_argument("--out", default="gold_sample.json")
    args = ap.parse_args()

    con = duckdb.connect(":memory:", read_only=False)
    raw = f"read_parquet('{PARQUET}', file_row_number=true)"

    alias_docs = {r[0] for r in con.execute(f"""
        SELECT DISTINCT doc_id FROM {raw}
        WHERE regexp_matches(coalesce(article_text, ''), 'bundan buyon matnda FK deb')
    """).fetchall()}

    rows = con.execute(f"""
        SELECT file_row_number, doc_id, doc_type, article_number,
               article_text, cross_references, amendment_note
        FROM {raw}
        WHERE regexp_matches(lower(coalesce(article_text,'') || ' ' || coalesce(cross_references,'')
                                   || ' ' || coalesce(amendment_note,'')), 'kodeks|\\bfk\\b')
        ORDER BY file_row_number
    """).fetchall()

    hits: list[dict] = []
    empties: list[dict] = []

    for row_id, doc_id, doc_type, art_no, *texts in rows:
        is_code = doc_id in CC_DOCS
        for field, text in zip(SOURCE_FIELDS, texts):
            if not text:
                continue
            anchors = cx._anchors(text, allow_fk_alias=doc_id in alias_docs, is_the_code=is_code)
            if not anchors:
                continue
            all_cites = cx.extract(text, allow_fk_alias=doc_id in alias_docs, is_the_code=is_code)
            for i, (a_start, a_end, kind) in enumerate(anchors):
                limit = min(a_end + cx.WINDOW, anchors[i + 1][0] if i + 1 < len(anchors) else len(text))
                window_text = text[max(0, a_start - 20):limit]
                cites_here = [c for c in all_cites if a_start <= c.start < limit]
                rec = {
                    "row_id": row_id,
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "article_number": art_no,
                    "field": field,
                    "anchor_kind": kind,
                    "anchor_start": a_start,
                    "anchor_end": a_end,
                    "is_the_code": is_code,
                    "window": window_text,
                    "extracted": [citation_dict(c) for c in cites_here],
                }
                produced_nonact = any(c["target_kind"] != "act" for c in rec["extracted"])
                (hits if produced_nonact else empties).append(rec)

    rng = random.Random(args.seed)
    half = args.n // 2
    sample_hits = rng.sample(hits, min(half, len(hits)))
    sample_empties = rng.sample(empties, min(args.n - half, len(empties)))
    sample = sample_hits + sample_empties
    rng.shuffle(sample)
    for idx, rec in enumerate(sample):
        rec["gold_id"] = idx

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)

    print(f"candidate windows: {len(hits)} hit, {len(empties)} empty")
    print(f"sampled: {len(sample_hits)} hit + {len(sample_empties)} empty = {len(sample)} -> {args.out}")


if __name__ == "__main__":
    main()
