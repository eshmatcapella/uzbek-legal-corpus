#!/usr/bin/env python
"""
M0 — Build the derived DuckDB layer and land the English General Part text.

Design rules (see also the hierarchy plan):
  * The parquet at articles/ is the RAW layer and is never written to.
  * corpus.duckdb is the DERIVED layer. It can always be rebuilt from
    (parquet + Civil_Code_Part1_Updated_2025.md) by re-running this script.
  * Every derived value carries provenance: which run produced it, from which
    source line range, and by which alignment method.

Scope of M0: `act` for every act in the corpus, `norm_unit` for the Civil Code
General Part (doc_id = -111189) with the Uzbek text carried over verbatim and
the English text aligned onto it.  Structure (M1), links (M2) and OKOZ (M3)
tables are intentionally not created here.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

import structure_parser

ROOT = Path(__file__).resolve().parent
PARQUET = ROOT / "articles" / "train-00000-of-00001.parquet"
PARSED = ROOT / "parsed_articles.json"
MARKDOWN = ROOT / "Civil code of Uzbekistan_general part" / "Civil_Code_Part1_Updated_2025.md"
DB_PATH = ROOT / "corpus.duckdb"

CC_GENERAL_PART = -111189

# Kelsenian tier of each act type. Lower number = higher in the pyramid.
# Alignment decisions taken after reading both texts side by side.  Keyed by
# norm_id.  The corpus is pinned at version_date 2026-06-29 while the English
# markdown is a 2025 state, so a shared article number does not guarantee a
# shared norm.  Anything listed here keeps its English text (nothing is thrown
# away) but is marked so the UI and any downstream training use can exclude it.
ALIGNMENT_OVERRIDES = {
    "-111189-a261#1": (
        "suspect_version_drift",
        "Article 26-super-1: Uzbek is 'Jismoniy shaxsning to'lovga qobiliyatsizligi' (insolvency of a "
        "natural person); English is 'Insolvency estate' (the konkurs massa of an individual "
        "entrepreneur). Different norms — the 2025 English text predates the current article. "
        "Verified by reading both bodies on 2026-08-12. The other 9 superscript articles "
        "(173-1..173-7, 259-1, 358-1) and Article 26 itself were checked and align correctly.",
    ),
}

TIER = {
    "constitution": 1,
    "code": 2,
    "law": 3,
    "decree": 4,
    "resolution": 5,
    "order": 6,
    "other": 9,
}


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE OR REPLACE TABLE extraction_run (
            run_id        VARCHAR PRIMARY KEY,
            started_at    TIMESTAMPTZ,
            script        VARCHAR,
            parquet_sha256 VARCHAR,
            markdown_sha256 VARCHAR,
            notes         VARCHAR
        );

        CREATE OR REPLACE TABLE act (
            doc_id        BIGINT PRIMARY KEY,
            act_group_id  VARCHAR,
            doc_title     VARCHAR,
            doc_type      VARCHAR,
            tier          INTEGER,
            doc_number    VARCHAR,
            doc_date      VARCHAR,
            version_date  VARCHAR,
            status        VARCHAR,
            source_url    VARCHAR,
            n_articles    BIGINT,
            tier_note     VARCHAR
        );

        -- Article-level norm unit: the grain every hierarchy edge attaches to.
        CREATE OR REPLACE TABLE norm_unit (
            norm_id           VARCHAR PRIMARY KEY,
            doc_id            BIGINT,
            src_row           BIGINT,      -- position in the raw parquet, document order
            part_raw          VARCHAR,     -- as-is from the corpus (known mangled, fixed in M1)
            chapter_raw       VARCHAR,     -- empty for the Civil Code; rebuilt in M1
            article_number    VARCHAR,
            occurrence        INTEGER,     -- disambiguates a repeated article_number (e.g. 26-super-1 vs 261)
            article_base      INTEGER,     -- 173 for Article 173-super-4
            superscript       INTEGER,     -- 4 for Article 173-super-4, NULL otherwise
            struct_node_id    VARCHAR,     -- deepest structural node containing this article
            article_title_uz  VARCHAR,
            article_text_uz   VARCHAR,
            n_tokens_uz       BIGINT,
            okoz_codes_doc    VARCHAR[],   -- document-level codes from the corpus (sphere granularity only)
            -- English side, landed by M0
            article_title_en  VARCHAR,
            article_text_en   VARCHAR,
            en_display_number VARCHAR,     -- e.g. "Article 26<sup>1</sup>" as written in the markdown
            en_heading_type   VARCHAR,
            en_titleless      BOOLEAN,
            en_repealed       BOOLEAN,
            en_line_start     INTEGER,
            en_line_end       INTEGER,
            en_align_method   VARCHAR,     -- 'exact_key' | 'positional_within_key'
            en_align_status   VARCHAR,     -- 'aligned' | 'suspect_version_drift' | NULL if no English
            en_align_note     VARCHAR,
            en_run_id         VARCHAR
        );

        -- Stable handle on every article row in the raw corpus.  The corpus's own
        -- `id` cannot serve: 54,173 rows carry only 52,886 distinct ids.
        CREATE OR REPLACE TABLE corpus_row (
            row_id         BIGINT PRIMARY KEY,   -- position in the parquet, document order
            corpus_id      VARCHAR,              -- the corpus's own (non-unique) id
            doc_id         BIGINT,
            doc_type       VARCHAR,
            tier           INTEGER,
            article_number VARCHAR
        );

        -- The Code's internal structure: part > subsection > chapter > section.
        -- Rebuilt from structure/civil_code_structure.md because the corpus's own
        -- `chapter` is empty for the whole Code and `part` is mangled.
        CREATE OR REPLACE TABLE struct_node (
            node_id     VARCHAR PRIMARY KEY,
            kind        VARCHAR,     -- part | subsection | chapter | section
            number      VARCHAR,
            label_en    VARCHAR,
            parent_id   VARCHAR,
            ordinal     INTEGER,
            depth       INTEGER,
            art_from    INTEGER,     -- NULL on nodes that delegate to children
            art_to      INTEGER,
            doc_id      BIGINT,
            n_units     INTEGER      -- norm units actually present in the corpus
        );

        -- Reconciliation of every article on either side that did NOT land cleanly.
        CREATE OR REPLACE TABLE en_transfer_report (
            run_id       VARCHAR,
            kind         VARCHAR,
            article_key  VARCHAR,
            detail       VARCHAR
        );
    """)


def load_markdown_articles() -> list[dict]:
    data = json.loads(PARSED.read_text(encoding="utf-8"))
    return data["articles"]


def main() -> int:
    for p in (PARQUET, PARSED, MARKDOWN):
        if not p.exists():
            log(f"FATAL: missing input {p}")
            return 1

    run_id = datetime.now(timezone.utc).strftime("m0-%Y%m%dT%H%M%SZ")
    log(f"run_id = {run_id}")
    log("hashing inputs (the parquet is read-only for the whole pipeline)...")
    parquet_sha = sha256_file(PARQUET)
    markdown_sha = sha256_file(MARKDOWN)

    con = duckdb.connect(str(DB_PATH))
    create_schema(con)
    con.execute(
        "INSERT INTO extraction_run VALUES (?, ?, ?, ?, ?, ?)",
        [run_id, datetime.now(timezone.utc), "build_corpus_db.py", parquet_sha, markdown_sha,
         "M0: derived layer bootstrap + English General Part transfer"],
    )

    # file_row_number is the parquet's own physical row index: deterministic and
    # independent of scan parallelism, unlike row_number() OVER ().
    raw = f"read_parquet('{PARQUET.as_posix()}', file_row_number=true)"

    # ---------- act ----------
    con.execute(f"""
        INSERT INTO act
        SELECT
            doc_id,
            any_value(act_group_id),
            any_value(doc_title),
            any_value(doc_type),
            CASE any_value(doc_type)
                WHEN 'constitution' THEN 1 WHEN 'code' THEN 2 WHEN 'law' THEN 3
                WHEN 'decree' THEN 4 WHEN 'resolution' THEN 5 WHEN 'order' THEN 6
                ELSE 9 END,
            any_value(doc_number),
            any_value(doc_date),
            any_value(version_date),
            any_value(status),
            any_value(source_url),
            count(*),
            NULL
        FROM {raw}
        GROUP BY doc_id
    """)
    # The corpus's doc_type = 'constitution' is a catch-all: of 113 such acts only a
    # handful are actually a constitution, the rest are Constitutional Court
    # decisions, amendment laws and even Cabinet resolutions.  Leaving them all at
    # tier 1 would put them above the Civil Code in the realization graph, which is
    # wrong for most.  Only an act whose title IS a constitution keeps tier 1; the
    # remainder drop to 'unclassified' with the reason recorded.
    con.execute(r"""
        UPDATE act SET tier = 9, tier_note = CASE
            WHEN regexp_matches(lower(doc_title), 'konstitutsiyaviy sud')
                THEN 'Constitutional Court decision — outside the Kelsen tier line'
            ELSE 'corpus doc_type=constitution is a catch-all; real act type unknown'
            END
        WHERE doc_type = 'constitution'
          AND NOT regexp_matches(lower(doc_title), '^[«"“]?(oʻzbekiston respublikasi|qoraqalpogʻiston respublikasi)?[^.]{0,40}konstitutsiyasi')
    """)
    n_acts = con.execute("SELECT count(*) FROM act").fetchone()[0]
    kept = con.execute("SELECT count(*) FROM act WHERE tier = 1").fetchone()[0]
    log(f"act: {n_acts} acts loaded ({kept} retained at tier 1 = constitution proper)")

    # ---------- corpus_row ----------
    # row_id is the parquet's own row order, which is stable for a given file;
    # the file's sha256 is recorded in extraction_run so drift is detectable.
    con.execute(f"""
        INSERT INTO corpus_row
        SELECT r.file_row_number, r.id, r.doc_id, r.doc_type, a.tier, r.article_number
        FROM {raw} r JOIN act a ON a.doc_id = r.doc_id
    """)
    log(f"corpus_row: {con.execute('SELECT count(*) FROM corpus_row').fetchone()[0]} rows indexed")

    # ---------- norm_unit (Uzbek side) ----------
    # `id` is NOT unique in the corpus (54,173 rows / 52,886 distinct ids), and
    # article_number repeats within this act ('261' = both Article 26-super-1 and
    # Article 261).  So the key is (article_number, occurrence) where occurrence
    # follows document order, and src_row preserves that order explicitly.
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE uz AS
        SELECT file_row_number AS src_row, *
        FROM {raw}
        WHERE doc_id = {CC_GENERAL_PART}
    """)
    con.execute("""
        INSERT INTO norm_unit (
            norm_id, doc_id, src_row, part_raw, chapter_raw, article_number, occurrence,
            article_title_uz, article_text_uz, n_tokens_uz, okoz_codes_doc
        )
        SELECT
            CASE WHEN occ_total > 1
                 THEN doc_id || '-a' || article_number || '#' || occurrence
                 ELSE doc_id || '-a' || article_number END,
            doc_id, src_row, part, chapter, article_number, occurrence,
            article_title, article_text, n_tokens, okoz_codes
        FROM (
            SELECT *,
                   row_number() OVER (PARTITION BY article_number ORDER BY src_row) AS occurrence,
                   count(*)    OVER (PARTITION BY article_number)                   AS occ_total
            FROM uz
        )
    """)
    n_units = con.execute("SELECT count(*) FROM norm_unit").fetchone()[0]
    log(f"norm_unit: {n_units} Uzbek article rows loaded (doc_id={CC_GENERAL_PART})")

    # ---------- struct_node (M1) ----------
    nodes = structure_parser.parse_structure()
    problems = structure_parser.validate(nodes)
    if problems:
        log("FATAL: the structure source is internally inconsistent:")
        for p in problems:
            log(f"  - {p}")
        return 1
    con.executemany(
        "INSERT INTO struct_node (node_id, kind, number, label_en, parent_id, ordinal, depth, "
        "art_from, art_to, doc_id, n_units) VALUES (?,?,?,?,?,?,?,?,?,?,0)",
        [[n.node_id, n.kind, n.number, n.label_en, n.parent_id, n.ordinal, n.depth,
          n.art_from, n.art_to, n.doc_id] for n in nodes],
    )
    art_index = structure_parser.build_article_index(nodes)
    log(f"struct_node: {len(nodes)} nodes covering articles 1-{max(art_index)}")

    # ---------- attach norm units to the structure ----------
    # Superscript articles are concatenated upstream (Article 173-super-4 -> '1734'),
    # and '261' is ambiguous: it is Article 26-super-1 in Part I and Article 261 in
    # Part III.  Resolution uses the part the row sits in plus document order: a
    # number outside its own part's range cannot be a base article, so it must be a
    # superscript of the article before it.
    by_id = {n.node_id: n for n in nodes}

    def root_part(node: structure_parser.Node) -> structure_parser.Node:
        while node.parent_id:
            node = by_id[node.parent_id]
        return node

    part_range: dict[str, tuple[int, int]] = {}
    for leaf in structure_parser.leaf_ranges(nodes):
        key = root_part(leaf).number
        lo, hi = part_range.get(key, (leaf.art_from, leaf.art_to))
        part_range[key] = (min(lo, leaf.art_from), max(hi, leaf.art_to))

    rows = con.execute(
        "SELECT norm_id, article_number, part_raw FROM norm_unit ORDER BY src_row"
    ).fetchall()
    assignments: list[list] = []
    report_unresolved: list[list] = []
    current_base = 0
    GENERAL_PART_LAST_ARTICLE = structure_parser.GENERAL_PART_LAST_ARTICLE
    for norm_id, art_no, part_raw in rows:
        m = re.match(r"\s*(I{1,3})\s*BO", part_raw or "")
        lo, hi = part_range.get(m.group(1) if m else "", (1, GENERAL_PART_LAST_ARTICLE))
        value = int(art_no)
        if lo <= value <= hi and value > current_base:
            base, sup = value, None
            current_base = value
        else:
            base = current_base
            tail = art_no[len(str(base)):] if art_no.startswith(str(base)) else ""
            sup = int(tail) if tail.isdigit() else None
            if sup is None:
                report_unresolved.append([norm_id, art_no, part_raw])
        node = art_index.get(base)
        assignments.append([base, sup, node.node_id if node else None, norm_id])

    con.executemany(
        "UPDATE norm_unit SET article_base = ?, superscript = ?, struct_node_id = ? WHERE norm_id = ?",
        assignments,
    )
    con.execute("""
        UPDATE struct_node s SET n_units = (
            SELECT count(*) FROM norm_unit n WHERE n.struct_node_id = s.node_id
        )
    """)
    unassigned = con.execute("SELECT count(*) FROM norm_unit WHERE struct_node_id IS NULL").fetchone()[0]
    log(f"structure: {len(rows) - unassigned}/{len(rows)} norm units attached, "
        f"{sum(1 for r in assignments if r[1] is not None)} identified as superscript articles")

    struct_report = [
        [run_id, "structure_unresolved_number", art_no,
         f"{norm_id} could not be resolved to a base article (part {part_raw!r})"]
        for norm_id, art_no, part_raw in report_unresolved
    ]
    # Articles the structure expects but the 2026 corpus no longer contains
    # (repealed since), reported per structural node rather than silently absent.
    for node_id, label, lo, hi, present in con.execute(f"""
        SELECT s.node_id, s.label_en, s.art_from, s.art_to, s.n_units
        FROM struct_node s
        WHERE s.art_from IS NOT NULL AND s.doc_id = {CC_GENERAL_PART}
        ORDER BY s.art_from
    """).fetchall():
        expected = hi - lo + 1
        if present < expected:
            missing = sorted(set(range(lo, hi + 1)) - set(
                r[0] for r in con.execute(
                    "SELECT DISTINCT article_base FROM norm_unit WHERE struct_node_id = ?", [node_id]
                ).fetchall()))
            if missing:
                struct_report.append([run_id, "structure_missing_articles", node_id,
                                      f"{label or node_id} (arts {lo}-{hi}): not in the corpus: "
                                      + ", ".join(map(str, missing))])
    con.executemany("INSERT INTO en_transfer_report VALUES (?, ?, ?, ?)", struct_report)

    # ---------- align the English side ----------
    md = load_markdown_articles()
    log(f"markdown: {len(md)} parsed English articles")

    md_by_key: dict[str, list[dict]] = {}
    for a in md:
        md_by_key.setdefault(a["db_article_number_key"], []).append(a)

    db_rows = con.execute(
        "SELECT norm_id, article_number, occurrence, part_raw, article_title_uz FROM norm_unit ORDER BY src_row"
    ).fetchall()
    db_by_key: dict[str, list[tuple]] = {}
    for row in db_rows:
        db_by_key.setdefault(row[1], []).append(row)

    updates: list[list] = []
    report: list[list] = []
    matched = 0

    for key, db_list in db_by_key.items():
        md_list = md_by_key.get(key, [])
        if not md_list:
            report.append([run_id, "db_only", key,
                           f"Uzbek article present in corpus, absent from the 2025 English markdown "
                           f"(title: {db_list[0][4]})"])
            continue
        # Both sides are in document order, so a repeated key pairs positionally.
        method = "exact_key" if len(db_list) == 1 and len(md_list) == 1 else "positional_within_key"
        for i, db_row in enumerate(db_list):
            if i >= len(md_list):
                report.append([run_id, "db_only_occurrence", key,
                               f"occurrence {db_row[2]} has no English counterpart"])
                continue
            a = md_list[i]
            status, note = ALIGNMENT_OVERRIDES.get(db_row[0], ("aligned", None))
            updates.append([
                a["title"] or None,
                a["clean_text"],
                a["article_number_display"],
                a["heading_type"],
                bool(a["titleless"]),
                bool(a["repealed"]),
                a["line_range"]["start_line"],
                a["line_range"]["end_line"],
                method,
                status,
                note,
                run_id,
                db_row[0],
            ])
            matched += 1
            if method == "positional_within_key":
                report.append([run_id, "review_ambiguous_key", key,
                               f"{a['article_number_display']} -> {db_row[0]} | EN: {a['title']!r} | "
                               f"UZ: {db_row[4]!r} | part: {db_row[3]!r}"])
        if len(md_list) > len(db_list):
            for a in md_list[len(db_list):]:
                report.append([run_id, "md_only_occurrence", key,
                               f"{a['article_number_display']} has no Uzbek counterpart"])

    for key, md_list in md_by_key.items():
        if key not in db_by_key:
            for a in md_list:
                report.append([run_id, "md_only", key,
                               f"{a['article_number_display']} ({a['title']!r}) present in the English markdown "
                               f"but absent from the corpus"
                               + (" — marked repealed in the markdown" if a["repealed"] else "")])

    con.executemany("""
        UPDATE norm_unit SET
            article_title_en = ?, article_text_en = ?, en_display_number = ?, en_heading_type = ?,
            en_titleless = ?, en_repealed = ?, en_line_start = ?, en_line_end = ?,
            en_align_method = ?, en_align_status = ?, en_align_note = ?, en_run_id = ?
        WHERE norm_id = ?
    """, updates)
    for norm_id, (status, note) in ALIGNMENT_OVERRIDES.items():
        report.append([run_id, status, norm_id, note])
    con.executemany("INSERT INTO en_transfer_report VALUES (?, ?, ?, ?)", report)

    # Flag superscript articles for expert eyeballing: numbering is concatenated
    # upstream (26-super-1 -> '261'), so these carry the highest mis-alignment risk.
    con.executemany("INSERT INTO en_transfer_report VALUES (?, ?, ?, ?)", [
        [run_id, "review_superscript", a["db_article_number_key"],
         f"{a['article_number_display']} | EN: {a['title']!r}"]
        for a in md if a["superscript"]
    ])

    # Convenience view: an article with its full structural breadcrumb, for the
    # Streamlit browser and for eyeballing joins during M2/M3.
    con.execute("""
        CREATE OR REPLACE VIEW v_general_part AS
        WITH RECURSIVE path(node_id, root_id, breadcrumb) AS (
            SELECT node_id, node_id, label_en FROM struct_node WHERE parent_id IS NULL
            UNION ALL
            SELECT s.node_id, p.root_id,
                   p.breadcrumb || ' > ' ||
                   CASE s.kind WHEN 'chapter' THEN 'Chapter ' || s.number || '. '
                               WHEN 'section' THEN '§ ' || s.number || '. '
                               WHEN 'subsection' THEN 'Subsection ' || s.number || '. '
                               ELSE '' END || s.label_en
            FROM struct_node s JOIN path p ON s.parent_id = p.node_id
        )
        SELECT
            n.norm_id, n.article_number, n.article_base, n.superscript,
            n.article_title_uz, n.article_title_en,
            n.article_text_uz, n.article_text_en,
            n.en_align_status,
            s.node_id AS struct_node_id, s.kind AS struct_kind, s.label_en AS struct_label,
            p.breadcrumb, n.src_row
        FROM norm_unit n
        LEFT JOIN struct_node s ON s.node_id = n.struct_node_id
        LEFT JOIN path p        ON p.node_id = n.struct_node_id
        ORDER BY n.src_row
    """)

    con.commit()

    landed = con.execute("SELECT count(*) FROM norm_unit WHERE article_text_en IS NOT NULL").fetchone()[0]
    log(f"aligned: {matched} pairs | non-null article_text_en: {landed}")
    log("\nreconciliation:")
    for kind, n in con.execute(
        "SELECT kind, count(*) FROM en_transfer_report WHERE run_id = ? GROUP BY 1 ORDER BY 2 DESC", [run_id]
    ).fetchall():
        log(f"  {kind:<24} {n}")

    log(f"\nwrote {DB_PATH}")
    log(f"raw parquet sha256 (unchanged by this script): {parquet_sha[:16]}...")
    con.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
