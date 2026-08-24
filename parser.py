#!/usr/bin/env python3
"""
parser.py — Civil Code of Uzbekistan (Part 1) Markdown Parser Engine
---------------------------------------------------------------------
Parses `Civil_Code_Part1_Updated_2025.md` into structured JSON (`parsed_articles.json`).

Features:
- Finite State Machine (FSM) line-by-line streaming parser (lines 1 to 3632).
- Structural context tracking (Part, Section, Subsection, Chapter, Paragraph Division).
- Robust regular expressions for 384 standard articles, 8 Section-mislabeled articles,
  2 §-mislabeled articles, 10 superscript sub-articles, and 115 titleless headings.
- Zero-distortion formatting preservation (verbatim raw_content and clean_text).
- 15-field output schema generation for `parsed_articles.json`.
- Built-in `--verify` and `--summary` CLI suite with 10 automated verification checks.
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# ==============================================================================
# CONSTANTS & TAXONOMY CONFIGURATION
# ==============================================================================

MISLABELED_SECTIONS = {'144', '255', '273', '302', '304', '305', '320', '349'}
MISLABELED_SYMBOLS = {'268', '309'}
REPEALED_ARTICLES = {'63', '70', '71', '72', '176', '177', '179'}

SUPERSCRIPT_MAP = {
    '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0'
}

DEFAULT_INPUT_PATHS = [
    Path("Civil code of Uzbekistan_general part/Civil_Code_Part1_Updated_2025.md"),
    Path("Civil_Code_Part1_Updated_2025.md"),
    Path("c:/uzbek-legal-corpus/Civil code of Uzbekistan_general part/Civil_Code_Part1_Updated_2025.md"),
    Path("c:/uzbek-legal-corpus/Civil_Code_Part1_Updated_2025.md")
]

# ==============================================================================
# REGULAR EXPRESSIONS
# ==============================================================================

# Article Heading Pattern (Primary):
# Captures optional #, ##, ### prefix, bold **, keyword (Article|Section|§), number with superscripts, and title rest
ARTICLE_HEADING_PATTERN = re.compile(
    r'^(?P<prefix>#{1,3}\s+)?\*\*(?P<kw>Article|Section|§)\s+(?P<num>\d+[¹²³⁴⁵⁶⁷⁸⁹⁰]*)(?P<rest>.*?)\*\*\s*$',
    re.IGNORECASE
)

# Alternative Heading Pattern (for headings where closing ** comes right after number):
ARTICLE_HEADING_ALT_PATTERN = re.compile(
    r'^(?P<prefix>#{1,3}\s+)?\*\*(?P<kw>Article|Section|§)\s+(?P<num>\d+[¹²³⁴⁵⁶⁷⁸⁹⁰]*)\*\*\s*(?P<rest>.*)$',
    re.IGNORECASE
)

# Structural Header Patterns:
PART_PATTERN = re.compile(r'^(?:#{1,3}\s+)?\*\*(Part\s+[A-Za-z0-9_\s]+)\*\*', re.IGNORECASE)
SECTION_ROMAN_PATTERN = re.compile(r'^(?:#{1,3}\s+)?\*\*(Section\s+[IVXLCDM]+\..*?)\*\*', re.IGNORECASE)
SUBSECTION_TEXT_PATTERN = re.compile(r'^(?:#{1,3}\s+)?\*\*(Subsection\s+\d+.*?)\*\*', re.IGNORECASE)
CHAPTER_PATTERN = re.compile(r'^(?:#{1,3}\s+)?\*\*(Chapter\s+\d+.*?)\*\*', re.IGNORECASE)
CHAPTER_ALT_PATTERN = re.compile(r'^(?:#{1,3}\s+)?Chapter\s+\d+', re.IGNORECASE)
PARAGRAPH_DIV_PATTERN = re.compile(r'^(?:#{1,3}\s+)?\*\*(§\s+(?:[1-9]|10)\..*?)\*\*', re.IGNORECASE)


# ==============================================================================
# STRUCTURAL CONTEXT TRACKER
# ==============================================================================

class ContextTracker:
    """Tracks hierarchical legal context (Part, Section, Chapter, Subsection)."""
    def __init__(self):
        self.part: str = "Part one"
        self.section: Optional[str] = None
        self.chapter: Optional[str] = None
        self.subsection: Optional[str] = None
        self.paragraph_division: Optional[str] = None

    def snapshot(self) -> Dict[str, Optional[str]]:
        return {
            "part": self.part,
            "section": self.section,
            "chapter": self.chapter,
            "subsection": self.subsection
        }


# ==============================================================================
# FSM PARSER ENGINE
# ==============================================================================

def parse_markdown(input_path: Path) -> Dict[str, Any]:
    """Parses Civil Code Markdown file line-by-line using an FSM."""
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    ctx = ContextTracker()
    raw_articles_data: List[Dict[str, Any]] = []
    
    in_frontmatter = False
    frontmatter_lines: List[str] = []
    preamble_lines: List[str] = []
    
    current_article: Optional[Dict[str, Any]] = None

    for i, line in enumerate(lines):
        line_no = i + 1  # 1-indexed line number
        line_s = line.strip()

        # Handle YAML frontmatter lines (1..5)
        if line_s == '---':
            if line_no == 1:
                in_frontmatter = True
                frontmatter_lines.append(line)
                continue
            elif in_frontmatter:
                in_frontmatter = False
                frontmatter_lines.append(line)
                continue

        if in_frontmatter:
            frontmatter_lines.append(line)
            continue

        # Check for Structural Headers (Part, Section, Chapter, Subsection)
        m_part = PART_PATTERN.match(line_s)
        if m_part:
            ctx.part = m_part.group(1).strip()
            if current_article:
                current_article['body_lines'].append(line)
            else:
                preamble_lines.append(line)
            continue

        m_sec = SECTION_ROMAN_PATTERN.match(line_s)
        if m_sec:
            ctx.section = m_sec.group(1).strip()
            if current_article:
                current_article['body_lines'].append(line)
            else:
                preamble_lines.append(line)
            continue

        m_sub = SUBSECTION_TEXT_PATTERN.match(line_s)
        if m_sub:
            ctx.subsection = m_sub.group(1).strip()
            if current_article:
                current_article['body_lines'].append(line)
            else:
                preamble_lines.append(line)
            continue

        m_chap = CHAPTER_PATTERN.match(line_s) or CHAPTER_ALT_PATTERN.match(line_s)
        if m_chap:
            ctx.chapter = line_s.strip('*# ')
            ctx.paragraph_division = None
            if current_article:
                current_article['body_lines'].append(line)
            else:
                preamble_lines.append(line)
            continue

        m_pdiv = PARAGRAPH_DIV_PATTERN.match(line_s)
        if m_pdiv:
            ctx.paragraph_division = m_pdiv.group(1).strip()
            if current_article:
                current_article['body_lines'].append(line)
            else:
                preamble_lines.append(line)
            continue

        # Check for Article Headings
        m_art = ARTICLE_HEADING_PATTERN.match(line_s) or ARTICLE_HEADING_ALT_PATTERN.match(line_s)
        is_article_heading = False
        heading_kw = ""
        heading_num = ""
        heading_rest = ""

        if m_art:
            kw = m_art.group('kw')
            num = m_art.group('num')
            rest = m_art.group('rest')
            clean_base = re.sub(r'\D', '', num)

            if kw.lower() == 'article':
                is_article_heading = True
                heading_kw = 'Article'
            elif kw.lower() == 'section' and clean_base in MISLABELED_SECTIONS:
                is_article_heading = True
                heading_kw = 'Section'
            elif kw == '§' and (clean_base in MISLABELED_SYMBOLS or (clean_base.isdigit() and int(clean_base) >= 10)):
                is_article_heading = True
                heading_kw = '§'

            if is_article_heading:
                heading_num = num
                heading_rest = rest

        if is_article_heading:
            # Finalize previous article if active
            if current_article:
                current_article['end_line'] = line_no - 1
                raw_articles_data.append(current_article)

            # Extract title and titleless flag
            title_text = re.sub(r'^[\.\:]\s*', '', heading_rest.strip()).strip()
            title_text = title_text.strip('*_ ')
            is_titleless = (len(title_text) == 0)

            # Classify heading type
            if heading_kw == 'Section':
                heading_type = 'mislabeled_section'
            elif heading_kw == '§':
                heading_type = 'mislabeled_symbol'
            else:
                heading_type = 'standard_article'

            current_article = {
                'start_line': line_no,
                'heading_line': line,
                'heading_kw': heading_kw,
                'num_str': heading_num,
                'title': title_text,
                'titleless': is_titleless,
                'heading_type': heading_type,
                'context': ctx.snapshot(),
                'body_lines': []
            }
        else:
            if current_article:
                current_article['body_lines'].append(line)
            else:
                preamble_lines.append(line)

    # Finalize last article
    if current_article:
        current_article['end_line'] = len(lines)
        raw_articles_data.append(current_article)

    # Transform into final 15-field schema objects
    articles_list: List[Dict[str, Any]] = []
    
    for art in raw_articles_data:
        num_str = art['num_str']
        base_num = int(re.sub(r'\D', '', num_str))
        
        # Detect superscript character
        sup_chars = [c for c in num_str if c in SUPERSCRIPT_MAP]
        if sup_chars:
            superscript_val = "".join(SUPERSCRIPT_MAP[c] for c in sup_chars)
        else:
            superscript_val = None

        # Formulate db_article_number_key
        if superscript_val:
            db_key = f"{base_num}{superscript_val}"
        else:
            db_key = str(base_num)

        article_id = num_str

        # Format display label
        if art['heading_type'] == 'mislabeled_section':
            display_label = f"Section {num_str}"
        elif art['heading_type'] == 'mislabeled_symbol':
            display_label = f"§ {num_str}"
        else:
            display_label = f"Article {num_str}"

        # Build raw content and clean text
        raw_content = art['heading_line'] + "".join(art['body_lines'])
        clean_text = "".join(art['body_lines']).strip()

        # Check repealed status
        is_repealed = (str(base_num) in REPEALED_ARTICLES and superscript_val is None) or ("lost force" in clean_text.lower())

        article_obj = {
            "article_id": article_id,
            "article_number_base": base_num,
            "superscript": superscript_val,
            "db_article_number_key": db_key,
            "article_number_display": display_label,
            "title": art['title'],
            "titleless": art['titleless'],
            "heading_type": art['heading_type'],
            "structural_hierarchy": art['context'],
            "raw_content": raw_content,
            "clean_text": clean_text,
            "char_count_raw": len(raw_content),
            "char_count_clean": len(clean_text),
            "line_range": {
                "start_line": art['start_line'],
                "end_line": art['end_line']
            },
            "repealed": is_repealed
        }
        articles_list.append(article_obj)

    # Build Metadata Summary Object
    metadata = {
        "source_file": str(input_path).replace("\\", "/"),
        "total_articles_parsed": len(articles_list),
        "standard_article_headings": len([a for a in articles_list if a['heading_type'] == 'standard_article']),
        "mislabeled_section_headings": len([a for a in articles_list if a['heading_type'] == 'mislabeled_section']),
        "mislabeled_symbol_headings": len([a for a in articles_list if a['heading_type'] == 'mislabeled_symbol']),
        "superscript_sub_articles": len([a for a in articles_list if a['superscript'] is not None]),
        "titleless_headings": len([a for a in articles_list if a['titleless']]),
        "repealed_articles": len([a for a in articles_list if a['repealed']]),
        "missing_base_articles_in_markdown": ["168"]
    }

    return {
        "metadata": metadata,
        "articles": articles_list
    }


# ==============================================================================
# AUTOMATED VERIFICATION SUITE (10 CHECKS)
# ==============================================================================

def verify_parsed_data(data: Dict[str, Any], strict: bool = False) -> Tuple[bool, List[str]]:
    """Executes 10 automated verification checks on parsed JSON data."""
    errors: List[str] = []
    articles = data.get("articles", [])

    # V1: Total Article Count
    if len(articles) != 394:
        errors.append(f"V1 Failed: Total article count is {len(articles)}, expected 394.")

    # V2: Zero Duplicate IDs
    ids = [a["article_id"] for a in articles]
    if len(set(ids)) != len(ids):
        duplicates = [i for i in set(ids) if ids.count(i) > 1]
        errors.append(f"V2 Failed: Found duplicate article_ids: {duplicates}")

    # V3: Mislabeled Section Count & Targets
    sec_ids = sorted([a["article_id"] for a in articles if a["heading_type"] == "mislabeled_section"], key=int)
    expected_sec = ["144", "255", "273", "302", "304", "305", "320", "349"]
    if sec_ids != expected_sec:
        errors.append(f"V3 Failed: Mislabeled section articles got {sec_ids}, expected {expected_sec}.")

    # V4: Mislabeled Symbol Count & Targets
    sym_ids = sorted([a["article_id"] for a in articles if a["heading_type"] == "mislabeled_symbol"], key=int)
    expected_sym = ["268", "309"]
    if sym_ids != expected_sym:
        errors.append(f"V4 Failed: Mislabeled symbol articles got {sym_ids}, expected {expected_sym}.")

    # V5: Superscript Sub-articles Count & Targets
    super_ids = [a["article_id"] for a in articles if a["superscript"] is not None]
    expected_super = ["26¹", "173¹", "173²", "173³", "173⁴", "173⁵", "173⁶", "173⁷", "259¹", "358¹"]
    if sorted(super_ids) != sorted(expected_super):
        errors.append(f"V5 Failed: Superscript articles got {super_ids}, expected {expected_super}.")

    # V6: Titleless Headings Count
    titleless_count = len([a for a in articles if a.get("titleless", False)])
    if titleless_count != 115:
        errors.append(f"V6 Failed: Titleless headings count is {titleless_count}, expected 115.")

    # V7: Repealed Articles Count & Targets
    repealed_ids = sorted([a["article_id"] for a in articles if a.get("repealed", False)], key=lambda x: int(re.sub(r'\D', '', x)))
    expected_repealed = ["63", "70", "71", "72", "176", "177", "179"]
    if repealed_ids != expected_repealed:
        errors.append(f"V7 Failed: Repealed articles got {repealed_ids}, expected {expected_repealed}.")

    # V8: No Empty Text Bodies
    empty_articles = [a["article_id"] for a in articles if not a.get("clean_text", "").strip() or a.get("char_count_clean", 0) <= 0]
    if empty_articles:
        errors.append(f"V8 Failed: Found empty text bodies in articles: {empty_articles}")

    # V9: Line Range Continuity & Ascending Order
    if articles:
        if articles[0]["line_range"]["start_line"] != 14:
            errors.append(f"V9 Failed: First article start_line is {articles[0]['line_range']['start_line']}, expected 14.")
        if articles[-1]["line_range"]["end_line"] != 3632:
            errors.append(f"V9 Failed: Last article end_line is {articles[-1]['line_range']['end_line']}, expected 3632.")
        
        last_start = 0
        for a in articles:
            start = a["line_range"]["start_line"]
            end = a["line_range"]["end_line"]
            if start > end:
                errors.append(f"V9 Failed: Article {a['article_id']} has start_line ({start}) > end_line ({end}).")
            if start <= last_start:
                errors.append(f"V9 Failed: Article {a['article_id']} start_line ({start}) <= previous start_line ({last_start}).")
            last_start = start

    # V10: Disambiguation Key Validation
    art_26_1 = next((a for a in articles if a["article_id"] == "26¹"), None)
    art_261 = next((a for a in articles if a["article_id"] == "261"), None)
    if not art_26_1 or not art_261:
        errors.append("V10 Failed: Article 26¹ or Article 261 missing from parsed articles.")
    elif art_26_1["db_article_number_key"] != "261" or art_261["db_article_number_key"] != "261":
        errors.append(f"V10 Failed: db_article_number_key mismatch for Article 26¹ ({art_26_1.get('db_article_number_key')}) or Article 261 ({art_261.get('db_article_number_key')}).")

    return (len(errors) == 0, errors)


# ==============================================================================
# CLI RUNNER & ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Civil Code English Translation Markdown Parser")
    parser.add_argument("-i", "--input", help="Path to input markdown file")
    parser.add_argument("-o", "--output", default="parsed_articles.json", help="Path to output JSON file")
    parser.add_argument("-v", "--verify", action="store_true", help="Run 10-check automated verification suite")
    parser.add_argument("-s", "--summary", action="store_true", help="Print summary report to console")
    parser.add_argument("--strict", action="store_true", help="Treat verification warnings as fatal errors")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress informational messages")

    args = parser.parse_args()

    # Determine input path
    input_path: Optional[Path] = None
    if args.input:
        input_path = Path(args.input)
    else:
        for p in DEFAULT_INPUT_PATHS:
            if p.exists():
                input_path = p
                break

    if not input_path or not input_path.exists():
        print(f"[ERROR] Input markdown file not found.", file=sys.stderr)
        sys.exit(2)

    if not args.quiet:
        print(f"[INFO] Reading source markdown: {input_path}")

    try:
        parsed_data = parse_markdown(input_path)
    except Exception as e:
        print(f"[ERROR] Parsing failed with exception: {e}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        if not args.quiet:
            file_size_kb = output_path.stat().st_size / 1024.0
            print(f"[SUCCESS] Parsed {parsed_data['metadata']['total_articles_parsed']} articles.")
            print(f"[SUCCESS] Output written to {output_path} ({file_size_kb:.1f} KB).")
    except Exception as e:
        print(f"[ERROR] Failed to write output JSON to {output_path}: {e}", file=sys.stderr)
        sys.exit(3)

    if args.summary and not args.quiet:
        meta = parsed_data['metadata']
        print("\n" + "="*60)
        print("PARSER EXECUTION SUMMARY REPORT")
        print("="*60)
        print(f" Source File                   : {meta['source_file']}")
        print(f" Total Articles Parsed         : {meta['total_articles_parsed']}")
        print(f" Standard Article Headings     : {meta['standard_article_headings']}")
        print(f" Mislabeled Section Headings  : {meta['mislabeled_section_headings']}")
        print(f" Mislabeled Symbol (§) Headings: {meta['mislabeled_symbol_headings']}")
        print(f" Superscript Sub-articles      : {meta['superscript_sub_articles']}")
        print(f" Titleless Headings            : {meta['titleless_headings']}")
        print(f" Repealed / Lost-Force Articles: {meta['repealed_articles']}")
        print(f" Missing Base Articles in MD   : {meta['missing_base_articles_in_markdown']}")
        print("="*60 + "\n")

    if args.verify:
        if not args.quiet:
            print("[INFO] Running automated verification checks...")
        passed, errors = verify_parsed_data(parsed_data, strict=args.strict)
        if not passed:
            print("[FAIL] Verification failed:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            sys.exit(1)
        elif not args.quiet:
            print("  [PASS] Check 1: Total Article Count (394/394)")
            print("  [PASS] Check 2: Zero Duplicate Article Identifiers (394 unique)")
            print("  [PASS] Check 3: Mislabeled Section Headings Count (8/8)")
            print("  [PASS] Check 4: Mislabeled Section Symbol Headings Count (2/2)")
            print("  [PASS] Check 5: Superscript Sub-articles Count (10/10)")
            print("  [PASS] Check 6: Titleless Headings Count (115/115)")
            print("  [PASS] Check 7: Repealed Articles Count (7/7)")
            print("  [PASS] Check 8: No Empty Text Bodies (0/394 empty)")
            print("  [PASS] Check 9: Complete Line Range Coverage (Lines 14 to 3632)")
            print("  [PASS] Check 10: Disambiguation Keys Validation (26¹ vs 261)")
            print("[SUCCESS] All 10 verification checks PASSED.")

    sys.exit(0)


if __name__ == "__main__":
    main()
