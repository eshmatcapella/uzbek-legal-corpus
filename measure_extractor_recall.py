#!/usr/bin/env python
"""
Corpus-wide recall check for citation_extractor.py's core surface forms.

citation_extractor.py ships 22 self-tests, but those run on synthetic/curated
phrasings, not the actual corpus. This script builds an independent, much
simpler "naive" detector for the two most common surface forms (a bare digit
immediately before "-modda" or "-bob") and checks every "Fuqarolik kodeksi"
anchor occurrence in the full 54,173-row raw parquet: does the real extractor
account for every number the naive detector finds in the same citation clause?

The naive detector is deliberately dumber than the real one — no list/range
handling — so it undercounts on its own; the check is one-directional (every
naive hit must be explained by some extracted citation), not a full diff.
It reproduces the extractor's own exclusion rules (RE_STOP, RE_STOP_ABBR) so
a naive hit inside another act's own citation (e.g. "FPK 75-moddasi") is not
flagged as a miss.

Where corpus.duckdb already runs the same extractor over both `article_text`
and `cross_references` (see build_links.py), an earlier hypothesis was that
disagreement between the two fields' extracted citations on the same row
would itself be a recall signal (see DAILY_REVIEW.md, backlog "Data currency"
-> "Extractor recall/precision"). That turned out false: `cross_references`
is LexUZ's own editorial commentary pointing at topically related provisions
in OTHER laws, not a restatement of what `article_text` says, so the two
fields disagree ~99.5% of the time by design, not by extractor failure (see
the "cross-reference disagreement" section below, kept for the record).

2026-09-04 extended this to the anchor forms the first pass didn't cover
(see DAILY_REVIEW.md Active threads): the article/chapter checks below now
scan windows opened by ANY anchor kind (`Fuqarolik kodeksi`, the FK alias,
and "ushbu/shu/mazkur Kodeks" self-reference), using citation_extractor's
own `_anchors()` so window boundaries match `extract()` exactly instead of
being recomputed against only the `Fuqarolik kodeksi` phrase. That also adds
a qism/band ATTACHMENT check: not "was the article found" (already measured
clean) but "when a qism/band clause follows a found article citation, does
the extractor actually attach it to `Citation.qism`". That check exposed a
real gap — the attachment logic only fired for the genitive "moddasining"
suffix, silently dropping the qism/band on the far more common bare
"moddasi ..." construction ("...moddasi uchinchi qismiga muvofiq"). Fixed in
citation_extractor.py (RE_QISM_BLOCK-gated attachment for non-"sining"
suffixes); see the Log entry for the measured before/after and the
false-positive risk (list continuations like "185-moddasi, 186-moddasi
toʻqqizinchi qismi") that the gate exists to reject.

Run: python measure_extractor_recall.py
"""
from __future__ import annotations

import re

import duckdb

import citation_extractor as cx

PARQUET = "articles/train-00000-of-00001.parquet"
FIELDS = ("article_text", "cross_references", "amendment_note")

RE_NAIVE_MODDA = re.compile(r"(\d{1,5})\s*[-–—]\s*modda", re.IGNORECASE)
RE_NAIVE_BOB = re.compile(r"(\d{1,3})\s*[-–—]\s*bob", re.IGNORECASE)


def load_rows(con):
    raw = f"read_parquet('{PARQUET}', file_row_number=true)"
    rows = con.execute(f"""
        SELECT file_row_number, doc_id, article_text, cross_references, amendment_note
        FROM {raw}
        WHERE regexp_matches(lower(coalesce(article_text,'') || ' ' || coalesce(cross_references,'')
                                   || ' ' || coalesce(amendment_note,'')), 'kodeks|\\bfk\\b')
    """).fetchall()
    alias_docs = {r[0] for r in con.execute(f"""
        SELECT DISTINCT doc_id FROM {raw}
        WHERE regexp_matches(coalesce(article_text, ''), 'bundan buyon matnda FK deb')
    """).fetchall()}
    return rows, alias_docs


def check_recall(rows, alias_docs, naive_re, target_kinds, number_of) -> dict:
    """Scan windows opened by ANY anchor kind (Fuqarolik kodeksi, the FK alias,
    and the self-reference form), using citation_extractor's own `_anchors()`
    and the same next-anchor window limit `extract()` uses, so a naive hit
    is always checked against the citation(s) that could actually explain it."""
    windows = naive_total = extracted_total = 0
    misses = []
    by_anchor: dict[str, int] = {}
    for row_id, doc_id, art_text, cross_ref, amend in rows:
        texts = {"article_text": art_text, "cross_references": cross_ref, "amendment_note": amend}
        is_code = doc_id in (cx.DOC_GENERAL, cx.DOC_SPECIAL)
        allow_alias = doc_id in alias_docs
        for field in FIELDS:
            text = texts[field]
            if not text:
                continue
            anchors = cx._anchors(text, allow_fk_alias=allow_alias, is_the_code=is_code)
            if not anchors:
                continue
            citations = cx.extract(text, allow_fk_alias=allow_alias, is_the_code=is_code)
            for i, (a_start, a_end, kind) in enumerate(anchors):
                limit = min(a_end + cx.WINDOW, anchors[i + 1][0] if i + 1 < len(anchors) else len(text))
                window_text = text[a_end:limit]
                stops = [m.start() for m in
                         (cx.RE_STOP.search(window_text), cx.RE_STOP_ABBR.search(window_text)) if m]
                cutoff = min(stops) if stops else len(window_text)
                scoped = window_text[:cutoff]
                naive_nums = {int(n) for n in naive_re.findall(scoped)}
                if not naive_nums:
                    continue
                windows += 1
                by_anchor[kind] = by_anchor.get(kind, 0) + 1
                naive_total += len(naive_nums)
                ex_nums = {number_of(c) for c in citations
                           if c.anchor == kind and a_end <= c.start < limit and c.target_kind in target_kinds}
                extracted_total += len(ex_nums)
                missing = naive_nums - ex_nums
                if missing:
                    misses.append((row_id, field, kind, sorted(missing), scoped[:200]))
    return {
        "windows": windows, "naive_total": naive_total,
        "extracted_total": extracted_total, "misses": misses, "windows_by_anchor": by_anchor,
    }


def check_qism_band_attachment(rows, alias_docs) -> dict:
    """Recall for the qism/band ATTACHMENT (not the article number itself,
    already checked clean above): among single-article citations, whenever a
    qism/band clause immediately follows (RE_QISM matches the tail, and
    nothing in RE_QISM_BLOCK's sense suggests it belongs to a later citation
    in a list), does the extractor actually set Citation.qism? This is a
    live regression guard for the 2026-09-04 fix in citation_extractor.py:
    the attachment used to fire only for the genitive "moddasining" suffix,
    silently dropping the far more common bare "moddasi ..." construction."""
    checked = 0
    misses = []
    for row_id, doc_id, art_text, cross_ref, amend in rows:
        texts = {"article_text": art_text, "cross_references": cross_ref, "amendment_note": amend}
        is_code = doc_id in (cx.DOC_GENERAL, cx.DOC_SPECIAL)
        allow_alias = doc_id in alias_docs
        for field in FIELDS:
            text = texts[field]
            if not text:
                continue
            citations = cx.extract(text, allow_fk_alias=allow_alias, is_the_code=is_code)
            for c in citations:
                if c.target_kind != "article" or c.listing != "single":
                    continue
                tail = text[c.end: c.end + 60]
                m = cx.RE_QISM.search(tail)
                if not m or cx.RE_QISM_BLOCK.search(tail[:m.start()]):
                    continue
                checked += 1
                if c.qism is None:
                    misses.append((row_id, field, c.article, tail[:70]))
    return {"checked": checked, "misses": misses}


def check_cross_reference_disagreement(con) -> dict:
    """Record of the falsified hypothesis: does cross_references name an article
    that article_text mining on the SAME row misses entirely? (It almost always
    does, because the two fields describe different things — see module docstring.)"""
    q = """
        WITH art AS (
            SELECT DISTINCT src_row_id, source_field, dst_article_number
            FROM link_edge
            WHERE dst_kind = 'article' AND dst_doc_id IN (-111189, -180552)
                  AND dst_article_number IS NOT NULL
        ),
        cr AS (SELECT src_row_id, dst_article_number FROM art WHERE source_field = 'cross_references'),
        txt AS (SELECT src_row_id, dst_article_number FROM art WHERE source_field = 'article_text')
        SELECT count(*), count(*) FILTER (WHERE txt.src_row_id IS NULL)
        FROM cr LEFT JOIN txt USING (src_row_id, dst_article_number)
    """
    total_cr, cr_only = con.execute(q).fetchone()
    return {"total_cross_ref_article_citations": total_cr, "with_no_article_text_match": cr_only}


def main() -> int:
    con = duckdb.connect("corpus.duckdb", read_only=True)
    rows, alias_docs = load_rows(con)
    print(f"candidate rows (mention 'kodeks' or standalone FK): {len(rows)}\n")

    print("=== article-level recall (naive 'N-modda' vs extractor), all anchor kinds ===")
    r1 = check_recall(rows, alias_docs, RE_NAIVE_MODDA, {"article"},
                       lambda c: int(c.article.split("-")[0]))
    print(f"  anchor windows with a naive hit: {r1['windows']}  (by anchor kind: {r1['windows_by_anchor']})")
    print(f"  naive numbers: {r1['naive_total']}  |  extractor numbers: {r1['extracted_total']}")
    print(f"  real misses: {len(r1['misses'])}")
    for miss in r1["misses"]:
        print(f"    {miss}")

    print("\n=== chapter/section-level recall (naive 'N-bob' vs extractor), all anchor kinds ===")
    r2 = check_recall(rows, alias_docs, RE_NAIVE_BOB, {"chapter", "section"},
                       lambda c: c.struct_number)
    print(f"  anchor windows with a naive hit: {r2['windows']}  (by anchor kind: {r2['windows_by_anchor']})")
    print(f"  naive numbers: {r2['naive_total']}  |  extractor numbers: {r2['extracted_total']}")
    print(f"  real misses: {len(r2['misses'])}")
    for miss in r2["misses"]:
        print(f"    {miss}")

    print("\n=== qism/band attachment recall (single-article citations) ===")
    r4 = check_qism_band_attachment(rows, alias_docs)
    print(f"  citations checked (unambiguous qism/band tail present): {r4['checked']}")
    print(f"  attachment misses: {len(r4['misses'])}")
    for miss in r4["misses"][:20]:
        print(f"    {miss}")

    print("\n=== cross-reference disagreement (falsified hypothesis, kept for the record) ===")
    r3 = check_cross_reference_disagreement(con)
    pct = r3["with_no_article_text_match"] / r3["total_cross_ref_article_citations"]
    print(f"  cross_references-sourced article citations: {r3['total_cross_ref_article_citations']}")
    print(f"  with no matching article_text citation on the same row: "
          f"{r3['with_no_article_text_match']} ({pct:.1%})")
    print("  -> not a recall signal: cross_references points at topically related")
    print("     provisions in OTHER acts, not a restatement of article_text.")

    con.close()
    total_misses = len(r1["misses"]) + len(r2["misses"]) + len(r4["misses"])
    return 0 if total_misses == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
