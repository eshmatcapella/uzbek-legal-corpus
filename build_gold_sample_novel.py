#!/usr/bin/env python
"""
Signature-stratified gold sampler: draw hand-annotation candidates from
anchor-window *shapes* that the existing gold set (gold_citations.json)
has never seen, instead of another uniform-random batch.

Why: `build_gold_sample.py`'s plain stratified (hit/empty) random sample has
found a real, fixable extractor bug in 9 of 11 sessions so far, but the two
misses (2026-09-20, 100/100; 2026-09-22, 99.5/99.5, one tiny known gap) both
landed on a 50-window draw from the same uniform distribution the earlier,
bug-finding batches also drew from. With 100/~3251 candidate windows now
gold-annotated, a fresh uniform draw increasingly re-samples *shapes* the
gold set already covers (the common "single article, hyphen separator,
fuqarolik_kodeksi anchor" case dominates the corpus), which is exactly why
returns are diminishing. This script instead computes a cheap structural
*signature* per window -- which separators/unit-words/anchor-kind/oddities
its raw text contains, independent of what the extractor itself does with
it -- and measures, corpus-wide, which signatures the 100 already-annotated
gold windows have never once exercised. Sampling from THOSE signatures
targets exactly the shapes hypothesis-driven reading has never checked,
rather than re-rolling dice that mostly land on well-trodden ground.

This is a measurement of the *sampling methodology* itself, not just a new
batch: the script reports how many distinct signatures exist corpus-wide,
how many the current gold set covers, and how many candidate windows sit in
never-covered signatures -- a novelty-coverage number that didn't exist
before today.

Run: python build_gold_sample_novel.py [--n 40] [--out gold_sample_novel.json]
Output: a JSON file shaped exactly like build_gold_sample.py's gold_sample.json
(same fields, gold_id left as a plain 0-based index -- the merge step assigns
real gold_id values when appending to gold_citations.json), for hand reading.
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter

import duckdb

import citation_extractor as cx

PARQUET = "articles/train-00000-of-00001.parquet"
SOURCE_FIELDS = ("article_text", "cross_references", "amendment_note")
CC_DOCS = (cx.DOC_GENERAL, cx.DOC_SPECIAL)

# Feature detectors over the RAW window text (anchor-end to window-limit),
# independent of what citation_extractor.py itself decides to do with it --
# deliberately cheap regexes, not a re-run of RE_CLAUSE, so the signature
# reflects surface shape, not extractor behavior (that would just re-encode
# "what the extractor already handles" and miss exactly the unhandled shapes
# we're looking for).
SEP_COMMA = re.compile(r"\d\s*,\s*\d")
SEP_VA = re.compile(r"\d\s+va\s+\d", re.IGNORECASE)
SEP_HAMDA = re.compile(r"\d\s+hamda\s+\d", re.IGNORECASE)
SEP_DASH_ASCII = re.compile(r"\d\s*-\s*\d")
SEP_DASH_EN_EM = re.compile(r"\d\s*[–—]+\s*\d")
SEP_DASH_DOUBLED = re.compile(r"[–—-]{2,}")
UNIT_MODDA = re.compile(r"\bmodda", re.IGNORECASE)
UNIT_BOB = re.compile(r"\bbob", re.IGNORECASE)
UNIT_PARAGRAF = re.compile(r"\bparagraf", re.IGNORECASE)
UNIT_PARAGRIF = re.compile(r"\bparagrif", re.IGNORECASE)
UNIT_BOLIM = re.compile(r"boʻlim|bo'lim|bolim", re.IGNORECASE)
QISM_DIGIT = re.compile(r"\d+\s*-?\s*qism", re.IGNORECASE)
QISM_ORDINAL = re.compile("|".join(cx.ORDINALS), re.IGNORECASE)
BAND_WORD = re.compile(r"\bband", re.IGNORECASE)
SPACE_BEFORE_UNIT = re.compile(r"\d\s+(modda|bob|paragraf)\b", re.IGNORECASE)
NO_SPACE_UNIT = re.compile(r"\d(modda|bob|paragraf)\b", re.IGNORECASE)
PAREN = re.compile(r"[\(\)]")
ROMAN_CHAPTER = cx.RE_ROMAN_CHAPTER
QUOTE_TITLE = re.compile(r"[“”‘’\"]")
DIGIT4 = re.compile(r"\b\d{4}\b")  # possible concatenated superscript form


def signature(window_text: str, anchor_kind: str, field: str) -> tuple:
    return (
        anchor_kind,
        field,
        bool(SEP_COMMA.search(window_text)),
        bool(SEP_VA.search(window_text)),
        bool(SEP_HAMDA.search(window_text)),
        bool(SEP_DASH_ASCII.search(window_text)),
        bool(SEP_DASH_EN_EM.search(window_text)),
        bool(SEP_DASH_DOUBLED.search(window_text)),
        bool(UNIT_MODDA.search(window_text)),
        bool(UNIT_BOB.search(window_text)),
        bool(UNIT_PARAGRAF.search(window_text)),
        bool(UNIT_PARAGRIF.search(window_text)),
        bool(UNIT_BOLIM.search(window_text)),
        bool(QISM_DIGIT.search(window_text)),
        bool(QISM_ORDINAL.search(window_text)),
        bool(BAND_WORD.search(window_text)),
        bool(SPACE_BEFORE_UNIT.search(window_text)),
        bool(NO_SPACE_UNIT.search(window_text)),
        bool(PAREN.search(window_text)),
        bool(ROMAN_CHAPTER.search(window_text)),
        bool(QUOTE_TITLE.search(window_text)),
        bool(DIGIT4.search(window_text)),
    )


def build_candidates(con) -> list[dict]:
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

    candidates: list[dict] = []
    for row_id, doc_id, doc_type, art_no, *texts in rows:
        is_code = doc_id in CC_DOCS
        for field, text in zip(SOURCE_FIELDS, texts):
            if not text:
                continue
            allow_alias = doc_id in alias_docs
            anchors = cx._anchors(text, allow_fk_alias=allow_alias, is_the_code=is_code)
            if not anchors:
                continue
            all_cites = cx.extract(text, allow_fk_alias=allow_alias, is_the_code=is_code)
            for i, (a_start, a_end, kind) in enumerate(anchors):
                limit = min(a_end + cx.WINDOW, anchors[i + 1][0] if i + 1 < len(anchors) else len(text))
                window_text = text[max(0, a_start - 20):limit]
                raw_after_anchor = text[a_end:limit]
                cites_here = [c for c in all_cites if a_start <= c.start < limit]
                candidates.append({
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
                    "signature": signature(raw_after_anchor, kind, field),
                    "extracted": [
                        {
                            "target_kind": c.target_kind, "article": c.article,
                            "struct_number": c.struct_number, "section_number": c.section_number,
                            "qism": c.qism, "anchor": c.anchor, "listing": c.listing,
                            "evidence": c.evidence,
                        } for c in cites_here
                    ],
                })
    return candidates


def gold_signatures(con, gold_path: str) -> set[tuple]:
    """Recompute the signature of every already-annotated gold window, from
    its own stored anchor position (same recompute pattern score_gold.py
    uses), so novelty is measured against what's ACTUALLY been read, not
    against some approximation."""
    gold = json.load(open(gold_path, encoding="utf-8"))
    records = gold["records"]
    raw = f"read_parquet('{PARQUET}', file_row_number=true)"
    row_ids = sorted({r["row_id"] for r in records})
    rows = {r[0]: r for r in con.execute(f"""
        SELECT file_row_number, article_text, cross_references, amendment_note
        FROM {raw} WHERE file_row_number IN ({",".join(str(i) for i in row_ids)})
    """).fetchall()}
    field_index = {"article_text": 0, "cross_references": 1, "amendment_note": 2}
    sigs = set()
    for rec in records:
        row = rows.get(rec["row_id"])
        if row is None:
            continue
        text = row[1 + field_index[rec["field"]]]
        if text is None:
            continue
        a_end = rec["anchor_end"]
        # Cap the window the same way build_candidates does, using WINDOW alone
        # rather than re-locating the next real anchor (a slight overestimate of
        # context at worst, never wrong about which surface features are present).
        window_after = text[a_end: a_end + cx.WINDOW]
        sigs.add(signature(window_after, rec["anchor_kind"], rec["field"]))
    return sigs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260925)
    ap.add_argument("--gold", default="gold_citations.json")
    ap.add_argument("--out", default="gold_sample_novel.json")
    args = ap.parse_args()

    con = duckdb.connect(":memory:", read_only=False)
    candidates = build_candidates(con)
    covered = gold_signatures(con, args.gold)

    sig_counts = Counter(c["signature"] for c in candidates)
    print(f"candidate windows: {len(candidates)}")
    print(f"distinct signatures corpus-wide: {len(sig_counts)}")
    print(f"signatures already covered by gold set: {len(covered)}")

    novel = [c for c in candidates if c["signature"] not in covered]
    novel_sig_counts = Counter(c["signature"] for c in novel)
    print(f"windows in never-covered signatures: {len(novel)} "
          f"({len(novel_sig_counts)} distinct novel signatures)")

    already_gold_rows = set()
    gold = json.load(open(args.gold, encoding="utf-8"))
    for rec in gold["records"]:
        already_gold_rows.add((rec["row_id"], rec["field"], rec["anchor_start"]))
    novel = [c for c in novel
             if (c["row_id"], c["field"], c["anchor_start"]) not in already_gold_rows]

    # Prioritize rarer signatures first (rarity = more likely to be an
    # unusual, under-tested surface form), then randomize within each
    # rarity tier so the pick isn't just "first in file order."
    rng = random.Random(args.seed)
    novel.sort(key=lambda c: novel_sig_counts[c["signature"]])
    # Group by signature, take up to 3 examples per signature so one very
    # common "novel" signature doesn't crowd out the rest of the batch.
    by_sig: dict[tuple, list[dict]] = {}
    for c in novel:
        by_sig.setdefault(c["signature"], []).append(c)
    for group in by_sig.values():
        rng.shuffle(group)

    sample: list[dict] = []
    sig_order = sorted(by_sig.keys(), key=lambda s: novel_sig_counts[s])
    i = 0
    while len(sample) < args.n and any(by_sig[s] for s in sig_order):
        s = sig_order[i % len(sig_order)]
        if by_sig[s]:
            sample.append(by_sig[s].pop())
        i += 1

    for idx, rec in enumerate(sample):
        rec["gold_id"] = idx
        rec.pop("signature")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)

    print(f"sampled {len(sample)} windows from novel signatures -> {args.out}")


if __name__ == "__main__":
    main()
