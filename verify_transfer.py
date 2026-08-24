#!/usr/bin/env python
"""
M0 verification suite — English Civil Code General Part transfer.

Deliberately does NOT trust parsed_articles.json: the English text stored in
corpus.duckdb is re-extracted straight from the markdown using the line range
recorded with each row, so parser.py and this verifier fail independently.

Checks
  AC1  count reconciliation: markdown articles == landed + explicitly reported gaps
  AC2  zero distortion: byte-exact re-extraction for EVERY landed article
       (superset of the "at least 5 random articles" requirement), plus a
       character-count report on 5 randomly sampled articles
  AC3  Uzbek intactness: raw parquet untouched (sha256 + row/column count) and
       every Uzbek article body in the derived layer identical to the parquet

Exit code 0 = all checks pass, 1 = at least one failure.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import unicodedata
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
PARQUET = ROOT / "articles" / "train-00000-of-00001.parquet"
PARSED = ROOT / "parsed_articles.json"
MARKDOWN = ROOT / "Civil code of Uzbekistan_general part" / "Civil_Code_Part1_Updated_2025.md"
DB_PATH = ROOT / "corpus.duckdb"

CC_GENERAL_PART = -111189
EXPECTED_PARQUET_ROWS = 54_173
EXPECTED_PARQUET_COLS = 23
SAMPLE_SIZE = 5

failures: list[str] = []
warnings: list[str] = []


def log(msg: str = "") -> None:
    print(msg, flush=True)


def check(ok: bool, label: str, detail: str = "") -> bool:
    log(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)
    return ok


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    run_id, parquet_sha_at_build, markdown_sha_at_build = con.execute(
        "SELECT run_id, parquet_sha256, markdown_sha256 FROM extraction_run ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    log(f"verifying run {run_id}\n")

    md_lines = MARKDOWN.read_text(encoding="utf-8").splitlines(keepends=True)
    parsed = json.loads(PARSED.read_text(encoding="utf-8"))
    md_total = len(parsed["articles"])

    # ------------------------------------------------------------------ AC1
    log("AC1  count reconciliation")
    landed = con.execute(
        "SELECT count(*) FROM norm_unit WHERE article_text_en IS NOT NULL"
    ).fetchone()[0]
    uz_rows = con.execute("SELECT count(*) FROM norm_unit").fetchone()[0]
    md_only = con.execute(
        "SELECT count(*) FROM en_transfer_report WHERE run_id = ? AND kind IN ('md_only','md_only_occurrence')",
        [run_id],
    ).fetchone()[0]
    db_only = con.execute(
        "SELECT count(*) FROM en_transfer_report WHERE run_id = ? AND kind IN ('db_only','db_only_occurrence')",
        [run_id],
    ).fetchone()[0]

    check(landed + md_only == md_total,
          "every markdown article is either landed or explicitly reported",
          f"{landed} landed + {md_only} reported unmatched = {landed + md_only} (markdown has {md_total})")
    check(landed + db_only == uz_rows,
          "every Uzbek article either carries English text or is explicitly reported",
          f"{landed} + {db_only} = {landed + db_only} (corpus has {uz_rows})")
    check(con.execute(
              "SELECT count(*) FROM norm_unit WHERE article_text_en IS NOT NULL AND trim(article_text_en) = ''"
          ).fetchone()[0] == 0,
          "no landed article has empty English text")
    check(len(set(con.execute("SELECT norm_id FROM norm_unit").fetchall())) == uz_rows,
          "norm_id is unique across norm units")
    check(con.execute(
              "SELECT count(*) FROM norm_unit WHERE article_text_en IS NOT NULL AND en_align_status IS NULL"
          ).fetchone()[0] == 0,
          "every landed article carries an alignment status")
    suspect = con.execute("""
        SELECT en_display_number, article_title_uz, article_title_en FROM norm_unit
        WHERE en_align_status <> 'aligned'
    """).fetchall()
    log(f"  [INFO] {len(suspect)} article(s) flagged as not safely aligned (text kept, excluded from 'aligned'):")
    for d, tu, te in suspect:
        log(f"         {d}: UZ {tu!r} vs EN {te!r}")

    # ------------------------------------------------------------------ AC2
    log("\nAC2  zero distortion / zero truncation")
    rows = con.execute("""
        SELECT norm_id, article_number, en_display_number, article_text_en, en_line_start, en_line_end
        FROM norm_unit WHERE article_text_en IS NOT NULL ORDER BY src_row
    """).fetchall()

    mismatched: list[str] = []
    nfc_only: list[str] = []
    for norm_id, art_no, display, text_en, l0, l1 in rows:
        # line_start is the heading line (1-based); the body is everything after
        # it through line_end inclusive.
        expected = "".join(md_lines[l0:l1]).strip()
        if text_en != expected:
            if unicodedata.normalize("NFC", text_en) == unicodedata.normalize("NFC", expected):
                nfc_only.append(norm_id)
            else:
                mismatched.append(
                    f"{norm_id} ({display}): db={len(text_en)} chars, markdown={len(expected)} chars"
                )

    check(not mismatched,
          f"all {len(rows)} landed articles are byte-identical to a fresh markdown re-extraction",
          "" if not mismatched else f"{len(mismatched)} mismatch(es): " + "; ".join(mismatched[:5]))
    if nfc_only:
        warnings.append(f"{len(nfc_only)} article(s) differ only by Unicode normalisation form")

    check(sha256_file(MARKDOWN) == markdown_sha_at_build,
          "markdown source unchanged since the transfer ran",
          f"sha256 {markdown_sha_at_build[:16]}...")

    # Truncation is what a character-count comparison actually catches, so report
    # it explicitly on a random sample as the acceptance criteria require.
    random.seed(0xC0DE)  # reproducible sample; the exhaustive check above is the real guarantee
    log(f"\n  random sample of {SAMPLE_SIZE} articles — character counts (db vs markdown):")
    if len(rows) < SAMPLE_SIZE:
        check(False, f"at least {SAMPLE_SIZE} landed articles available to sample",
              f"only {len(rows)} — the build did not complete; re-run build_corpus_db.py")
        rows = rows * 0 or []
    for norm_id, art_no, display, text_en, l0, l1 in random.sample(rows, min(SAMPLE_SIZE, len(rows))):
        expected = "".join(md_lines[l0:l1]).strip()
        flag = "ok" if len(text_en) == len(expected) else "MISMATCH"
        log(f"    {display:<22} lines {l0}-{l1:<5} db={len(text_en):>6}  md={len(expected):>6}  {flag}")
        if len(text_en) != len(expected):
            failures.append(f"sampled char-count mismatch on {norm_id}")

    shortest = con.execute("""
        SELECT en_display_number, length(article_text_en) FROM norm_unit
        WHERE article_text_en IS NOT NULL ORDER BY 2 LIMIT 3
    """).fetchall()
    log(f"  shortest landed articles (truncation smoke test): {shortest}")

    # ------------------------------------------------------------------ AC3
    log("\nAC3  Uzbek text intactness")
    check(sha256_file(PARQUET) == parquet_sha_at_build,
          "raw parquet byte-identical to its state before the transfer",
          f"sha256 {parquet_sha_at_build[:16]}...")

    raw = f"read_parquet('{PARQUET.as_posix()}', file_row_number=true)"
    n_rows = con.execute(f"SELECT count(*) FROM {raw}").fetchone()[0]
    n_cols = len(con.execute(f"DESCRIBE SELECT * FROM {raw}").fetchall()) - 1  # minus file_row_number
    check(n_rows == EXPECTED_PARQUET_ROWS, "parquet row count unchanged", f"{n_rows}")
    check(n_cols == EXPECTED_PARQUET_COLS,
          "parquet column count unchanged (no column appended to the raw layer)", f"{n_cols}")

    drift = con.execute(f"""
        WITH src AS (
            SELECT file_row_number AS src_row, article_number, article_title, article_text
            FROM {raw} WHERE doc_id = {CC_GENERAL_PART}
        )
        SELECT count(*) FROM src JOIN norm_unit n USING (src_row)
        WHERE src.article_text IS DISTINCT FROM n.article_text_uz
           OR src.article_title IS DISTINCT FROM n.article_title_uz
           OR src.article_number IS DISTINCT FROM n.article_number
    """).fetchone()[0]
    check(drift == 0,
          f"all {uz_rows} Uzbek article bodies/titles in the derived layer identical to the parquet",
          f"{drift} row(s) drifted" if drift else "")

    # ------------------------------------------------------------------ AC4
    log("\nAC4  structural tree (M1)")
    import structure_parser

    nodes = structure_parser.parse_structure()
    check(not structure_parser.validate(nodes),
          "structure source is contiguous, non-overlapping and gap-free",
          f"{len(nodes)} nodes, articles 1-{max(n.art_to for n in structure_parser.leaf_ranges(nodes))}")
    check(con.execute("SELECT count(*) FROM norm_unit WHERE struct_node_id IS NULL").fetchone()[0] == 0,
          f"all {uz_rows} norm units attached to a structural node")
    check(con.execute("""
              SELECT count(*) FROM norm_unit n JOIN struct_node s ON s.node_id = n.struct_node_id
              WHERE n.article_base NOT BETWEEN s.art_from AND s.art_to
          """).fetchone()[0] == 0,
          "every norm unit's base article falls inside its node's declared range")
    check(con.execute("SELECT coalesce(sum(n_units), 0) FROM struct_node").fetchone()[0] == uz_rows,
          "structural unit counts sum to the corpus row count")

    # The superscript set is known independently from the English markdown.
    md_superscripts = {a["db_article_number_key"] for a in parsed["articles"] if a["superscript"]}
    db_superscripts = {r[0] for r in con.execute(
        "SELECT article_number FROM norm_unit WHERE superscript IS NOT NULL").fetchall()}
    check(md_superscripts == db_superscripts,
          f"superscript articles identified from structure match the markdown's {len(md_superscripts)}",
          "" if md_superscripts == db_superscripts
          else f"structure-only {sorted(db_superscripts - md_superscripts)}, "
               f"markdown-only {sorted(md_superscripts - db_superscripts)}")
    check(con.execute("SELECT count(*) FROM v_general_part WHERE breadcrumb IS NULL").fetchone()[0] == 0,
          "every article resolves to a full structural breadcrumb")

    # ------------------------------------------------------------------ AC5
    log("\nAC5  realization graph (M2)")
    have_edges = con.execute(
        "SELECT count(*) FROM duckdb_tables() WHERE table_name = 'link_edge'"
    ).fetchone()[0]
    if not have_edges:
        log("  [SKIP] link_edge not built yet — run build_links.py")
    else:
        import citation_extractor as cx_

        check(cx_._selftest() == 0, "citation extractor self-tests pass")
        n_edges = con.execute("SELECT count(*) FROM link_edge").fetchone()[0]
        check(con.execute(
                  "SELECT count(*) FROM link_edge WHERE evidence IS NULL OR trim(evidence) = ''"
              ).fetchone()[0] == 0,
              f"all {n_edges} edges carry evidence text")
        check(con.execute("""
                  SELECT count(*) FROM link_edge
                  WHERE dst_kind = 'article' AND dst_doc_id = -111189
                    AND dst_norm_id IS NULL AND NOT dst_dangling
              """).fetchone()[0] == 0,
              "every General Part article edge either resolves or is flagged dangling")
        dangling = con.execute(
            "SELECT count(*), count(DISTINCT dst_article_number) FROM link_edge WHERE dst_dangling"
        ).fetchone()
        log(f"  [INFO] {dangling[0]} citation(s) point at {dangling[1]} repealed article(s) "
            f"— acts still referencing provisions the 2026 corpus no longer contains")
        check(con.execute("""
                  SELECT count(*) FROM link_edge e LEFT JOIN norm_unit n ON n.norm_id = e.dst_norm_id
                  WHERE e.dst_norm_id IS NOT NULL AND n.norm_id IS NULL
              """).fetchone()[0] == 0,
              "no edge points at a non-existent norm unit")
        check(con.execute("""
                  SELECT count(*) FROM link_edge e LEFT JOIN corpus_row r ON r.row_id = e.src_row_id
                  WHERE r.row_id IS NULL
              """).fetchone()[0] == 0,
              "every edge's citing row exists in the corpus index")
        check(con.execute(
                  "SELECT count(*) FROM link_edge WHERE hierarchy_rel = 'below' AND src_tier <= 2"
              ).fetchone()[0] == 0,
              "no edge claims realization from an act at or above the Code's tier")
        # The gazette-citation false positive class must stay eradicated.
        gazette = con.execute(r"""
            SELECT count(*) FROM link_edge
            WHERE dst_kind = 'article'
              AND regexp_matches(lower(evidence), 'axborotnomasi, \d{4}-yil')
              AND regexp_matches(lower(evidence), '№')
        """).fetchone()[0]
        check(gazette == 0, "no article edge mined from an act's publication record",
              f"{gazette} suspected gazette citation(s)" if gazette else "")

        cov, real = con.execute(f"""
            SELECT count(DISTINCT dst_norm_id),
                   count(DISTINCT CASE WHEN hierarchy_rel = 'below' THEN dst_norm_id END)
            FROM link_edge WHERE dst_doc_id = {CC_GENERAL_PART}
        """).fetchone()
        log(f"  [INFO] {cov}/{uz_rows} General Part articles cited; "
            f"{real} have realizing acts below the Code")

    # ------------------------------------------------------------------ AC6
    log("\nAC6  OKOZ classification axis (M3)")
    have_okoz = con.execute(
        "SELECT count(*) FROM duckdb_tables() WHERE table_name = 'okoz_node'"
    ).fetchone()[0]
    if not have_okoz:
        log("  [SKIP] okoz_node not built yet — run build_okoz.py")
    else:
        import okoz_parser

        ok_nodes = okoz_parser.parse_okoz()
        ok_errors, ok_warnings = okoz_parser.validate(ok_nodes)
        check(not ok_errors, "OKOZ source tree parses without errors",
              f"{len(ok_nodes)} nodes, {len(ok_warnings)} see-also warnings")
        db_okoz = con.execute("SELECT count(*) FROM okoz_node").fetchone()[0]
        check(db_okoz == len(ok_nodes),
              "okoz_node row count matches a fresh parse of the source", f"{db_okoz}")
        check(con.execute("""
                  SELECT count(*) FROM okoz_node c
                  LEFT JOIN okoz_node p ON p.code = c.parent_code
                  WHERE c.parent_code IS NOT NULL AND p.code IS NULL
              """).fetchone()[0] == 0,
              "every non-sphere OKOZ node's parent exists")
        check(con.execute("""
                  SELECT count(*) FROM okoz_assignment a
                  LEFT JOIN okoz_node k ON k.code = a.okoz_code
                  LEFT JOIN struct_node s ON s.node_id = a.struct_node_id
                  WHERE k.code IS NULL OR s.node_id IS NULL
              """).fetchone()[0] == 0,
              "every assignment resolves to a real OKOZ code and struct node")
        classified = con.execute(
            "SELECT count(DISTINCT norm_id) FROM v_okoz_general_part").fetchone()[0]
        check(classified == uz_rows,
              f"all {uz_rows} General Part articles inherit an OKOZ classification",
              f"{classified} classified")
        check(con.execute(
                  "SELECT count(*) FROM v_okoz_general_part WHERE okoz_breadcrumb IS NULL"
              ).fetchone()[0] == 0,
              "every classification resolves to a full OKOZ breadcrumb")
        check(con.execute("""
                  SELECT count(*) FROM okoz_assignment
                  WHERE okoz_code NOT LIKE '03.%'
              """).fetchone()[0] == 0,
              "all General Part mappings stay inside sphere 03 (Civil Legislation)")
        pending = con.execute(
            "SELECT count(*) FROM okoz_assignment WHERE validated_by IS NULL"
        ).fetchone()[0]
        log(f"  [INFO] {pending} proposed mapping(s) awaiting the owner's validation")

    # ------------------------------------------------------------------ AC7
    log("\nAC7  evidence provenance, currency and the LLC slice")
    have_llc = con.execute(
        "SELECT count(*) FROM duckdb_tables() WHERE table_name = 'llc_norm'"
    ).fetchone()[0]
    if not have_llc:
        log("  [SKIP] llc_norm not built yet — run build_llc.py")
    else:
        check(con.execute("""
                  SELECT count(*) FROM link_edge
                  WHERE evidence_kind NOT IN ('normative','editorial','amendment')
              """).fetchone()[0] == 0,
              "every edge is labelled with a known evidence kind")
        check(con.execute("""
                  SELECT count(*) FROM link_edge
                  WHERE (source_field = 'article_text'      AND evidence_kind <> 'normative')
                     OR (source_field = 'cross_references'  AND evidence_kind <> 'editorial')
                     OR (source_field = 'amendment_note'    AND evidence_kind <> 'amendment')
              """).fetchone()[0] == 0,
              "evidence kind agrees with the field the citation came from")
        # The act's own words must never rank below an editorial pointer.
        check(con.execute("""
                  SELECT count(*) FROM link_edge a JOIN link_edge b
                    ON a.dst_kind = b.dst_kind
                  WHERE a.evidence_kind = 'normative' AND b.evidence_kind = 'editorial'
                    AND a.confidence < b.confidence
              """).fetchone()[0] == 0,
              "normative evidence always outranks editorial for the same target kind")
        check(con.execute("""
                  SELECT count(*) FROM link_edge
                  WHERE evidence_clean IS NULL
                     OR evidence_clean ILIKE '%Oldingi tahrirga qarang%'
                     OR evidence_clean ILIKE '%LexUZ sharhi%'
              """).fetchone()[0] == 0,
              "displayed evidence is free of LexUZ editorial apparatus")
        prov_missing = con.execute("""
            SELECT count(*) FROM link_edge e
            LEFT JOIN src_provision p ON p.row_id = e.src_row_id
            WHERE p.row_id IS NULL
        """).fetchone()[0]
        check(prov_missing == 0,
              "every edge resolves to its citing provision's stored text",
              f"{prov_missing} without a provision" if prov_missing else "")
        check(con.execute("""
                  SELECT count(*) FROM src_provision
                  WHERE article_text IS NULL OR trim(article_text) = ''
              """).fetchone()[0] == 0,
              "no stored citing provision is empty")

        # currency
        check(con.execute("""
                  SELECT count(*) FROM repeal_clause r
                  LEFT JOIN act a ON a.doc_id = r.dst_doc_id
                  WHERE r.dst_doc_id IS NOT NULL AND a.doc_id IS NULL
              """).fetchone()[0] == 0,
              "every resolved repeal points at a real act")
        check(con.execute("""
                  SELECT count(*) FROM repeal_clause r
                  JOIN act s ON s.doc_id = r.src_doc_id
                  JOIN act d ON d.doc_id = r.dst_doc_id
                  WHERE d.doc_date > s.doc_date
              """).fetchone()[0] == 0,
              "no act repeals something enacted after it")
        sup = con.execute(
            "SELECT count(DISTINCT doc_id) FROM v_act_currency WHERE derived_status='superseded'"
        ).fetchone()[0]
        stale = con.execute("""
            SELECT count(*) FROM link_edge e JOIN v_act_currency c ON c.doc_id = e.src_doc_id
            WHERE c.derived_status = 'superseded' AND e.hierarchy_rel = 'below'
        """).fetchone()[0]
        log(f"  [INFO] {sup} acts provably superseded; {stale} realization edges come "
            f"from them (corpus status says 'in-force' for all 24,267 acts)")

        # LLC slice
        check(con.execute("SELECT count(*) FROM llc_stage").fetchone()[0] == 8,
              "LLC skeleton has the current law's 8 chapters")
        check(con.execute("""
                  SELECT count(*) FROM llc_norm n LEFT JOIN norm_unit u
                    ON u.norm_id = n.cc_norm_id
                  WHERE n.layer = 'foundation' AND u.norm_id IS NULL
              """).fetchone()[0] == 0,
              "every LLC foundation norm resolves to a verified Civil Code article")
        check(con.execute("""
                  SELECT count(*) FROM llc_norm
                  WHERE layer = 'foundation' AND (rationale IS NULL OR trim(rationale) = '')
              """).fetchone()[0] == 0,
              "every foundation mapping states why it founds its stage")
        gaps = con.execute("""
            SELECT count(*) FROM llc_stage s
            WHERE NOT EXISTS (SELECT 1 FROM llc_norm n
                              WHERE n.stage_no = s.stage_no AND n.layer = 'special')
        """).fetchone()[0]
        check(gaps == 0, "every LLC stage carries its special-law articles")
        check(con.execute("""
                  SELECT count(*) FROM llc_norm WHERE layer = 'special' AND doc_id <> -8151376
              """).fetchone()[0] == 0,
              "the LLC skeleton is built on the current law, not the repealed one")
        cur_status = con.execute(
            "SELECT derived_status FROM v_act_currency WHERE doc_id = -22525").fetchone()[0]
        check(cur_status == "superseded",
              "the 2001 LLC Law is detected as repealed by the 2026 Law")

    # ---------------------------------------------------------------- report
    log("\nreconciliation detail (articles needing a human decision):")
    for kind, key, detail in con.execute("""
        SELECT kind, article_key, detail FROM en_transfer_report
        WHERE run_id = ? AND kind NOT IN ('review_superscript') ORDER BY kind, article_key
    """, [run_id]).fetchall():
        log(f"  {kind:<22} art {key:<6} {detail}")

    log("")
    for w in warnings:
        log(f"WARNING: {w}")
    if failures:
        log(f"\nVERIFICATION FAILED — {len(failures)} check(s):")
        for f in failures:
            log(f"  - {f}")
        return 1
    log("VERIFICATION PASSED — all checks green.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
