#!/usr/bin/env python
"""
Shared candidate-window builder for the two gold samplers
(build_gold_sample.py, build_gold_sample_novel.py).

Why this exists (Cleanup rotation, 2026-11-01): check_code_clones.py flagged
build_gold_sample.py::main() and build_gold_sample_novel.py::build_candidates()
at 0.579 similarity -- the flag undersold it. Both functions ran the exact
same SQL (the alias_docs query + the per-row/per-field anchor-window query)
and the exact same per-anchor extraction loop, independently maintained since
build_gold_sample_novel.py was written on 2026-09-25. This is the same class
of risk that already produced a real bug: the 2026-10-24 signature-span
mismatch (see build_gold_sample_novel.py's own docstring/comment history) was
exactly a case of the two scripts' independently-maintained window logic
silently disagreeing. Factoring the shared scan into one function removes
that whole risk class going forward -- a fix to how windows are built now
only has one place to go wrong.

`build_candidate_windows()` returns every anchor-window candidate row,
computing the fields both scripts need identically (row_id, doc_id,
anchor position, the window text each already used for its own display
column, and the citations `extract()` attributes to this anchor). Each
script attaches its own extra per-record field through `extra_fn` --
build_gold_sample.py needs nothing extra (its own hit/empty split reads
`extracted` directly); build_gold_sample_novel.py attaches `signature`,
computed from the raw row text at a DIFFERENT span than `window` (see that
script's own comment on why the two spans must not be conflated).
"""
from __future__ import annotations

from typing import Callable, Optional

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


def build_candidate_windows(
    con,
    extra_fn: Optional[Callable[[str, int, int, int, str, str], dict]] = None,
) -> list[dict]:
    """Scan every FK/Kodeks-mentioning row and return one record per anchor
    occurrence. `extra_fn(text, a_start, a_end, limit, kind, field)`, if
    given, is called per anchor and its returned dict is merged in -- used
    for fields that need the raw text/span rather than anything already
    computed here (e.g. a structural signature over a different span)."""
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
        allow_alias = doc_id in alias_docs
        for field, text in zip(SOURCE_FIELDS, texts):
            if not text:
                continue
            anchors = cx._anchors(text, allow_fk_alias=allow_alias, is_the_code=is_code)
            if not anchors:
                continue
            all_cites = cx.extract(text, allow_fk_alias=allow_alias, is_the_code=is_code)
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
                if extra_fn is not None:
                    rec.update(extra_fn(text, a_start, a_end, limit, kind, field))
                candidates.append(rec)
    return candidates
