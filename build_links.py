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
                    stored_kind = c.target_kind

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
                        if node in struct_doc:
                            dst_struct, dst_doc = node, struct_doc[node]
                        else:
                            # The named sub-paragraph doesn't exist as a struct node
                            # today (e.g. a stale cross-reference to a
                            # pre-restructuring numbering — "2-bob, 2-paragrafi"
                            # cited when chapter 2 currently has no sub-paragraphs
                            # at all). Fall back to the chapter itself rather than
                            # dropping the edge outright, same principle as the
                            # article-level dangling fallback above — the chapter
                            # is real even though the paragraph pin isn't.
                            # Measured 2026-09-10: exactly 1 occurrence corpus-wide
                            # (see DAILY_REVIEW.md).
                            chapter_node = f"C{c.struct_number}"
                            if chapter_node not in struct_doc:
                                continue
                            dst_struct, dst_doc = chapter_node, struct_doc[chapter_node]
                            stored_kind = "chapter"
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

                    conf = BASE_CONFIDENCE[(field, stored_kind)]
                    if c.anchor == "fk_alias":
                        conf *= 0.95
                    if ambiguous:
                        conf = min(conf, 0.60)
                    if dangling:
                        conf = min(conf, 0.70)

                    edge_id += 1
                    edges.append([
                        edge_id, run_id, row_id, doc_id, doc_type, src_tier, art_no,
                        stored_kind, dst_doc, dst_art, dst_norm, dst_struct, c.qism, ambiguous, dangling,
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

    # Measured 2026-09-09 (see DAILY_REVIEW.md): every one of the 45 items no
    # tier above resolves is a genuine corpus-coverage gap, not an extraction
    # bug — split cleanly into two causes. (1) The repealed document is a
    # Qaror/Farmon (a parliamentary/Cabinet resolution or presidential/Soviet
    # decree), not a Qonun (law): `act` carries essentially none of these —
    # corpus-wide, only 24/856 Qonuni citations vs 0/24 Qarori and 0/3 Farmon
    # resolve at the exact (date,title) tier, and a direct search for the most
    # common missing kind ("...amalga kiritish tartibi toʻgʻrisida" enactment
    # resolutions for the Labor/Urban-Planning/Housing/Civil-Procedure/
    # Economic-Procedure Codes) finds exactly one such act in the whole
    # corpus — the 1992 Constitution's own. (2) The rest are acts of
    # Qoraqalpogʻiston Respublikasi (Karakalpakstan) or pre-1991 Soviet-era
    # decrees that simply have no `act` row on their cited date at all
    # (verified directly: zero acts on 6 of 8 distinct Qoraqalpogʻiston dates
    # cited by row 16788 alone). Tag cause (1) explicitly, since it is a
    # cheap, unambiguous regex check on the word right after the quoted
    # title and turns an undifferentiated "unresolved" into "we know why,
    # verified" for 27 of 45 items — cause (2) has no comparably cheap
    # detector and stays generic "unresolved".
    re_repealed_kind = re.compile(r'^["”]\s*(?:g[ai]\s+)?(?:\S+\s+){0,4}?(Qonun|Qaror|Farmon)\w*', re.IGNORECASE)

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
            if dst is None:
                after = tail[m.end("title"): m.end("title") + 60]
                km = re_repealed_kind.match(after)
                if km and km.group(1).lower() in ("qaror", "farmon"):
                    method = "unresolved:non-statute"
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

    # ----------------------------------------------------------- amendments
    # A whole-act repeal isn't the only way a law changes.  Far more common:
    # one act edits specific articles of another without repealing it.  LexUZ
    # already records this, per article, in `amendment_note` — e.g. "(8-modda
    # birinchi qismining oltinchi xatboshisi Oʻzbekiston Respublikasining
    # 2025-yil 30-dekabrdagi OʻRQ-1109-sonli Qonuni tahririda — ...)". This is
    # a BETTER source than trying to detect "...kiritilsin"-style clauses
    # inside amending acts' own free text the way repeal_clause does for
    # repeals: those clauses are noisy (any decree can contain "kiritilsin"
    # for an unrelated reason) and would need the same fragile numbered-list
    # parsing repeal_clause uses, just one more grammar. `amendment_note` is
    # already LexUZ's own structured annotation of the *effect*, one event
    # per parenthetical clause, so we parse that instead.
    #
    # Scoped to the Civil Code's own two docs (CC_DOCS) — that's what
    # norm_unit/struct_node can anchor an article to, and it's this corpus's
    # subject. Measured 2026-09-11: the same grammar parses 97.4% of clauses
    # (23307/23919) across ALL 12,166 rows with an amendment_note corpus-wide,
    # so this generalizes well beyond the Civil Code if a future session
    # wants to widen scope — not done here given the time budget and that
    # norm_id/struct_node resolution only exists for the Civil Code today.
    con.execute("""
        CREATE OR REPLACE TABLE article_amendment (
            event_id             INTEGER,
            doc_id               BIGINT,   -- Civil Code part carrying the note
            host_article_number  VARCHAR,  -- the row's own article_number
            target_article_number VARCHAR, -- article the clause is actually about;
                                            -- NULL for a chapter/paragraph-level clause
            norm_id              VARCHAR,  -- norm_unit.norm_id, General Part only
            locator              VARCHAR,  -- raw sub-unit text ("birinchi qismi", "6-bob", ...)
            change_type          VARCHAR,  -- restated|supplemented|removed|inserted|replaced|voided
            amend_date           VARCHAR,  -- ISO, the amending law's adoption date
            amend_act_number     VARCHAR,  -- 'OʻRQ-1109' or legacy '832-I'
            effective_date       VARCHAR,  -- ISO, nullable (delayed entry into force)
            amending_doc_id      BIGINT,   -- resolved act, NULL if unresolved
            match_method         VARCHAR,
            evidence             VARCHAR
        );
    """)

    re_amend_clause = re.compile(r"\((?:[^()]|\([^()]*\))*\)")
    re_amend_event = re.compile(
        r"(?P<locator>.*?)"
        r"O\wzbekiston\s+Respublikasi\w*\s+"
        r"(?P<y>\d{4})-yil\s+(?P<d>\d{1,2})-(?P<mon>[a-z]+)\w*\s+"
        r"(?:O\wRQ-(?P<num>\d+)-sonli|(?P<num2>\d+)[-–](?:(?P<roman>[IVX]+)-)?son(?:li)?)\s+"
        r"Qonun\w*\s+"
        r"(?P<verb>.*?)"
        r"(?:\s*—\s*(?P<src>.*?))?"
        r"\)$",
        re.IGNORECASE | re.DOTALL,
    )
    re_target_article = re.compile(r"(\d{1,5})\s*-?\s*modda", re.IGNORECASE)
    re_any_date = re.compile(r"(\d{4})-yil\s+(\d{1,2})-([a-z]+)\w*", re.IGNORECASE)
    re_verb_map = [
        (re.compile(r"tahririda", re.IGNORECASE), "restated"),
        (re.compile(r"to\wldirilgan", re.IGNORECASE), "supplemented"),
        (re.compile(r"to\wldirib", re.IGNORECASE), "supplemented"),
        (re.compile(r"chiqarib tashlangan", re.IGNORECASE), "removed"),
        (re.compile(r"chiqaril", re.IGNORECASE), "removed"),       # chiqarilgan, chiqarilish sanasi
        (re.compile(r"almashtirilgan", re.IGNORECASE), "replaced"),
        (re.compile(r"kiritilgan", re.IGNORECASE), "inserted"),
        (re.compile(r"kuchini yo\wqot", re.IGNORECASE), "voided"), # yoʻqotgan, yoʻqotish sanasi
        (re.compile(r"kuchga ega emas", re.IGNORECASE), "voided"),
    ]

    def classify_amend(verb: str) -> str:
        for pat, label in re_verb_map:
            if pat.search(verb):
                return label
        return "other"

    def amend_to_iso(y: str, d: str, mon: str) -> str | None:
        monl = mon.lower()
        m = next((v for k, v in UZ_MONTHS.items() if monl.startswith(k[:4])), None)
        return f"{y}-{m:02d}-{int(d):02d}" if m else None

    norm_by_article = {
        art: nid for nid, art in con.execute(
            f"SELECT norm_id, article_number FROM norm_unit WHERE doc_id = {cx.DOC_GENERAL}"
        ).fetchall()
    }
    re_civil_title = re.compile(r"fuqarolik kodeks", re.IGNORECASE)

    amend_rows: list[list] = []
    aid = 0
    amend_method_counts: dict[str, int] = {}
    amend_type_counts: dict[str, int] = {}
    for doc_id in CC_DOCS:
        cur3 = con.cursor().execute(f"""
            SELECT file_row_number, article_number, amendment_note FROM {raw}
            WHERE doc_id = {doc_id} AND amendment_note IS NOT NULL AND amendment_note != ''
        """)
        for _row_id, host_art, note in cur3.fetchall():
            for c in re_amend_clause.findall(note):
                m = re_amend_event.match(c)
                if not m:
                    continue
                amend_date = amend_to_iso(m.group("y"), m.group("d"), m.group("mon"))
                num = m.group("num")
                act_number = (f"OʻRQ-{num}" if num else
                              (m.group("num2") or "") +
                              (f"-{m.group('roman')}" if m.group("roman") else "") + "-son")
                scope = (m.group("locator") or "") + " " + (m.group("verb") or "")
                tm = re_target_article.search(scope)
                target_art = tm.group(1) if tm else None
                eff_date = None
                for y2, d2, mo2 in re_any_date.findall(c):
                    iso2 = amend_to_iso(y2, d2, mo2)
                    if iso2 and iso2 != amend_date:
                        eff_date = iso2
                        break
                ctype = classify_amend(m.group("verb") or "")
                amend_type_counts[ctype] = amend_type_counts.get(ctype, 0) + 1
                # Only fall back to the host article's norm_id when the clause
                # names no target of its own (a chapter/paragraph-level note);
                # when it names a *different*, now-gone article (the voided-
                # neighbor case — see DAILY_REVIEW.md), that article genuinely
                # has no norm_unit row, so norm_id must stay NULL, not borrow
                # the host's.
                lookup_art = target_art if target_art is not None else host_art
                norm_id = norm_by_article.get(lookup_art) if doc_id == cx.DOC_GENERAL else None
                amending_doc_id, method = None, "unresolved"
                if amend_date:
                    civil_cands = [d_id for d_id, nt_d in by_date.get(amend_date, [])
                                   if re_civil_title.search(nt_d)]
                    if len(civil_cands) == 1:
                        amending_doc_id, method = civil_cands[0], "date+civil-code-title"
                amend_method_counts[method] = amend_method_counts.get(method, 0) + 1
                aid += 1
                amend_rows.append([
                    aid, doc_id, host_art, target_art, norm_id,
                    (m.group("locator") or "").strip(" ("),
                    ctype, amend_date, act_number, eff_date,
                    amending_doc_id, method, c,
                ])
    con.executemany(
        "INSERT INTO article_amendment VALUES (" + ",".join("?" * 13) + ")", amend_rows)
    con.commit()
    log(f"\narticle_amendment: {len(amend_rows)} amendment events from "
        f"{len({(r[1], r[2]) for r in amend_rows})} host rows "
        f"(see v_article_currency for the distinct-target-article count)")
    log(f"  by change_type: {amend_type_counts}")
    log(f"  by match_method: {amend_method_counts}")

    con.execute("""
        CREATE OR REPLACE VIEW v_article_currency AS
        SELECT doc_id,
               coalesce(target_article_number, host_article_number) AS article_number,
               max(norm_id)                                AS norm_id,
               count(*)                                     AS n_amendments,
               max(amend_date)                               AS last_amend_date,
               arg_max(change_type, amend_date)               AS last_change_type,
               bool_or(change_type IN ('removed', 'voided')) AS has_removed_or_voided_part
        FROM article_amendment
        GROUP BY doc_id, coalesce(target_article_number, host_article_number)
    """)
    con.commit()

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
