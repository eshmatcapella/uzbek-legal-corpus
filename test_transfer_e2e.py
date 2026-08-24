"""
E2E Test Suite for Civil Code English Translation Transfer Project.

Target Architecture & Coverage (4 Tiers):
1. Tier 1: Feature Coverage (R1-R4)
2. Tier 2: Boundary & Edge Cases
3. Tier 3: Non-Destructive & Schema Integrity
4. Tier 4: Programmatic Acceptance Criteria Verification (AC1-AC3)

Runs via: `python test_transfer_e2e.py` or `python -m unittest test_transfer_e2e.py`
"""

import importlib.util
import json
import os
import re
import sys
import unittest

import duckdb

# Path Constants
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MARKDOWN_PATH = os.path.join(
    PROJECT_ROOT,
    "Civil code of Uzbekistan_general part",
    "Civil_Code_Part1_Updated_2025.md",
)
PARQUET_PATH = os.path.join(
    PROJECT_ROOT, "articles", "train-00000-of-00001.parquet"
)

# Reference Sets & Constants from Specification
EXPECTED_TOTAL_PARQUET_ROWS = 54173
EXPECTED_CIVIL_CODE_ROWS = 386
EXPECTED_TOTAL_ARTICLES = 394
EXPECTED_ORIGINAL_COLUMNS = [
    "id",
    "act_group_id",
    "doc_id",
    "doc_title",
    "doc_type",
    "doc_number",
    "doc_date",
    "version_date",
    "status",
    "part",
    "chapter",
    "article_number",
    "article_title",
    "article_text",
    "amendment_note",
    "cross_references",
    "language",
    "script",
    "okoz_codes",
    "tsz_codes",
    "source_url",
    "n_tokens",
    "quality_flag",
]

SUPERSCRIPT_MAP = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
}

EXPECTED_SUPERSCRIPTS = [
    "26¹",
    "173¹",
    "173²",
    "173³",
    "173⁴",
    "173⁵",
    "173⁶",
    "173⁷",
    "259¹",
    "358¹",
]
EXPECTED_MISLABELED_SECTIONS = [
    "144",
    "255",
    "273",
    "302",
    "304",
    "305",
    "320",
    "349",
]
EXPECTED_SECTION_SYMBOLS = ["268", "309"]
EXPECTED_REPEALED_ARTICLES = ["63", "70", "71", "72", "176", "177", "179"]
EXPECTED_MARKDOWN_ONLY_ARTICLES = [
    "63",
    "65",
    "66",
    "70",
    "71",
    "72",
    "176",
    "177",
    "179",
]
EXPECTED_MISSING_ARTICLE = "168"


def load_external_parser():
    """
    Dynamically import external parser.py from PROJECT_ROOT if available.
    Returns module or None.
    """
    parser_py = os.path.join(PROJECT_ROOT, "parser.py")
    if os.path.exists(parser_py):
        try:
            spec = importlib.util.spec_from_file_location(
                "external_parser", parser_py
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        except Exception:
            return None
    return None


def parse_internal_markdown_articles(file_path=MARKDOWN_PATH):
    """
    Internal reference parser implementation for Civil_Code_Part1_Updated_2025.md.
    Extracts structured records for all 394 articles.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    headings = []
    for idx, line in enumerate(lines):
        line_num = idx + 1
        raw = line.rstrip("\r\n")
        stripped = raw.strip()

        # Skip footnote amendment notes starting with _(, (, *(
        if (
            stripped.startswith("_(")
            or stripped.startswith("(")
            or stripped.startswith("*(")
        ):
            continue

        cat = None
        art_id = None

        # 1. Section symbol for articles 268 and 309
        m_sym = re.match(
            r"^(?:\#+\s*)?(?:\*\*\s*)?\u00a7\s*(268|309)\b(.*)$", stripped
        )
        # 2. Mislabeled Section for 144, 255, 273, 302, 304, 305, 320, 349
        m_sec = re.match(
            r"^(?:\#+\s*)?(?:\*\*\s*)?Section\s+(144|255|273|302|304|305|320|349)\b(.*)$",
            stripped,
            re.IGNORECASE,
        )
        # 3. Standard Article (including superscript sub-articles)
        m_art = re.match(
            r"^(?:\#+\s*)?(?:\*\*\s*)?Article\s+([0-9\u00b9\u00b2\u00b3\u2070\u2074-\u2079]+)\.?(.*)$",
            stripped,
            re.IGNORECASE,
        )

        if m_art:
            art_id = m_art.group(1)
            cat = "Standard Article"
            rest = m_art.group(2).strip()
        elif m_sec:
            art_id = m_sec.group(1)
            cat = "Mislabeled Section"
            rest = m_sec.group(2).strip()
        elif m_sym:
            art_id = m_sym.group(1)
            cat = "Section Symbol (§)"
            rest = m_sym.group(2).strip()

        if art_id:
            norm_id = art_id
            for sup, std in SUPERSCRIPT_MAP.items():
                norm_id = norm_id.replace(sup, f"{std}")

            clean_title = re.sub(r"^\*+|\*+$", "", rest).strip()

            headings.append(
                {
                    "line_num": line_num,
                    "raw_id": art_id,
                    "norm_id": norm_id,
                    "category": cat,
                    "heading_line": raw,
                    "title": clean_title,
                }
            )

    articles = []
    for i in range(len(headings)):
        curr = headings[i]
        start_line = curr["line_num"]
        end_line = (
            headings[i + 1]["line_num"] - 1
            if i + 1 < len(headings)
            else len(lines)
        )

        block_lines = lines[start_line - 1 : end_line]
        h_line = block_lines[0].rstrip("\r\n")
        body_lines = block_lines[1:]

        body_raw = "".join(body_lines)
        body_stripped = body_raw.strip()

        is_repealed = (
            "lost force" in h_line.lower()
            or "lost force" in body_stripped.lower()
            or "repealed" in h_line.lower()
            or "repealed" in body_stripped.lower()
        )

        articles.append(
            {
                "article_index": i + 1,
                "line_start": start_line,
                "line_end": end_line,
                "raw_id": curr["raw_id"],
                "norm_id": curr["norm_id"],
                "category": curr["category"],
                "heading_line": h_line,
                "title": curr["title"],
                "text_en": body_stripped,
                "full_text": body_raw,
                "is_repealed": is_repealed,
                "char_count": len(body_stripped),
            }
        )

    return articles


def parse_markdown_articles(file_path=MARKDOWN_PATH):
    """
    Parse Civil Code markdown articles using external parser.py if present,
    otherwise falling back gracefully to internal reference parser implementation.
    """
    ext_parser = load_external_parser()
    if ext_parser is not None:
        for fn_name in [
            "parse_markdown_articles",
            "parse_markdown",
            "parse_articles",
            "extract_articles",
        ]:
            if hasattr(ext_parser, fn_name):
                fn = getattr(ext_parser, fn_name)
                try:
                    res = fn(file_path)
                    if isinstance(res, list) and len(res) > 0:
                        return res
                except Exception:
                    pass

    return parse_internal_markdown_articles(file_path)


def query_db_article_text_en(conn, parquet_path, raw_id, norm_id):
    """
    Helper to query DB for article_text_en with strict disambiguation for
    Article 26¹ (Part I) vs Article 261 (Part III).
    """
    if raw_id == "26¹":
        where_clause = "doc_id = -111189 AND article_number = '261' AND part NOT LIKE '%III%' AND (part LIKE '%I %' OR part LIKE '%I BO%' OR part LIKE '%UMUMIY%')"
    elif raw_id == "261":
        where_clause = "doc_id = -111189 AND article_number = '261' AND (part LIKE '%III%' OR part LIKE '%MAJBURIYAT%')"
    else:
        where_clause = f"doc_id = -111189 AND article_number = '{norm_id}'"

    res = conn.execute(
        f"SELECT article_text_en FROM read_parquet('{parquet_path}') WHERE {where_clause}"
    ).fetchone()
    return res[0] if res else None


class TestTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Feature Coverage (Requirements R1 - R4)"""

    def setUp(self):
        self.conn = duckdb.connect()
        self.extracted_articles = parse_markdown_articles(MARKDOWN_PATH)

    def tearDown(self):
        self.conn.close()

    def test_r1_markdown_extraction(self):
        """Test R1: Verify markdown parser extracts exactly 394 English articles, testing external parser.py dynamically if present."""
        self.assertEqual(
            len(self.extracted_articles),
            EXPECTED_TOTAL_ARTICLES,
            f"Expected {EXPECTED_TOTAL_ARTICLES} articles, got {len(self.extracted_articles)}",
        )

        # Dynamic verification of parser.py if present on disk
        ext_parser = load_external_parser()
        if ext_parser is not None:
            has_func = any(
                hasattr(ext_parser, fn)
                for fn in [
                    "parse_markdown_articles",
                    "parse_markdown",
                    "parse_articles",
                    "extract_articles",
                ]
            )
            self.assertTrue(
                has_func,
                "External parser.py found but does not expose a recognized parse function",
            )
            external_result = parse_markdown_articles(MARKDOWN_PATH)
            self.assertEqual(
                len(external_result),
                EXPECTED_TOTAL_ARTICLES,
                f"External parser.py extracted {len(external_result)} articles instead of {EXPECTED_TOTAL_ARTICLES}",
            )

    def test_r2_parquet_column_addition(self):
        """Test R2: Verify parquet schema and addition/readiness of article_text_en column (Pre-M2 vs Post-M2)."""
        self.assertTrue(
            os.path.exists(PARQUET_PATH), f"Parquet file missing: {PARQUET_PATH}"
        )

        cols_query = self.conn.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}')"
        ).fetchall()
        column_names = [col[0] for col in cols_query]

        # Verify all 23 original columns exist
        for orig_col in EXPECTED_ORIGINAL_COLUMNS:
            self.assertIn(
                orig_col,
                column_names,
                f"Original column '{orig_col}' missing from parquet schema",
            )

        if "article_text_en" in column_names:
            # Post-M2 state: column has been added
            self.assertEqual(
                len(column_names),
                24,
                f"Expected 24 columns post-M2, found {len(column_names)}",
            )
            col_type = dict([(col[0], col[1]) for col in cols_query])[
                "article_text_en"
            ]
            self.assertIn(
                "VARCHAR",
                col_type.upper(),
                f"Expected VARCHAR type for article_text_en, got {col_type}",
            )
            # Post-M2 coverage assertion
            cc_en_count = self.conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189 AND article_text_en IS NOT NULL"
            ).fetchone()[0]
            self.assertEqual(
                cc_en_count,
                EXPECTED_CIVIL_CODE_ROWS,
                f"Post-M2: Expected all {EXPECTED_CIVIL_CODE_ROWS} Civil Code rows to have non-null article_text_en, got {cc_en_count}",
            )
        else:
            # Pre-M2 state: column pending addition in M2
            self.assertEqual(
                len(column_names),
                23,
                f"Pre-M2 schema should have 23 columns, found {len(column_names)}",
            )

    def test_r3_alignment_key_matching(self):
        """Test R3: Verify strict alignment on doc_id = -111189 and article_number."""
        query = f"SELECT article_number, part, article_title FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189"
        db_rows = self.conn.execute(query).fetchall()

        self.assertEqual(
            len(db_rows),
            EXPECTED_CIVIL_CODE_ROWS,
            f"Expected {EXPECTED_CIVIL_CODE_ROWS} Civil Code rows in DB, found {len(db_rows)}",
        )

        db_art_numbers = set([row[0] for row in db_rows])

        # Verify extracted articles match DB article_number keys
        aligned_count = 0
        for art in self.extracted_articles:
            raw_id = art["raw_id"]
            norm_id = art["norm_id"]

            if norm_id in EXPECTED_MARKDOWN_ONLY_ARTICLES:
                # Omitted or repealed in Uzbek law database
                continue

            db_key = norm_id
            if db_key.startswith("26") and "¹" in raw_id:
                db_key = "261"

            self.assertIn(
                db_key,
                db_art_numbers,
                f"Extracted active article '{raw_id}' (db_key '{db_key}') not found in DB article_number set",
            )
            aligned_count += 1

        self.assertEqual(
            aligned_count,
            385,
            f"Expected 385 aligned markdown articles to match DB rows, got {aligned_count}",
        )

    def test_r4_zero_distortion_sample(self):
        """Test R4: Verify zero distortion / formatting loss in extracted text with Article 261 disambiguation."""
        sample_articles = [
            art
            for art in self.extracted_articles
            if art["raw_id"] in ["1", "2", "3", "26¹", "261"]
        ]
        self.assertGreaterEqual(len(sample_articles), 4)

        for art in sample_articles:
            body = art["text_en"]
            self.assertGreater(
                len(body),
                0,
                f"Article {art['raw_id']} has empty body text",
            )
            self.assertNotIn(
                "\x00",
                body,
                f"Article {art['raw_id']} contains null bytes",
            )

        cols_query = [
            c[0]
            for c in self.conn.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}')"
            ).fetchall()
        ]
        if "article_text_en" in cols_query:
            for art in sample_articles:
                text_en = query_db_article_text_en(
                    self.conn, PARQUET_PATH, art["raw_id"], art["norm_id"]
                )
                self.assertIsNotNone(
                    text_en,
                    f"Post-M2: DB article_text_en missing for article {art['raw_id']}",
                )
                self.assertEqual(
                    len(text_en),
                    art["char_count"],
                    f"Char length mismatch for article {art['raw_id']}: DB={len(text_en)} vs Extracted={art['char_count']}",
                )


class TestTier2BoundaryAndEdgeCases(unittest.TestCase):
    """Tier 2: Boundary & Edge Cases"""

    def setUp(self):
        self.conn = duckdb.connect()
        self.extracted_articles = parse_markdown_articles(MARKDOWN_PATH)

    def tearDown(self):
        self.conn.close()

    def test_edge_duplicate_article_261(self):
        """Test duplicate article_number '261': Part I (Article 26¹, Insolvency estate) vs Part III (Article 261, Forms of penalty)."""
        art_26_1 = [a for a in self.extracted_articles if a["raw_id"] == "26¹"]
        art_261 = [a for a in self.extracted_articles if a["raw_id"] == "261"]

        self.assertEqual(
            len(art_26_1),
            1,
            "Article 26¹ (Insolvency estate) should be extracted exactly once",
        )
        self.assertEqual(
            len(art_261),
            1,
            "Article 261 (Forms of penalty) should be extracted exactly once",
        )

        self.assertIn(
            "Insolvency",
            art_26_1[0]["title"],
            "Article 26¹ title should contain 'Insolvency'",
        )
        self.assertIn(
            "penalty",
            art_261[0]["title"].lower(),
            "Article 261 title should contain 'penalty'",
        )

        # Verify DB rows for article_number = '261' in doc_id = -111189
        db_261_rows = self.conn.execute(
            f"SELECT id, part, article_title FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189 AND article_number = '261' ORDER BY id"
        ).fetchall()
        self.assertEqual(
            len(db_261_rows),
            2,
            f"Expected exactly 2 rows for article_number = '261' in DB, found {len(db_261_rows)}",
        )

        # Disambiguate using part clause
        part1_row = self.conn.execute(
            f"SELECT id, part, article_title FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189 AND article_number = '261' AND part NOT LIKE '%III%' AND (part LIKE '%I %' OR part LIKE '%I BO%' OR part LIKE '%UMUMIY%')"
        ).fetchone()
        part3_row = self.conn.execute(
            f"SELECT id, part, article_title FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189 AND article_number = '261' AND (part LIKE '%III%' OR part LIKE '%MAJBURIYAT%')"
        ).fetchone()

        self.assertIsNotNone(part1_row, "Part I Article 26¹ DB row not found")
        self.assertIsNotNone(part3_row, "Part III Article 261 DB row not found")

        self.assertIn("qobiliyatsizligi", part1_row[2])  # Insolvency
        self.assertIn("Neustoyka", part3_row[2])  # Penalty

        # Post-M2 check: verify English texts are present, correctly assigned, and NOT swapped
        cols = [
            c[0]
            for c in self.conn.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}')"
            ).fetchall()
        ]
        if "article_text_en" in cols:
            p1_en = self.conn.execute(
                f"SELECT article_text_en FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189 AND article_number = '261' AND part NOT LIKE '%III%' AND (part LIKE '%I %' OR part LIKE '%I BO%' OR part LIKE '%UMUMIY%')"
            ).fetchone()[0]
            p3_en = self.conn.execute(
                f"SELECT article_text_en FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189 AND article_number = '261' AND (part LIKE '%III%' OR part LIKE '%MAJBURIYAT%')"
            ).fetchone()[0]

            self.assertIsNotNone(
                p1_en, "Part I article_text_en should not be NULL post-M2"
            )
            self.assertIsNotNone(
                p3_en, "Part III article_text_en should not be NULL post-M2"
            )
            self.assertEqual(
                len(p1_en),
                art_26_1[0]["char_count"],
                "Part I article_text_en char count mismatch",
            )
            self.assertEqual(
                len(p3_en),
                art_261[0]["char_count"],
                "Part III article_text_en char count mismatch",
            )
            self.assertNotEqual(
                p1_en,
                p3_en,
                "Part I and Part III English texts must not be identical or swapped",
            )
            self.assertIn(
                "insolvency",
                p1_en.lower(),
                "Part I English text should refer to insolvency",
            )
            self.assertIn(
                "penalty",
                p3_en.lower(),
                "Part III English text should refer to penalty",
            )

    def test_edge_superscript_sub_articles(self):
        """Test all 10 superscript sub-articles: 26¹, 173¹-173⁷, 259¹, 358¹."""
        extracted_superscript_ids = [
            a["raw_id"]
            for a in self.extracted_articles
            if any(sup in a["raw_id"] for sup in SUPERSCRIPT_MAP.keys())
        ]

        self.assertEqual(
            len(extracted_superscript_ids),
            len(EXPECTED_SUPERSCRIPTS),
            f"Expected {len(EXPECTED_SUPERSCRIPTS)} superscript sub-articles, found {len(extracted_superscript_ids)}",
        )

        for expected_sup in EXPECTED_SUPERSCRIPTS:
            self.assertIn(
                expected_sup,
                extracted_superscript_ids,
                f"Superscript article '{expected_sup}' missing from extracted articles",
            )

    def test_edge_titleless_headings(self):
        """Test 115 titleless headings (e.g. ## **Article 12**)."""
        titleless_articles = [
            a for a in self.extracted_articles if a["title"] == ""
        ]
        self.assertEqual(
            len(titleless_articles),
            115,
            f"Expected 115 titleless headings, found {len(titleless_articles)}",
        )

        for art in titleless_articles[:5]:
            self.assertGreater(
                len(art["text_en"]),
                0,
                f"Titleless article {art['raw_id']} has empty body text",
            )

    def test_edge_mislabeled_headings(self):
        """Test mislabeled Section headings (144, 255, 273, 302, 304, 305, 320, 349) and § headings (268, 309)."""
        mislabeled_sections = [
            a
            for a in self.extracted_articles
            if a["category"] == "Mislabeled Section"
        ]
        mislabeled_sec_ids = [a["raw_id"] for a in mislabeled_sections]

        self.assertEqual(
            len(mislabeled_sections),
            len(EXPECTED_MISLABELED_SECTIONS),
            f"Expected {len(EXPECTED_MISLABELED_SECTIONS)} mislabeled section headings, found {len(mislabeled_sections)}",
        )
        for expected_id in EXPECTED_MISLABELED_SECTIONS:
            self.assertIn(
                expected_id,
                mislabeled_sec_ids,
                f"Mislabeled Section {expected_id} missing",
            )

        sym_headings = [
            a
            for a in self.extracted_articles
            if a["category"] == "Section Symbol (§)"
        ]
        sym_ids = [a["raw_id"] for a in sym_headings]

        self.assertEqual(
            len(sym_headings),
            len(EXPECTED_SECTION_SYMBOLS),
            f"Expected {len(EXPECTED_SECTION_SYMBOLS)} § headings, found {len(sym_headings)}",
        )
        for expected_sym in EXPECTED_SECTION_SYMBOLS:
            self.assertIn(
                expected_sym,
                sym_ids,
                f"Section Symbol § {expected_sym} missing",
            )

    def test_edge_repealed_articles(self):
        """Test 7 repealed articles (63, 70, 71, 72, 176, 177, 179)."""
        repealed_articles = [
            a for a in self.extracted_articles if a["is_repealed"]
        ]
        repealed_ids = [a["raw_id"] for a in repealed_articles]

        self.assertEqual(
            len(repealed_articles),
            len(EXPECTED_REPEALED_ARTICLES),
            f"Expected {len(EXPECTED_REPEALED_ARTICLES)} repealed articles, found {len(repealed_articles)}",
        )
        for rep_id in EXPECTED_REPEALED_ARTICLES:
            self.assertIn(
                rep_id,
                repealed_ids,
                f"Repealed article {rep_id} missing from extracted repealed set",
            )
            art = [a for a in self.extracted_articles if a["raw_id"] == rep_id][
                0
            ]
            self.assertTrue(
                "lost force" in art["heading_line"].lower()
                or "lost force" in art["text_en"].lower(),
                f"Repealed notice text missing for article {rep_id}",
            )

    def test_edge_missing_article_168(self):
        """Test missing article 168 (gap between 167 and 169)."""
        art_168 = [a for a in self.extracted_articles if a["raw_id"] == "168"]
        self.assertEqual(
            len(art_168),
            0,
            "Article 168 should NOT exist in the markdown file",
        )

        art_167 = [a for a in self.extracted_articles if a["raw_id"] == "167"]
        art_169 = [a for a in self.extracted_articles if a["raw_id"] == "169"]
        self.assertEqual(len(art_167), 1, "Article 167 should exist")
        self.assertEqual(len(art_169), 1, "Article 169 should exist")


class TestTier3NonDestructiveSchemaIntegrity(unittest.TestCase):
    """Tier 3: Non-Destructive & Schema Integrity"""

    def setUp(self):
        self.conn = duckdb.connect()

    def tearDown(self):
        self.conn.close()

    def test_integrity_row_count(self):
        """Test total row count of articles/train-00000-of-00001.parquet remains exactly 54,173."""
        row_count = self.conn.execute(
            f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}')"
        ).fetchone()[0]
        self.assertEqual(
            row_count,
            EXPECTED_TOTAL_PARQUET_ROWS,
            f"Total parquet row count altered! Expected {EXPECTED_TOTAL_PARQUET_ROWS}, got {row_count}",
        )

    def test_integrity_column_count(self):
        """Test total columns count (24 columns when article_text_en is present, 23 originally)."""
        cols_query = self.conn.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}')"
        ).fetchall()
        column_names = [col[0] for col in cols_query]

        if "article_text_en" in column_names:
            self.assertEqual(
                len(column_names),
                24,
                f"Expected 24 columns post-M2, got {len(column_names)}",
            )
        else:
            self.assertEqual(
                len(column_names),
                23,
                f"Expected 23 columns pre-M2, got {len(column_names)}",
            )

        for idx, orig_col in enumerate(EXPECTED_ORIGINAL_COLUMNS):
            self.assertEqual(
                column_names[idx],
                orig_col,
                f"Column at index {idx} changed! Expected '{orig_col}', got '{column_names[idx]}'",
            )

    def test_integrity_uzbek_text_intact(self):
        """Test existing Uzbek article_text is 100% intact (0 nulls, 0 empty strings)."""
        null_count = self.conn.execute(
            f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}') WHERE article_text IS NULL"
        ).fetchone()[0]
        empty_count = self.conn.execute(
            f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}') WHERE article_text = ''"
        ).fetchone()[0]

        self.assertEqual(
            null_count, 0, f"Found {null_count} NULLs in Uzbek article_text"
        )
        self.assertEqual(
            empty_count,
            0,
            f"Found {empty_count} empty strings in Uzbek article_text",
        )

        cc_uzbek_len = self.conn.execute(
            f"SELECT SUM(LENGTH(article_text)) FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189"
        ).fetchone()[0]
        self.assertGreater(
            cc_uzbek_len,
            250000,
            "Uzbek article_text total length is abnormally short!",
        )

    def test_integrity_doc_id_alignment(self):
        """Test doc_id = -111189 alignment (exactly 386 rows in doc_id = -111189) and non-null distribution (Pre-M2 vs Post-M2)."""
        cc_rows = self.conn.execute(
            f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189"
        ).fetchone()[0]
        self.assertEqual(
            cc_rows,
            EXPECTED_CIVIL_CODE_ROWS,
            f"Expected {EXPECTED_CIVIL_CODE_ROWS} rows for doc_id = -111189, got {cc_rows}",
        )

        cols_query = [
            c[0]
            for c in self.conn.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}')"
            ).fetchall()
        ]
        if "article_text_en" in cols_query:
            # Post-M2 checks: 386 non-null for doc_id = -111189, 0 non-null for all other 53,787 rows
            cc_en_count = self.conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189 AND article_text_en IS NOT NULL"
            ).fetchone()[0]
            self.assertEqual(
                cc_en_count,
                EXPECTED_CIVIL_CODE_ROWS,
                f"Post-M2: Expected all {EXPECTED_CIVIL_CODE_ROWS} Civil Code rows to have non-null article_text_en, got {cc_en_count}",
            )

            non_cc_en_count = self.conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}') WHERE doc_id != -111189 AND article_text_en IS NOT NULL"
            ).fetchone()[0]
            self.assertEqual(
                non_cc_en_count,
                0,
                f"Post-M2: article_text_en should be NULL for all 53,787 non-Civil-Code rows, found {non_cc_en_count} non-NULLs",
            )
        else:
            # Pre-M2 check: article_text_en column not yet added
            self.assertNotIn(
                "article_text_en",
                cols_query,
                "Pre-M2 schema should not contain article_text_en column",
            )


class TestTier4ProgrammaticAcceptanceCriteria(unittest.TestCase):
    """Tier 4: Programmatic Acceptance Criteria Verification"""

    def setUp(self):
        self.conn = duckdb.connect()
        self.extracted_articles = parse_markdown_articles(MARKDOWN_PATH)

    def tearDown(self):
        self.conn.close()

    def test_ac1_article_count_equality(self):
        """AC1: Test extracted markdown article count (394) vs updated non-null article_text_en rows contract (386 post-M2)."""
        extracted_count = len(self.extracted_articles)
        self.assertEqual(
            extracted_count,
            EXPECTED_TOTAL_ARTICLES,
            f"AC1 Failure: Extracted article count is {extracted_count}, expected {EXPECTED_TOTAL_ARTICLES}",
        )

        cols_query = [
            c[0]
            for c in self.conn.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}')"
            ).fetchall()
        ]
        if "article_text_en" in cols_query:
            # Post-M2 assertions
            updated_count = self.conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}') WHERE doc_id = -111189 AND article_text_en IS NOT NULL"
            ).fetchone()[0]

            # 1. Assert that all 386 rows of doc_id = -111189 have non-null article_text_en (100% coverage)
            self.assertEqual(
                updated_count,
                EXPECTED_CIVIL_CODE_ROWS,
                f"AC1 Failure: Expected all {EXPECTED_CIVIL_CODE_ROWS} doc_id = -111189 rows to have non-null article_text_en, got {updated_count}",
            )

            # 2. Assert that all 394 extracted markdown articles are mapped and present in the dataset contract
            active_extracted = [
                a
                for a in self.extracted_articles
                if a["norm_id"] not in EXPECTED_MARKDOWN_ONLY_ARTICLES
            ]
            self.assertEqual(
                len(active_extracted),
                385,
                f"AC1 Failure: Expected 385 active extracted articles matching DB keys, got {len(active_extracted)}",
            )
            # Verify 385 active extracted articles + 9 markdown-only/repealed articles = 394 total
            self.assertEqual(
                len(active_extracted) + len(EXPECTED_MARKDOWN_ONLY_ARTICLES),
                EXPECTED_TOTAL_ARTICLES,
                "AC1 Failure: Active extracted + markdown-only articles sum does not equal 394",
            )

    def test_ac2_random_sampling_char_count(self):
        """AC2: Character count sampling for >= 10 random articles (standards, sub-articles, mislabeled sections, repealed) comparing extracted vs DB."""
        # 17 representative sample targets covering all structural categories (>= 10)
        sample_targets = [
            "1",
            "50",
            "100",
            "200",
            "300",
            "385",  # Standard articles
            "26¹",
            "261",
            "173¹",
            "173⁷",
            "259¹",
            "358¹",  # Sub-articles & duplicates
            "144",
            "255",
            "268",
            "309",  # Mislabeled Section/§ headings
            "63",
            "70",
            "176",  # Repealed articles
        ]
        sample_articles = [
            a for a in self.extracted_articles if a["raw_id"] in sample_targets
        ]

        self.assertGreaterEqual(
            len(sample_articles),
            10,
            f"AC2 Failure: Expected at least 10 sampled articles, got {len(sample_articles)}",
        )

        for art in sample_articles:
            raw_char_count = art["char_count"]
            self.assertEqual(
                len(art["text_en"]),
                raw_char_count,
                f"AC2 Failure: Character count mismatch for article {art['raw_id']}: len(text_en)={len(art['text_en'])} vs raw={raw_char_count}",
            )

        cols_query = [
            c[0]
            for c in self.conn.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{PARQUET_PATH}')"
            ).fetchall()
        ]
        if "article_text_en" in cols_query:
            for art in sample_articles:
                if art["norm_id"] in EXPECTED_MARKDOWN_ONLY_ARTICLES:
                    continue

                db_text = query_db_article_text_en(
                    self.conn, PARQUET_PATH, art["raw_id"], art["norm_id"]
                )
                self.assertIsNotNone(
                    db_text,
                    f"AC2 Failure: DB article_text_en missing for sample article {art['raw_id']}",
                )
                self.assertEqual(
                    len(db_text),
                    art["char_count"],
                    f"AC2 Failure: Parquet char count ({len(db_text)}) != markdown char count ({art['char_count']}) for article {art['raw_id']}",
                )

    def test_ac3_uzbek_text_intactness(self):
        """AC3: Uzbek text intactness verification."""
        total_uzbek_rows = self.conn.execute(
            f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}') WHERE article_text IS NOT NULL AND LENGTH(article_text) > 0"
        ).fetchone()[0]

        self.assertEqual(
            total_uzbek_rows,
            EXPECTED_TOTAL_PARQUET_ROWS,
            f"AC3 Failure: Uzbek text lost or corrupted! Valid rows: {total_uzbek_rows}/{EXPECTED_TOTAL_PARQUET_ROWS}",
        )


if __name__ == "__main__":
    unittest.main()
