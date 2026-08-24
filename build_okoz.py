#!/usr/bin/env python
"""
M3 — Load the OKOZ classification axis into corpus.duckdb.

Creates:
    okoz_node        the full classifier tree (all 19 spheres, 4 levels)
    okoz_assignment  struct_node -> OKOZ code mappings for the Civil Code
                     General Part, PROPOSED by title correspondence and
                     awaiting the owner's validation (validated_by is NULL)
    v_okoz_general_part   article -> OKOZ breadcrumb via its structural node

Design decisions:
  * Assignments attach to STRUCTURAL nodes, not articles: OKOZ classifies
    institutions of law, and the Code's chapters/sections ARE those
    institutions.  Articles inherit through their node, so a re-mapping
    of one node reclassifies its whole range at once.
  * Every mapping is a proposal.  confidence reflects how mechanical the
    title correspondence is; validated_by stays NULL until the owner
    confirms it (M4 exposes this).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

import okoz_parser

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "corpus.duckdb"

# ---------------------------------------------------------------------------
# Proposed mapping: General Part structural node -> OKOZ code.
# node_id -> (okoz_code, confidence, rationale)
#
# Confidence tiers:
#   0.95 the OKOZ label and the chapter/section title are the same institution
#   0.85-0.90 same institution, wording differs or OKOZ is one level coarser
#   <=0.80 judgment call — flagged for the owner's attention first
# ---------------------------------------------------------------------------
MAPPING: dict[str, tuple[str, float, str]] = {
    # Part I. General Provisions
    "C1":     ("03.01.00.00", 0.90, "Civil Legislation -> sphere-03 General Provisions"),
    "C2":     ("03.01.00.00", 0.75, "no dedicated OKOZ node for emergence/exercise/protection "
                                    "of civil rights; nearest is 03.01 General Provisions"),
    "C3":     ("03.02.00.00", 0.95, "Citizens (Natural Persons) = Citizens (Individuals)"),
    "C4":     ("03.03.00.00", 0.95, "Legal Entities, institution-level"),
    "C4.S1":  ("03.03.01.00", 0.90, "General Provisions on legal entities"),
    "C4.S2":  ("03.03.04.00", 0.90, "Commercial Organizations = Commercial Organisations"),
    "C4.S3":  ("03.03.10.00", 0.90, "Non-Commercial Organizations = Non-Profit Organisations"),
    "C5":     ("03.03.11.00", 0.95, "The State as a Participant in Civil-Law Relations, verbatim"),
    "C6":     ("03.04.01.00", 0.90, "Objects: General Provisions"),
    "C7":     ("03.04.03.00", 0.85, "Material Benefits = Tangible Benefits"),
    "C8":     ("03.04.04.00", 0.85, "Non-Material Benefits = Intangible Benefits"),
    "C9":     ("03.05.00.00", 0.95, "Transactions"),
    "C9.S1":  ("03.05.00.00", 0.85, "OKOZ does not subdivide Transactions; inherits institution"),
    "C9.S2":  ("03.05.00.00", 0.85, "OKOZ does not subdivide Transactions; inherits institution"),
    "C10":    ("03.06.00.00", 0.95, "Representation. Power of Attorney, verbatim"),
    "C11":    ("03.07.01.00", 0.90, "Calculation of Time Periods -> Time Limits"),
    "C12":    ("03.07.02.00", 0.90, "Limitation of Actions -> Limitation Period"),
    # Part II. Ownership
    "C13":    ("03.08.01.00", 0.90, "Ownership: General Provisions"),
    "C14":    ("03.08.07.00", 0.80, "chapter spans economic AND operational management "
                                    "(03.08.07.01 + 03.08.07.02); mapped to their parent"),
    "C15":    ("03.08.02.00", 0.90, "Acquisition and Termination of Ownership"),
    "C16":    ("03.08.03.00", 0.95, "Private Ownership, verbatim"),
    "C17":    ("03.08.04.00", 0.95, "Public Ownership, verbatim"),
    "C18":    ("03.08.06.00", 0.95, "Common Ownership, verbatim"),
    "C19":    ("03.09.00.00", 0.95, "Protection of Ownership and Other Rights in Rem"),
    # Part III. Law of Obligations (General Part half)
    "C20":    ("03.10.01.00", 0.90, "Concept and Parties to Obligations"),
    "C21":    ("03.10.00.00", 0.70, "no OKOZ node for Performance of Obligations; mapped to "
                                    "the Law of Obligations institution itself"),
    "C22":    ("03.10.02.00", 0.95, "Security for Performance of Obligations, verbatim"),
    "C22.S1": ("03.10.02.01", 0.95, "Penalty"),
    "C22.S2": ("03.10.02.02", 0.95, "Pledge"),
    "C22.S3": ("03.10.02.03", 0.95, "Retention"),
    "C22.S4": ("03.10.02.04", 0.95, "Suretyship"),
    "C22.S5": ("03.10.02.05", 0.95, "Guarantee"),
    "C22.S6": ("03.10.02.06", 0.90, "Deposit (zadatok) = Earnest Money"),
    "C23":    ("03.10.01.00", 0.85, "Change of Persons in an Obligation is named inside "
                                    "03.10.01 (Substitution of Parties)"),
    "C24":    ("03.10.03.00", 0.95, "Liability for Breach of Obligations, verbatim"),
    "C25":    ("03.10.04.00", 0.95, "Termination of Obligations, verbatim"),
    "C26":    ("03.10.05.00", 0.90, "Contract: Concept and Terms -> 03.10.05 Contract"),
    "C27":    ("03.10.05.00", 0.90, "Conclusion of a Contract -> 03.10.05 Contract"),
    "C28":    ("03.10.05.00", 0.90, "Amendment and Dissolution -> 03.10.05 Contract"),
}


def log(msg: str = "") -> None:
    print(msg, flush=True)


def main() -> int:
    nodes = okoz_parser.parse_okoz()
    errors, warnings = okoz_parser.validate(nodes)
    if errors:
        for e in errors:
            log(f"ERROR {e}")
        return 1
    log(f"OKOZ tree parsed: {len(nodes)} nodes, {len(warnings)} source warnings")

    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE OR REPLACE TABLE okoz_node (
            code        VARCHAR PRIMARY KEY,
            parent_code VARCHAR,
            level       INTEGER,     -- 1 sphere | 2 institution | 3 subinst. | 4 detail
            label_en    VARCHAR,
            see_also    VARCHAR,     -- comma-separated codes, '' if none
            ordinal     INTEGER      -- document order
        );
    """)
    con.executemany(
        "INSERT INTO okoz_node VALUES (?, ?, ?, ?, ?, ?)",
        [(n.code, n.parent_code, n.level, n.label_en, ",".join(n.see_also), n.ordinal)
         for n in nodes],
    )

    # ------------------------------------------------------------ assignments
    valid_nodes = {r[0] for r in con.execute("SELECT node_id FROM struct_node").fetchall()}
    missing = [nid for nid in MAPPING if nid not in valid_nodes]
    if missing:
        log(f"ERROR mapping references unknown struct nodes: {missing}")
        return 1
    codes = {n.code for n in nodes}
    bad = [c for c, _, _ in MAPPING.values() if c not in codes]
    if bad:
        log(f"ERROR mapping references unknown OKOZ codes: {bad}")
        return 1

    now = datetime.now(timezone.utc)
    con.execute("""
        CREATE OR REPLACE TABLE okoz_assignment (
            assignment_id  INTEGER PRIMARY KEY,
            okoz_code      VARCHAR,
            struct_node_id VARCHAR,
            method         VARCHAR,
            confidence     DOUBLE,
            rationale      VARCHAR,
            proposed_at    TIMESTAMPTZ,
            validated_by   VARCHAR,      -- NULL until the owner confirms
            validated_at   TIMESTAMPTZ
        );
    """)
    con.executemany(
        "INSERT INTO okoz_assignment VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)",
        [(i, code, nid, "structural_title_match", conf, why, now)
         for i, (nid, (code, conf, why)) in enumerate(sorted(MAPPING.items()), 1)],
    )

    # Article -> OKOZ, inherited through the article's structural node, with
    # the full classifier breadcrumb resolved for display.
    con.execute("""
        CREATE OR REPLACE VIEW v_okoz_general_part AS
        WITH RECURSIVE chain(code, parent_code, label_en, level, root) AS (
            SELECT code, parent_code, label_en, level, code FROM okoz_node
            UNION ALL
            SELECT o.code, o.parent_code, o.label_en, o.level, c.root
            FROM okoz_node o JOIN chain c ON o.code = c.parent_code
        ),
        breadcrumb AS (
            SELECT root AS code,
                   string_agg(label_en, ' > ' ORDER BY level) AS okoz_breadcrumb
            FROM chain GROUP BY root
        )
        SELECT
            n.norm_id, n.article_number, n.article_base, n.superscript,
            n.article_title_uz, n.article_title_en, n.struct_node_id,
            a.okoz_code, k.label_en AS okoz_label, k.level AS okoz_level,
            b.okoz_breadcrumb,
            a.confidence, a.rationale, a.validated_by, a.assignment_id
        FROM norm_unit n
        JOIN okoz_assignment a ON a.struct_node_id = n.struct_node_id
        JOIN okoz_node k       ON k.code = a.okoz_code
        JOIN breadcrumb b      ON b.code = a.okoz_code
    """)
    con.commit()

    # ---------------------------------------------------------------- report
    n_assigned = con.execute(
        "SELECT count(DISTINCT norm_id) FROM v_okoz_general_part").fetchone()[0]
    n_units = con.execute("SELECT count(*) FROM norm_unit").fetchone()[0]
    log(f"\nokoz_node: {len(nodes)} rows; okoz_assignment: {len(MAPPING)} proposed mappings")
    log(f"coverage: {n_assigned}/{n_units} General Part articles classified\n")

    log("articles per OKOZ institution (level-2 rollup):")
    for code, label, arts in con.execute("""
        SELECT coalesce(k2.code, v.okoz_code), coalesce(k2.label_en, v.okoz_label),
               count(DISTINCT v.norm_id)
        FROM v_okoz_general_part v
        LEFT JOIN okoz_node k2
          ON k2.code = substr(v.okoz_code, 1, 5) || '.00.00' AND k2.level = 2
        GROUP BY 1, 2 ORDER BY 1
    """).fetchall():
        log(f"  {code}  {label:<55} {arts:>3} articles")

    low = con.execute("""
        SELECT struct_node_id, okoz_code, confidence, rationale
        FROM okoz_assignment WHERE confidence <= 0.80 ORDER BY confidence
    """).fetchall()
    log(f"\n{len(low)} judgment-call mapping(s) most in need of the owner's review:")
    for nid, code, conf, why in low:
        log(f"  {nid:<7} -> {code}  ({conf})  {why}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
