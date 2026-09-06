#!/usr/bin/env python
"""
M2 — Build the realization graph: which acts realize which Civil Code norms.

Reads the raw parquet (never writes to it), runs citation_extractor over every
candidate row, resolves each citation onto a norm unit or structural node, and
writes link_edge into corpus.duckdb.

An edge always means "src references dst".  Whether that is *realization* is
derived, not asserted: hierarchy_rel compares the citing act's tier against the
Code's, so a Cabinet resolution citing Article 49 is 'below' (it realizes the
norm) while another code citing it is 'same'.
"""
from __future__ import annotations

import difflib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

import citation_extractor as cx

ROOT = Path(__file__).resolve().parent
PARQUET = ROOT / "articles" / "train-00000-of-00001.parquet"
DB_PATH = ROOT / "corpus.duckdb"

CC_DOCS = (cx.DOC_GENERAL, cx.DOC_SPECIAL)
CC_TIER = 2
UNCLASSIFIED_TIER = 9
BATCH = 5000

SOURCE_FIELDS = ("article_text", "cross_references", "amendment_note")

# What KIND of thing the citation was mined from.  This is the distinction that
# matters legally: only `normative` evidence is the act itself invoking the Code.
# `cross_references` is LexUZ's editorial apparatus — a professional's pointer
# ("LexUZ sharhiQarang: ...") interleaved with version history ("Oldingi tahrirga
# qarang."), which is good evidence that two provisions are related but is NOT
# the act speaking.  `amendment_note` is legislative history about the text.
EVIDENCE_KIND = {
    "article_text": "normative",
    "cross_references": "editorial",
    "amendment_note": "amendment",
}

# Confidence that the edge is a correctly extracted, correctly resolved citation.
# The act's own words outrank an editorial pointer: a curated link tells you the
# editor saw a connection, not that the act realizes the norm.
BASE_CONFIDENCE = {
    ("article_text", "article"): 0.90,
    ("article_text", "chapter"): 0.85,
    ("article_text", "section"): 0.85,
    ("article_text", "act"): 0.40,
    ("cross_references", "article"): 0.80,
    ("cross_references", "chapter"): 0.75,
    ("cross_references", "section"): 0.75,
    ("cross_references", "act"): 0.40,
    ("amendment_note", "article"): 0.60,
    ("amendment_note", "chapter"): 0.55,
    ("amendment_note", "section"): 0.55,
    ("amendment_note", "act"): 0.30,
}

# LexUZ's editorial furniture, stripped from displayed evidence so the reader
# sees the citation and not the site's chrome.  Kept out of `evidence` itself:
# that column stays byte-faithful to the source for provenance.
RE_APPARATUS = re.compile(
    r"(Oldingi tahrirga qarang\.?|LexUZ sharhi|Batafsil maʼlumot uchun|"
    r"Qarang:|Мазкур|\(Qarang:.*?\))",
    re.IGNORECASE,
)


def clean_evidence(text: str) -> str:
    return re.sub(r"\s{2,}", " ", RE_APPARATUS.sub(" ", text)).strip(" .;,")


def log(msg: str = "") -> None:
    print(msg, flush=True)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("m2-%Y%m%dT%H%M%SZ")
    con = duckdb.connect(str(DB_PATH))

    con.execute("""
        CREATE OR REPLACE TABLE link_edge (
            edge_id            BIGINT PRIMARY KEY,
            run_id             VARCHAR,
            -- citing side
            src_row_id         BIGINT,
            src_doc_id         BIGINT,
            src_doc_type       VARCHAR,
            src_tier           INTEGER,
            src_article_number VARCHAR,
            -- cited side
            dst_kind           VARCHAR,   -- article | chapter | section | act
            dst_doc_id         BIGINT,
            dst_article_number VARCHAR,
            dst_norm_id        VARCHAR,
            dst_struct_node_id VARCHAR,
            dst_qism           VARCHAR,   -- article part/point as cited, for a finer grain later
            dst_ambiguous      BOOLEAN,
            dst_dangling       BOOLEAN,   -- cites an article the current corpus no longer has
            -- interpretation
            hierarchy_rel      VARCHAR,   -- below | same | above | self
            relation           VARCHAR,   -- realizes | cites | internal
            -- provenance
            anchor             VARCHAR,
            listing            VARCHAR,
            source_field       VARCHAR,
            evidence_kind      VARCHAR,   -- normative | editorial | amendment
            method             VARCHAR,
            confidence         DOUBLE,
            evidence           VARCHAR,   -- byte-faithful to the source
            evidence_clean     VARCHAR,   -- LexUZ apparatus stripped, for display
            ev_start           INTEGER,
            ev_end             INTEGER,
            validated_by       VARCHAR,
            validated_at       TIMESTAMPTZ
        );
    """)

    # Acts that define the "FK" abbreviation; the alias is enabled only there.
    raw = f"read_parquet('{PARQUET.as_posix()}', file_row_number=true)"
    alias_docs = {r[0] for r in con.execute(f"""
        SELECT DISTINCT doc_id FROM {raw}
        WHERE regexp_matches(coalesce(article_text, ''), 'bundan buyon matnda FK deb')
    """).fetchall()}
    log(f"FK abbreviation defined by {len(alias_docs)} act(s): {sorted(alias_docs)}")

    # Resolution tables.
    norm_by_number: dict[str, list[tuple[str, int | None]]] = {}
    for norm_id, number, sup in con.execute(
        "SELECT norm_id, article_number, superscript FROM norm_unit ORDER BY src_row"
    ).fetchall():
        norm_by_number.setdefault(number, []).append((norm_id, sup))
    struct_doc = dict(con.execute("SELECT node_id, doc_id FROM struct_node").fetchall())
    tier_of = dict(con.execute("SELECT doc_id, tier FROM act").fetchall())

    # Candidate rows: anything mentioning a code at all.  Cheap filter, no recall
    # loss — every anchor the extractor knows contains "kodeks" or "FK".
    total = con.execute(f"""
        SELECT count(*) FROM {raw}
        WHERE regexp_matches(lower(coalesce(article_text,'') || ' ' || coalesce(cross_references,'')
                                   || ' ' || coalesce(amendment_note,'')), 'kodeks|\\bfk\\b')
    """).fetchone()[0]
    log(f"scanning {total} candidate rows of 54,173\n")

    # A dedicated cursor: any query issued on `con` would invalidate a result set
    # still being streamed from it.
    cur = con.cursor().execute(f"""
        SELECT file_row_number, doc_id, doc_type, article_number,
               article_text, cross_references, amendment_note
        FROM {raw}
        WHERE regexp_matches(lower(coalesce(article_text,'') || ' ' || coalesce(cross_references,'')
                                   || ' ' || coalesce(amendment_note,'')), 'kodeks|\\bfk\\b')
        ORDER BY file_row_number
    """)

    edges: list[list] = []
    edge_id = 0
    scanned = 0

    while True:
        rows = cur.fetchmany(BATCH)
        if not rows:
            break
        for row_id, doc_id, doc_type, art_no, *texts in rows:
            scanned += 1
            src_tier = tier_of.get(doc_id, 9)
            is_code = doc_id in CC_DOCS
            for field, text in zip(SOURCE_FIELDS, texts):
                for c in cx.extract(text, allow_fk_alias=doc_id in alias_docs, is_the_code=is_code):
                    dst_norm = dst_struct = dst_doc = dst_art = None
                    ambiguous = dangling = False

                    if c.target_kind == "article":
                        dst_doc, dst_art = c.doc_id, c.article
                        if dst_doc is None:
                            continue  # article number outside the Code
                        candidates = norm_by_number.get(c.article, [])
                        # A citation writes 26-super-1 and 261 identically; the plain
                        # base article is the ordinary reading, so prefer it and flag.
                        plain = [n for n, sup in candidates if sup is None]
                        if plain:
                            dst_norm = plain[0]
                            ambiguous = len(candidates) > 1
                        elif candidates:
                            dst_norm, ambiguous = candidates[0][0], True
                        elif dst_doc == cx.DOC_GENERAL:
                            # The citing act still points at an article that has since
                            # been repealed: a real finding, kept and flagged.
                            dangling = True
                    elif c.target_kind in ("chapter", "section"):
                        node = f"C{c.struct_number}" + (f".S{c.section_number}"
                                                        if c.target_kind == "section" else "")
                        if node not in struct_doc:
                            continue
                        dst_struct, dst_doc = node, struct_doc[node]
                    else:  # act-level
                        dst_doc = None

                    # The Code is published as two acts (General and Special Part);
                    # a reference between them is still internal to the same code.
                    if doc_id in CC_DOCS and (dst_doc in CC_DOCS or c.anchor == "self_reference"):
                        rel, hrel = "internal", "self"
                    elif src_tier == UNCLASSIFIED_TIER:
                        # Act type unknown (see act.tier_note): we cannot claim it sits
                        # below the Code, so it stays out of the realization graph.
                        rel, hrel = "cites", "unknown"
                    elif src_tier > CC_TIER:
                        rel, hrel = "realizes", "below"
                    elif src_tier == CC_TIER:
                        rel, hrel = "cites", "same"
                    else:
                        rel, hrel = "cites", "above"

                    conf = BASE_CONFIDENCE[(field, c.target_kind)]
                    if c.anchor == "fk_alias":
                        conf *= 0.95
                    if ambiguous:
                        conf = min(conf, 0.60)
                    if dangling:
                        conf = min(conf, 0.70)

                    edge_id += 1
                    edges.append([
                        edge_id, run_id, row_id, doc_id, doc_type, src_tier, art_no,
                        c.target_kind, dst_doc, dst_art, dst_norm, dst_struct, c.qism, ambiguous, dangling,
                        hrel, rel, c.anchor, c.listing, field, EVIDENCE_KIND[field],
                        f"explicit_citation_uz/{c.anchor}", round(conf, 3),
                        c.evidence, clean_evidence(c.evidence), c.start, c.end, None, None,
                    ])
        if scanned % 5000 < BATCH:
            log(f"  {scanned}/{total} rows -> {len(edges)} edges")

    con.executemany(
        "INSERT INTO link_edge VALUES (" + ",".join("?" * 29) + ")", edges
    )
    con.commit()
    log(f"\nlink_edge: {len(edges)} edges written")

    log("\nby target kind / hierarchy relation:")
    for r in con.execute("""
        SELECT dst_kind, hierarchy_rel, count(*) n, count(DISTINCT src_doc_id) acts
        FROM link_edge GROUP BY 1, 2 ORDER BY n DESC
    """).fetchall():
        log(f"  {r[0]:<8} {r[1]:<6} edges={r[2]:<6} citing acts={r[3]}")

    log("\nrealization edges by evidence kind:")
    for r in con.execute("""
        SELECT evidence_kind, count(*) n, count(DISTINCT src_doc_id) acts
        FROM link_edge WHERE hierarchy_rel = 'below' GROUP BY 1 ORDER BY n DESC
    """).fetchall():
        log(f"  {r[0]:<10} edges={r[1]:<6} acts={r[2]}")

    # ------------------------------------------------------------ provisions
    # The citing provision itself.  Without this the UI can only show the ±90
    # character evidence window, which for an editorial citation is LexUZ's
    # apparatus rather than a legal norm — you see a pointer, never the rule.
    con.execute(f"""
        CREATE OR REPLACE TABLE src_provision AS
        SELECT
            p.file_row_number          AS row_id,
            p.doc_id,
            p.article_number,
            p.article_title,
            p.article_text,
            length(p.article_text)     AS text_len,
            p.chapter                  AS chapter_raw,
            -- rows with no article number hold the whole act in one blob; the
            -- article text is then not a single provision and must be excerpted.
            (p.article_number IS NULL OR trim(p.article_number) = '') AS is_whole_act_blob
        FROM {raw} p
        WHERE p.file_row_number IN (SELECT DISTINCT src_row_id FROM link_edge)
    """)
    con.commit()
    n_prov, n_blob = con.execute(
        "SELECT count(*), count(*) FILTER (WHERE is_whole_act_blob) FROM src_provision"
    ).fetchone()
    log(f"\nsrc_provision: {n_prov} citing provisions "
        f"({n_blob} are whole-act blobs with no article number)")

    # One row per (General Part article, realizing act): the pyramid's data source.
    con.execute(f"""
        CREATE OR REPLACE VIEW v_realization AS
        SELECT
            n.norm_id, n.article_number, n.article_base, n.superscript,
            n.article_title_uz, n.article_title_en, n.struct_node_id,
            e.src_doc_id, a.doc_title AS src_doc_title, e.src_doc_type, e.src_tier,
            a.doc_date AS src_doc_date, a.source_url AS src_url,
            e.src_article_number, e.dst_qism,
            e.relation, e.hierarchy_rel, e.source_field, e.evidence_kind,
            e.confidence, e.evidence, e.evidence_clean,
            -- the realizing norm itself, so the reader sees a rule not a pointer
            v.article_number AS src_prov_number,
            v.article_title  AS src_prov_title,
            v.article_text   AS src_prov_text,
            v.is_whole_act_blob AS src_prov_is_blob,
            e.dst_ambiguous, e.validated_by, e.edge_id
        FROM norm_unit n
        JOIN link_edge e ON e.dst_norm_id = n.norm_id
        JOIN act a       ON a.doc_id = e.src_doc_id
        LEFT JOIN src_provision v ON v.row_id = e.src_row_id
        WHERE e.dst_doc_id = {cx.DOC_GENERAL}
    """)
    # Chapter/section-level citations, which attach to a structural node rather
    # than to one article.
    con.execute("""
        CREATE OR REPLACE VIEW v_realization_struct AS
        SELECT s.node_id, s.kind, s.label_en, s.art_from, s.art_to,
               e.src_doc_id, a.doc_title AS src_doc_title, e.src_doc_type, e.src_tier,
               e.relation, e.hierarchy_rel, e.confidence, e.evidence, e.edge_id
        FROM struct_node s
        JOIN link_edge e ON e.dst_struct_node_id = s.node_id
        JOIN act a       ON a.doc_id = e.src_doc_id
    """)
    con.commit()

    # -------------------------------------------------------------- repeals
    # act.status is 'in-force' for all 24,267 acts, so the corpus cannot say what
    # is still law.  An act's own repeal clause can: "Quyidagilar oʻz kuchini
    # yoʻqotgan deb topilsin: 1) ... 2001-yil 6-dekabrda qabul qilingan
    # '...toʻgʻrisida'gi 310-II-sonli Qonuni".  We extract the clause and match
    # the repealed act by (date, document number), both of which it states.
    con.execute("""
        CREATE OR REPLACE TABLE repeal_clause (
            clause_id   INTEGER,
            src_doc_id  BIGINT,      -- the act doing the repealing
            src_row_id  BIGINT,
            item_no     INTEGER,     -- position in the enumerated repeal list
            cited_date  VARCHAR,     -- '2001-yil 6-dekabr'  (as written)
            cited_number VARCHAR,    -- '310-II'
            dst_doc_id  BIGINT,      -- resolved target, NULL if unresolved
            match_method VARCHAR,
            evidence    VARCHAR
        );
    """)

    UZ_MONTHS = {"yanvar": 1, "fevral": 2, "mart": 3, "aprel": 4, "may": 5, "iyun": 6,
                 "iyul": 7, "avgust": 8, "sentabr": 9, "oktabr": 10, "noyabr": 11,
                 "dekabr": 12}
    re_clause = re.compile(r"kuchini\s+yo\wqotgan\s+deb\s+topilsin", re.IGNORECASE)
    # "2001-yil 6-dekabrda qabul qilingan “Masʼuliyati cheklangan jamiyatlar
    #  toʻgʻrisida”gi 310-II-sonli Qonuni" — the clause states the date, the
    # title in quotes and the document number.  doc_number is empty for every
    # act in this corpus, so (date + title) is the only usable key.
    re_item = re.compile(
        r"(?P<y>\d{4})-yil\s+(?P<d>\d{1,2})-(?P<mon>[a-zʻʼʻʼ]+)\w*\s+qabul\s+qilingan"
        r"[^“”\"]{0,120}?[“\"](?P<title>[^“”\"]{6,300})[”\"]"
        r"(?:\s*\w*\s*(?P<num>[\dA-ZIVX\-]{2,14})-sonli)?",
        re.IGNORECASE | re.DOTALL,
    )

    def norm_title(s: str) -> str:
        s = re.sub(r"[ʻʼ'`ʻʼ‘’]", "'", (s or "").lower())
        return re.sub(r"\s+", " ", s).strip(" .,;:\"'")

    by_date_title: dict[tuple[str, str], int] = {}
    by_date: dict[str, list[tuple[int, str]]] = {}
    for d_id, d_date, d_title in con.execute(
        "SELECT doc_id, doc_date, doc_title FROM act"
    ).fetchall():
        if d_date and d_title:
            iso_d = str(d_date)[:10]
            nt_d = norm_title(d_title)
            by_date_title[(iso_d, nt_d)] = d_id
            by_date.setdefault(iso_d, []).append((d_id, nt_d))

    # The clause item's quoted title is only ever a *substring* of the resolved
    # act's own title when the item is really citing an amending act ("...gi
    # Qonuniga oʻzgartishlar va qoʻshimchalar kiritish toʻgʻrisida"): the quote
    # names the ORIGINAL law, the act being repealed is the amendment to it, and
    # both share the item's cited date (measured 2026-09-06 against the 175
    # items the exact (date,title) match left unresolved — see DAILY_REVIEW.md).
    # Tier 2 exploits that: unique substring match against every act on the same
    # date. Tier 3 catches spelling variants of the SAME title on the same date
    # (oʻzgartish/oʻzgartirish, tashkilotlarning/tashkilotlarining, ...) via
    # similarity ratio, only when there is a clear, unambiguous winner.
    def resolve_fallback(iso: str, nt: str) -> tuple[int | None, str]:
        candidates = by_date.get(iso, [])
        if not candidates:
            return None, "unresolved"
        substr = [(d_id, dt) for d_id, dt in candidates if nt in dt]
        if len(substr) == 1:
            return substr[0][0], "date+substring"
        if len(substr) > 1:
            return None, "unresolved"  # ambiguous: never observed, but stay silent rather than guess
        scored = sorted(
            ((difflib.SequenceMatcher(None, nt, dt).ratio(), d_id) for d_id, dt in candidates),
            reverse=True,
        )
        best_ratio, best_id = scored[0]
        second_ratio = scored[1][0] if len(scored) > 1 else 0.0
        if best_ratio >= 0.80 and (best_ratio - second_ratio) >= 0.15:
            return best_id, f"date+fuzzy:{best_ratio:.2f}"
        return None, "unresolved"

    clauses: list[list] = []
    cur2 = con.cursor().execute(f"""
        SELECT file_row_number, doc_id, article_text FROM {raw}
        WHERE regexp_matches(lower(article_text), 'kuchini yo.?qotgan deb topilsin')
    """)
    cid = 0
    method_counts: dict[str, int] = {}
    for row_id, doc_id, text in cur2.fetchall():
        m0 = re_clause.search(text)
        if not m0:
            continue
        tail = text[m0.end(): m0.end() + 8000]
        for i, m in enumerate(re_item.finditer(tail), 1):
            mon = next((v for k, v in UZ_MONTHS.items()
                        if m.group("mon").lower().startswith(k[:4])), None)
            iso = f"{m.group('y')}-{mon:02d}-{int(m.group('d')):02d}" if mon else None
            nt = norm_title(m.group("title"))
            dst = by_date_title.get((iso, nt)) if iso else None
            method = "date+title" if dst else "unresolved"
            if dst is None and iso:
                dst, method = resolve_fallback(iso, nt)
            method_counts[method] = method_counts.get(method, 0) + 1
            cid += 1
            clauses.append([cid, doc_id, row_id, i,
                            f"{m.group('y')}-yil {m.group('d')}-{m.group('mon')}",
                            (m.group("num") or "").strip().upper() or None,
                            dst, method,
                            re.sub(r"\s+", " ",
                                   tail[max(0, m.start() - 40): m.end() + 40]).strip()])
    con.executemany("INSERT INTO repeal_clause VALUES (" + ",".join("?" * 9) + ")", clauses)
    con.commit()
    resolved = sum(1 for c in clauses if c[6] is not None)
    log(f"\nrepeal_clause: {len(clauses)} repeal items from "
        f"{len({c[1] for c in clauses})} acts; {resolved} resolved to a corpus act")
    log(f"  by match_method: {method_counts}")

    # An act is superseded if a later act repealed it by date+number.
    con.execute("""
        CREATE OR REPLACE VIEW v_act_currency AS
        SELECT a.doc_id, a.doc_title, a.doc_date, a.doc_number, a.tier, a.status AS corpus_status,
               r.src_doc_id AS repealed_by, ra.doc_title AS repealed_by_title,
               ra.doc_date  AS repealed_on, r.evidence AS repeal_evidence,
               CASE WHEN r.src_doc_id IS NOT NULL THEN 'superseded' ELSE 'no repeal found' END
                   AS derived_status
        FROM act a
        LEFT JOIN repeal_clause r ON r.dst_doc_id = a.doc_id
        LEFT JOIN act ra          ON ra.doc_id = r.src_doc_id
    """)
    con.commit()

    log("\nGeneral Part coverage:")
    cov = con.execute(f"""
        SELECT count(DISTINCT dst_norm_id) FROM link_edge
        WHERE dst_doc_id = {cx.DOC_GENERAL} AND dst_norm_id IS NOT NULL
    """).fetchone()[0]
    below = con.execute(f"""
        SELECT count(DISTINCT dst_norm_id) FROM link_edge
        WHERE dst_doc_id = {cx.DOC_GENERAL} AND hierarchy_rel = 'below'
    """).fetchone()[0]
    log(f"  {cov}/386 articles have at least one incoming edge")
    log(f"  {below}/386 have at least one edge from a LOWER act (realization)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
