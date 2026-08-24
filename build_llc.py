#!/usr/bin/env python
"""
LLC slice — a single-institution dossier built on the General Part foundation.

Navigating all 386 General Part articles is too broad to be useful day to day.
This narrows to one institution, the limited liability company (masʼuliyati
cheklangan jamiyat, MCHJ), and assembles the three axes around it:

    foundation   Civil Code General Part articles the LLC rests on
    special law  the LLC Law's own articles, the tier below the Code
    realization  acts below the special law that implement it

The skeleton (stages) is DERIVED from the current LLC Law's own chapters, not
invented: the legislator already grouped the institution's lifecycle.  Only the
Civil Code foundation mapping is curated, because deciding which general norm a
company-law chapter rests on is a legal judgment, and it is recorded per stage
with a rationale so the owner can overrule it.

    python build_llc.py
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "corpus.duckdb"
PARQUET = ROOT / "articles" / "train-00000-of-00001.parquet"

# The institution.
LLC_OKOZ = "03.03.05.04"          # Limited Liability Company. Additional Liability Company
LLC_LAW_CURRENT = -8151376        # 2026-04-21, 71 articles, 8 chapters
LLC_LAW_PRIOR = -22525            # 2001-12-06, repealed by art. 68 of the 2026 Law
CC_GENERAL = -111189

# Civil Code General Part articles the LLC rests on, per stage of the LLC Law's
# own chapter structure.  `None` in the article list means the stage has no
# distinct general-part anchor beyond the ones its parent stage already carries.
#   stage key -> {cc article number: why it is the foundation}
FOUNDATION: dict[int, dict[str, str]] = {
    1: {  # Umumiy qoidalar — general provisions / legal status
        "39": "defines what a legal entity is; the LLC is one",
        "40": "types of legal entities — places the LLC among commercial organisations",
        "41": "legal capacity, which the LLC exercises",
        "45": "bodies of a legal entity — the genus of the LLC's governance organs",
        "46": "name and location, specialised by LLC Law art. 5",
        "47": "representative offices and branches, specialised by LLC Law art. 6",
        "48": "liability of a legal entity, specialised by LLC Law art. 4",
        "58": "basic rules on business partnerships and companies — the LLC's family",
        "59": "rights and obligations of participants in a business company",
        "62": "THE anchor: 'Masʼuliyati cheklangan jamiyat' defines the LLC in the Code",
    },
    2: {  # Jamiyatni taʼsis etish — formation
        "42": "creation of legal entities",
        "43": "constituent documents, specialised by LLC Law arts. 12-14",
        "44": "state registration of legal entities",
    },
    3: {  # Ustav fondi — charter capital
        "62": "art. 62 fixes the charter-fund rule the LLC Law elaborates",
    },
    4: {  # Boshqaruv — governance
        "45": "bodies of a legal entity acquire their competence here",
    },
    5: {  # Manfaatdorlik / yirik bitimlar — interested-party and major transactions
        "101": "concept and form of transactions — the genus of a 'major transaction'",
        "102": "types of transactions",
        "113": "invalidity of transactions, the sanction behind the approval rules",
    },
    6: {},  # Nazorat — audit/control: no distinct General Part anchor
    7: {  # Affillangan shaxslar — affiliated persons
        "67": "subsidiary business company",
        "68": "dependent business company",
    },
    8: {  # Qayta tashkil etish va tugatish — reorganisation and liquidation
        "49": "reorganisation of a legal entity",
        "50": "legal succession on reorganisation",
        "51": "transfer deed and separation balance sheet",
        "52": "creditors' guarantees on reorganisation",
        "53": "liquidation of a legal entity",
        "54": "decision to liquidate",
        "55": "liquidation procedure",
        "56": "satisfaction of creditors' claims",
        "57": "insolvency of a legal entity",
    },
}

# Articles the Code once carried for company forms and no longer does.  They are
# a live issue for the LLC: acts still in force cite them.
REPEALED_COMPANY_ARTICLES = ["63", "65", "66", "70", "71", "72"]

# An act referring to the LLC Law by its title, rather than to the Code.
RE_LLC_LAW_REF = re.compile(
    r"mas.?uliyati\s+cheklangan(?:\s+hamda\s+qo.?shimcha\s+mas.?uliyatli)?"
    r"\s+jamiyat\w*\s+to.?g.?risida",
    re.IGNORECASE,
)


def log(msg: str = "") -> None:
    print(msg, flush=True)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("llc-%Y%m%dT%H%M%SZ")
    con = duckdb.connect(str(DB_PATH))
    raw = f"read_parquet('{PARQUET.as_posix()}', file_row_number=true)"

    # ------------------------------------------------------- stages (derived)
    # The LLC Law states its own chapters; parse "N-bob. Title" and take each
    # chapter's article span from the rows themselves.
    chapters = con.execute(f"""
        SELECT
            CAST(regexp_extract(chapter, '^(\\d+)-bob', 1) AS INTEGER) AS stage_no,
            regexp_replace(chapter, '^\\d+-bob\\.\\s*', '')            AS stage_label,
            min(CAST(article_number AS INTEGER))                       AS art_from,
            max(CAST(article_number AS INTEGER))                       AS art_to,
            count(*)                                                   AS n_articles
        FROM {raw}
        WHERE doc_id = {LLC_LAW_CURRENT} AND regexp_matches(chapter, '^\\d+-bob')
        GROUP BY 1, 2 ORDER BY 1
    """).fetchall()
    if not chapters:
        log("ERROR: could not derive chapters from the current LLC Law")
        return 1

    con.execute("""
        CREATE OR REPLACE TABLE llc_stage (
            stage_no    INTEGER PRIMARY KEY,
            stage_label VARCHAR,      -- as the law titles it (Uzbek)
            art_from    INTEGER,      -- LLC Law article span
            art_to      INTEGER,
            n_articles  INTEGER,
            n_foundation INTEGER      -- Civil Code articles it rests on
        );
    """)
    con.executemany(
        "INSERT INTO llc_stage VALUES (?, ?, ?, ?, ?, ?)",
        [(c[0], c[1], c[2], c[3], c[4], len(FOUNDATION.get(c[0], {}))) for c in chapters],
    )
    log(f"llc_stage: {len(chapters)} stages derived from the current LLC Law's chapters")

    # -------------------------------------------------------------- the norms
    # Two layers in one table: the Code's general norm and the special law's
    # article that specialises it.  `layer` keeps them distinguishable.
    con.execute("""
        CREATE OR REPLACE TABLE llc_norm (
            norm_key     VARCHAR PRIMARY KEY,
            stage_no     INTEGER,
            layer        VARCHAR,     -- foundation (Civil Code) | special (LLC Law)
            doc_id       BIGINT,
            article_number VARCHAR,
            article_title  VARCHAR,
            article_text   VARCHAR,
            article_title_en VARCHAR, -- Civil Code only
            cc_norm_id     VARCHAR,   -- link into norm_unit for foundation rows
            rationale      VARCHAR,   -- why this Code article founds this stage
            row_id         BIGINT
        );
    """)

    rows: list[list] = []
    # foundation layer — curated, joined to the verified norm_unit table
    seen: set[str] = set()
    for stage_no, arts in FOUNDATION.items():
        for art, why in arts.items():
            rec = con.execute("""
                SELECT norm_id, article_number, article_title_uz, article_text_uz,
                       article_title_en, src_row
                FROM norm_unit WHERE article_number = ? AND superscript IS NULL
            """, [art]).fetchone()
            if not rec:
                log(f"  WARN foundation article {art} not in the corpus (repealed?)")
                continue
            key = f"F{stage_no}-{art}"
            if key in seen:
                continue
            seen.add(key)
            rows.append([key, stage_no, "foundation", CC_GENERAL, rec[1], rec[2],
                         rec[3], rec[4], rec[0], why, rec[5]])

    # special layer — every article of the current LLC Law, placed in its chapter
    for r in con.execute(f"""
        SELECT file_row_number, article_number, article_title, article_text,
               CAST(regexp_extract(chapter, '^(\\d+)-bob', 1) AS INTEGER) AS stage_no
        FROM {raw}
        WHERE doc_id = {LLC_LAW_CURRENT} AND regexp_matches(chapter, '^\\d+-bob')
        ORDER BY file_row_number
    """).fetchall():
        rows.append([f"L{r[1]}", r[4], "special", LLC_LAW_CURRENT, r[1], r[2],
                     r[3], None, None, None, r[0]])

    con.executemany("INSERT INTO llc_norm VALUES (" + ",".join("?" * 11) + ")", rows)
    con.commit()
    n_found = sum(1 for r in rows if r[2] == "foundation")
    log(f"llc_norm: {n_found} foundation (Civil Code) + {len(rows)-n_found} special "
        f"(LLC Law) norms")

    # ------------------------------------------------- implementing acts below
    # Two independent routes to the same question — which acts implement the
    # LLC?  (a) they cite a Civil Code article the LLC rests on; (b) they name
    # the LLC Law itself.  Route (b) is new: link_edge only tracks the Code.
    con.execute("""
        CREATE OR REPLACE TABLE llc_implementing_act (
            doc_id      BIGINT,
            route       VARCHAR,     -- cites_cc_foundation | names_llc_law
            tier        INTEGER,
            doc_title   VARCHAR,
            doc_date    VARCHAR,
            n_hits      INTEGER,
            stages      VARCHAR,     -- stages touched, for cites_cc_foundation
            derived_status VARCHAR,
            evidence    VARCHAR
        );
    """)

    found_arts = sorted({a for s in FOUNDATION.values() for a in s})
    con.execute("""
        INSERT INTO llc_implementing_act
        SELECT e.src_doc_id, 'cites_cc_foundation', e.src_tier, a.doc_title, a.doc_date,
               count(*) AS n_hits,
               string_agg(DISTINCT CAST(n.stage_no AS VARCHAR), ',') AS stages,
               c.derived_status,
               max(e.evidence_clean)
        FROM link_edge e
        JOIN act a ON a.doc_id = e.src_doc_id
        JOIN llc_norm n ON n.article_number = e.dst_article_number
                       AND n.layer = 'foundation'
        JOIN v_act_currency c ON c.doc_id = e.src_doc_id
        WHERE e.hierarchy_rel = 'below' AND e.dst_doc_id = ?
        GROUP BY 1, 2, 3, 4, 5, 8
    """, [CC_GENERAL])

    # route (b): scan for acts naming the LLC Law
    hits: dict[int, list] = {}
    cur = con.cursor().execute(f"""
        SELECT file_row_number, doc_id, article_text FROM {raw}
        WHERE doc_id NOT IN ({LLC_LAW_CURRENT}, {LLC_LAW_PRIOR})
          AND regexp_matches(lower(coalesce(article_text,'')),
                             'mas.?uliyati cheklangan')
    """)
    for row_id, doc_id, text in cur.fetchall():
        m = RE_LLC_LAW_REF.search(text or "")
        if not m:
            continue
        ev = re.sub(r"\s+", " ", text[max(0, m.start() - 110): m.end() + 110]).strip()
        rec = hits.setdefault(doc_id, [0, ev])
        rec[0] += 1
    if hits:
        meta = {r[0]: r for r in con.execute(f"""
            SELECT a.doc_id, a.tier, a.doc_title, a.doc_date, c.derived_status
            FROM act a JOIN v_act_currency c ON c.doc_id = a.doc_id
            WHERE a.doc_id IN ({','.join(str(d) for d in hits)})
        """).fetchall()}
        con.executemany(
            "INSERT INTO llc_implementing_act VALUES (?, 'names_llc_law', ?, ?, ?, ?, NULL, ?, ?)",
            [[d, meta[d][1], meta[d][2], meta[d][3], v[0], meta[d][4], v[1]]
             for d, v in hits.items() if d in meta],
        )
    con.commit()

    # ------------------------------------------------------------------ views
    con.execute("""
        CREATE OR REPLACE VIEW v_llc_skeleton AS
        SELECT s.stage_no, s.stage_label, s.art_from, s.art_to, s.n_articles,
               n.layer, n.article_number, n.article_title, n.article_title_en,
               n.rationale, n.cc_norm_id, n.norm_key, n.article_text
        FROM llc_stage s LEFT JOIN llc_norm n ON n.stage_no = s.stage_no
    """)
    # Realization restricted to the LLC's own foundation articles, carrying the
    # citing provision's text and whether that act is still law.
    con.execute(f"""
        CREATE OR REPLACE VIEW v_llc_realization AS
        SELECT DISTINCT
            n.stage_no, n.article_number AS cc_article, n.article_title AS cc_title,
            e.src_doc_id, a.doc_title AS src_doc_title, e.src_tier, a.doc_date,
            a.source_url, e.evidence_kind, e.confidence, e.evidence_clean,
            p.article_number AS src_prov_number, p.article_title AS src_prov_title,
            p.article_text   AS src_prov_text, p.is_whole_act_blob,
            c.derived_status, c.repealed_by_title, e.edge_id
        FROM llc_norm n
        JOIN link_edge e ON e.dst_article_number = n.article_number
                        AND e.dst_doc_id = {CC_GENERAL} AND e.hierarchy_rel = 'below'
        JOIN act a           ON a.doc_id = e.src_doc_id
        LEFT JOIN src_provision p ON p.row_id = e.src_row_id
        JOIN v_act_currency c ON c.doc_id = e.src_doc_id
        WHERE n.layer = 'foundation'
    """)
    con.commit()

    # ----------------------------------------------------------------- report
    log("\nLLC skeleton (stage <- Civil Code foundation):")
    for s_no, label, a_from, a_to, n_art, n_f in con.execute(
            "SELECT * FROM llc_stage ORDER BY stage_no").fetchall():
        arts = ", ".join(sorted(FOUNDATION.get(s_no, {}), key=int)) or "—"
        log(f"  {s_no}. {label[:46]:<46} LLC arts {a_from}-{a_to} ({n_art})")
        log(f"     CC foundation: {arts}")

    log("\nimplementing acts found:")
    for route, tier, n in con.execute("""
        SELECT route, tier, count(DISTINCT doc_id) FROM llc_implementing_act
        GROUP BY 1, 2 ORDER BY 1, 2
    """).fetchall():
        log(f"  {route:<22} tier {tier}: {n} acts")
    sup = con.execute("""
        SELECT count(DISTINCT doc_id) FROM llc_implementing_act
        WHERE derived_status = 'superseded'
    """).fetchone()[0]
    log(f"  -> {sup} of them are provably superseded by a later act")

    log("\nrepealed company-form articles still cited by acts in the corpus:")
    for art, n, acts in con.execute(f"""
        SELECT dst_article_number, count(*), count(DISTINCT src_doc_id)
        FROM link_edge
        WHERE dst_dangling AND dst_article_number IN ({','.join('?' * len(REPEALED_COMPANY_ARTICLES))})
        GROUP BY 1 ORDER BY CAST(dst_article_number AS INT)
    """, REPEALED_COMPANY_ARTICLES).fetchall():
        log(f"  art {art}: {n} citations from {acts} acts")
    con.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
