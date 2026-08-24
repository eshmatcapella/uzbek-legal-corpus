#!/usr/bin/env python
"""
M4 — Hierarchy explorer for the Civil Code General Part.

    streamlit run app_hierarchy.py

Three axes over one database (corpus.duckdb):
  structural   part > subsection > chapter > § > article
  vertical     realization pyramid: acts below the Code that implement a norm
  classification  OKOZ codes proposed per structural node, validated here

The validation page WRITES to corpus.duckdb (okoz_assignment.validated_by/_at
and okoz_code on owner override).  Everything else is read-only.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "corpus.duckdb"
DOC_GENERAL = -111189

TIER_LABEL = {
    1: "Constitution",
    2: "Code",
    3: "Law",
    4: "Presidential decree",
    5: "Government resolution",
    6: "Departmental order",
    9: "Unclassified type",
}
REL_LABEL = {
    "below": "realizes (from below)",
    "same": "cited by a peer code",
    "above": "cited from above",
    "self": "internal reference",
    "unknown": "citing act's tier unknown",
}
# What the citation was mined from — only 'normative' is the act's own words.
KIND_BADGE = {
    "normative": ("🟩", "the act's own text invokes the Code"),
    "editorial": ("🟦", "LexUZ editorial cross-reference, not the act speaking"),
    "amendment": ("🟨", "drawn from an amendment note (legislative history)"),
}


def excerpt(text: str, around: str, pad: int = 400) -> str:
    """Paragraph-sized window into an act stored as a single block."""
    if not text:
        return ""
    i = text.lower().find((around or "")[:40].lower()) if around else -1
    if i < 0:
        i = text.lower().find("fuqarolik kodeksi")
    if i < 0:
        return text[:pad]
    return ("…" if i > pad else "") + text[max(0, i - pad): i + pad] + "…"


@st.cache_resource
def _connect() -> tuple[duckdb.DuckDBPyConnection, bool]:
    """Read-write if the file is free, else read-only.

    DuckDB allows one writer or many readers per file, so running this app
    alongside app_llc.py would otherwise fail at startup.  Browsing works
    either way; only the validation page needs to write.
    """
    try:
        return duckdb.connect(str(DB_PATH)), True
    except duckdb.IOException:
        return duckdb.connect(str(DB_PATH), read_only=True), False


def get_con() -> duckdb.DuckDBPyConnection:
    return _connect()[0]


def can_write() -> bool:
    return _connect()[1]


def q(sql: str, params: list | None = None):
    return get_con().execute(sql, params or []).fetchall()


def qdf(sql: str, params: list | None = None):
    return get_con().execute(sql, params or []).df()


def display_number(article_number: str, superscript, en_display) -> str:
    if en_display:
        return en_display
    if superscript:
        base = article_number[: -len(str(superscript))]
        sup = str(superscript).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
        return f"Article {base}{sup}"
    return f"Article {article_number}"


def conf_badge(c: float) -> str:
    return "🟢" if c >= 0.9 else ("🟡" if c >= 0.8 else "🟠")


# ---------------------------------------------------------------------------
def page_article() -> None:
    st.header("Article explorer")

    arts = q("""
        SELECT n.norm_id, n.article_number, n.superscript, n.en_display_number,
               coalesce(n.article_title_en, n.article_title_uz, '') AS title
        FROM norm_unit n ORDER BY n.src_row
    """)
    labels = {f"{display_number(a, s, d)} — {t[:70]}": nid for nid, a, s, d, t in arts}
    picked = st.selectbox("Article", list(labels), index=48)  # Article 49 by default
    norm_id = labels[picked]

    meta = q("""
        SELECT g.article_title_uz, g.article_title_en, g.article_text_uz,
               g.article_text_en, g.en_align_status, g.breadcrumb, g.struct_node_id,
               o.okoz_code, o.okoz_breadcrumb, o.confidence, o.validated_by
        FROM v_general_part g
        LEFT JOIN v_okoz_general_part o USING (norm_id)
        WHERE g.norm_id = ?
    """, [norm_id])[0]
    (title_uz, title_en, text_uz, text_en, align, breadcrumb,
     node_id, okoz_code, okoz_bc, okoz_conf, okoz_val) = meta

    st.subheader(title_en or title_uz)
    st.caption(f"**Structure:** {breadcrumb}")
    if okoz_code:
        state = f"validated by {okoz_val}" if okoz_val else "proposed, awaiting validation"
        st.caption(f"**OKOZ:** `{okoz_code}` {okoz_bc}  "
                   f"{conf_badge(okoz_conf)} {okoz_conf} — *{state}*")
    if align and align != "aligned":
        st.warning(f"English text flagged `{align}` — the 2025 translation may not "
                   "match the current Uzbek article. Trust the Uzbek text.")

    col_uz, col_en = st.columns(2)
    with col_uz, st.expander(f"🇺🇿 {title_uz}", expanded=False):
        st.write(text_uz)
    with col_en, st.expander(f"🇬🇧 {title_en or '(no English text)'}", expanded=False):
        st.write(text_en or "*Not present in the 2025 English translation.*")

    st.divider()
    st.subheader("Realization pyramid")

    counts = dict(q("""
        SELECT hierarchy_rel, count(*) FROM v_realization
        WHERE norm_id = ? GROUP BY 1
    """, [norm_id]))
    if not counts:
        st.info("No act in the corpus cites this article.")
        return
    st.caption("  •  ".join(f"{REL_LABEL.get(k, k)}: **{v}**"
                            for k, v in sorted(counts.items())))

    show_all = st.toggle("Include internal and peer-code citations", value=False)
    rels = list(counts) if show_all else [r for r in counts if r == "below"]
    if "below" not in counts and not show_all:
        st.info("No realizing act below the Code cites this article — "
                "turn the toggle on to see its other citations.")

    for tier, in q("""
        SELECT DISTINCT src_tier FROM v_realization
        WHERE norm_id = ? AND hierarchy_rel = ANY(?) ORDER BY src_tier
    """, [norm_id, rels]):
        acts = q("""
            SELECT src_doc_id, src_doc_title, src_doc_date, src_url,
                   count(*) AS n, max(hierarchy_rel) AS rel
            FROM v_realization
            WHERE norm_id = ? AND src_tier = ? AND hierarchy_rel = ANY(?)
            GROUP BY 1, 2, 3, 4 ORDER BY n DESC, src_doc_date
        """, [norm_id, tier, rels])
        st.markdown(f"#### Tier {tier} — {TIER_LABEL.get(tier, '?')} "
                    f"({len(acts)} act{'s' if len(acts) != 1 else ''})")
        for doc_id, doc_title, doc_date, url, n, rel in acts:
            head = f"{doc_title[:110]}  ·  {doc_date or 'no date'}  ·  {n} citation(s)"
            with st.expander(head):
                if url:
                    st.caption(f"[source]({url})  ·  {REL_LABEL.get(rel, rel)}")
                for (ev, qism, conf, kind, amb, p_no, p_title,
                     p_text, p_blob) in q("""
                    SELECT evidence_clean, dst_qism, confidence, evidence_kind,
                           dst_ambiguous, src_prov_number, src_prov_title,
                           src_prov_text, src_prov_is_blob
                    FROM v_realization
                    WHERE norm_id = ? AND src_doc_id = ? AND hierarchy_rel = ANY(?)
                    ORDER BY (evidence_kind <> 'normative'), confidence DESC
                """, [norm_id, doc_id, rels]):
                    flags = (f" · part: {qism}" if qism else "") + \
                            (" · ⚠ ambiguous superscript" if amb else "")
                    badge, why = KIND_BADGE.get(kind, ("", ""))
                    st.markdown(f"{badge} **{kind}** `{conf}`{flags}")
                    st.caption(why)
                    # The realizing provision itself, not just the citation window.
                    if p_text:
                        label = (f"Implementing provision — art. {p_no}"
                                 + (f". {p_title}" if p_title else "")
                                 if p_no and not p_blob
                                 else "Implementing provision (excerpt)")
                        with st.expander(label):
                            st.write(p_text if not p_blob else excerpt(p_text, ev))
                    st.caption(f"cited as: …{ev}…")

    # citations that pin the chapter/section rather than the article
    chain = q("""
        WITH RECURSIVE up(node_id, parent_id) AS (
            SELECT node_id, parent_id FROM struct_node WHERE node_id = ?
            UNION ALL
            SELECT s.node_id, s.parent_id FROM struct_node s
            JOIN up ON s.node_id = up.parent_id
        ) SELECT node_id FROM up
    """, [node_id])
    node_ids = [r[0] for r in chain]
    struct_hits = q("""
        SELECT kind, label_en, count(DISTINCT src_doc_id), count(*)
        FROM v_realization_struct WHERE node_id = ANY(?) GROUP BY 1, 2
    """, [node_ids])
    if struct_hits:
        st.markdown("#### Citations to this article's chapter/section as a whole")
        for kind, label, n_acts, n_edges in struct_hits:
            st.caption(f"{kind} *{label}*: {n_acts} act(s), {n_edges} citation(s)")


# ---------------------------------------------------------------------------
def page_structure() -> None:
    st.header("Structural tree")
    st.caption("The whole Code for orientation; only the General Part "
               "(Articles 1–385) carries data in this corpus build.")

    nodes = q("""
        SELECT node_id, kind, number, label_en, parent_id, depth,
               art_from, art_to, n_units
        FROM struct_node
    """)
    by_id = {n[0]: n for n in nodes}
    kids: dict[str | None, list] = {}
    for n in nodes:
        kids.setdefault(n[4], []).append(n)

    def sort_key(n):
        if n[6] is not None:
            return n[6]
        desc = [sort_key(c) for c in kids.get(n[0], [])]
        return min(desc) if desc else 10_000

    real_by_node = dict(q("""
        SELECT n.struct_node_id, count(DISTINCT e.src_doc_id)
        FROM link_edge e JOIN norm_unit n ON n.norm_id = e.dst_norm_id
        WHERE e.hierarchy_rel = 'below' GROUP BY 1
    """))
    okoz_by_node = {r[0]: (r[1], r[2]) for r in q(
        "SELECT struct_node_id, okoz_code, validated_by FROM okoz_assignment")}

    lines: list[str] = []

    def walk(parent, indent=0):
        for n in sorted(kids.get(parent, []), key=sort_key):
            nid, kind, num, label, _, _, lo, hi, units = n
            rng = f" (art. {lo}–{hi})" if lo else ""
            badge = ""
            if units:
                badge += f" · **{units}** articles"
                if nid in real_by_node:
                    badge += f" · {real_by_node[nid]} realizing acts"
            if nid in okoz_by_node:
                code, val = okoz_by_node[nid]
                badge += f" · `{code}`{'✅' if val else ' *(proposed)*'}"
            name = {"part": f"**Part {num}. {label}**",
                    "subsection": f"**Subsection {num}. {label}**",
                    "chapter": f"Chapter {num}. {label}",
                    "section": f"§ {num}. {label}"}[kind]
            lines.append("&nbsp;" * indent * 4 + name + rng + badge)
            walk(nid, indent + 1)

    walk(None)
    st.markdown("<br>".join(lines), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
def page_okoz() -> None:
    st.header("OKOZ classifier")
    spheres = q("SELECT code, label_en FROM okoz_node WHERE level = 1 ORDER BY code")
    sphere = st.selectbox("Sphere", [f"{c}  {l}" for c, l in spheres],
                          index=2)  # 03 CIVIL LEGISLATION
    prefix = sphere[:2]

    assigned = {}
    for code, nid, lbl, lo, hi, val in q("""
        SELECT a.okoz_code, s.node_id, s.label_en,
               coalesce(s.art_from, (SELECT min(c.art_from) FROM struct_node c
                                     WHERE c.parent_id = s.node_id)) AS art_from,
               coalesce(s.art_to,   (SELECT max(c.art_to) FROM struct_node c
                                     WHERE c.parent_id = s.node_id)) AS art_to,
               a.validated_by
        FROM okoz_assignment a JOIN struct_node s ON s.node_id = a.struct_node_id
    """):
        assigned.setdefault(code, []).append((nid, lbl, lo, hi, val))

    rows = q("""
        SELECT code, level, label_en, see_also FROM okoz_node
        WHERE code LIKE ? ORDER BY ordinal
    """, [prefix + ".%"])
    lines = []
    for code, level, label, see_also in rows:
        pad = "&nbsp;" * (level - 1) * 5
        line = f"{pad}`{code}` {'**' + label + '**' if level <= 2 else label}"
        if see_also:
            line += f" <sub>see also {see_also}</sub>"
        for nid, lbl, lo, hi, val in assigned.get(code, []):
            mark = "✅" if val else "🟨 proposed"
            line += (f"<br>{pad}&nbsp;&nbsp;&nbsp;↳ {mark} CC {nid}: "
                     f"*{lbl}* (art. {lo}–{hi})")
        lines.append(line)
    st.markdown("<br>".join(lines), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
def page_validate() -> None:
    st.header("Validate OKOZ mappings")
    st.caption("Every mapping was proposed by title correspondence between the "
               "Code's chapters and the classifier. Approving stamps your name; "
               "re-mapping overrides the code and validates in one step. "
               "Decisions persist in corpus.duckdb.")

    validator = st.text_input("Validator name", value="Dilmurod")
    con = get_con()
    if not can_write():
        st.error("The database is open read-only because another process holds it "
                 "(the LLC dossier app, most likely). Decisions below are shown but "
                 "cannot be saved — stop the other app and reload this page.")

    pending, done = q("SELECT count(*) FILTER (WHERE validated_by IS NULL), "
                      "count(*) FILTER (WHERE validated_by IS NOT NULL) "
                      "FROM okoz_assignment")[0]
    c1, c2 = st.columns(2)
    c1.metric("Awaiting validation", pending)
    c2.metric("Validated", done)

    if pending and st.button(f"Approve all {pending} pending with confidence ≥ 0.90"):
        con.execute("""
            UPDATE okoz_assignment SET validated_by = ?, validated_at = now()
            WHERE validated_by IS NULL AND confidence >= 0.90
        """, [validator])
        con.commit()
        st.rerun()

    okoz_options = {f"{c}  {l}": c for c, l in q(
        "SELECT code, label_en FROM okoz_node WHERE code LIKE '03.%' ORDER BY code")}

    rows = q("""
        SELECT a.assignment_id, a.struct_node_id, s.label_en,
               coalesce(s.art_from, (SELECT min(c.art_from) FROM struct_node c
                                     WHERE c.parent_id = s.node_id)) AS art_from,
               coalesce(s.art_to,   (SELECT max(c.art_to) FROM struct_node c
                                     WHERE c.parent_id = s.node_id)) AS art_to,
               a.okoz_code, k.label_en, a.confidence, a.rationale,
               a.validated_by, a.method
        FROM okoz_assignment a
        JOIN struct_node s ON s.node_id = a.struct_node_id
        JOIN okoz_node k   ON k.code = a.okoz_code
        ORDER BY a.validated_by IS NOT NULL, a.confidence, art_from
    """)
    for (aid, nid, s_label, lo, hi, code, k_label, conf, why, val, method) in rows:
        head = (f"{'✅' if val else conf_badge(conf)} {nid} · {s_label} "
                f"(art. {lo}–{hi})  →  {code} {k_label}")
        with st.expander(head, expanded=False):
            st.markdown(f"confidence `{conf}` · method `{method}`")
            st.caption(why)
            if val:
                st.success(f"Validated by {val}.")
                if st.button("Withdraw validation", key=f"un{aid}"):
                    con.execute("UPDATE okoz_assignment SET validated_by = NULL, "
                                "validated_at = NULL WHERE assignment_id = ?", [aid])
                    con.commit()
                    st.rerun()
            else:
                bcol, rcol = st.columns([1, 3])
                if bcol.button("Approve", key=f"ap{aid}", type="primary"):
                    con.execute("UPDATE okoz_assignment SET validated_by = ?, "
                                "validated_at = now() WHERE assignment_id = ?",
                                [validator, aid])
                    con.commit()
                    st.rerun()
                with rcol:
                    alt = st.selectbox("Re-map to", list(okoz_options),
                                       index=list(okoz_options.values()).index(code),
                                       key=f"alt{aid}", label_visibility="collapsed")
                    if st.button("Re-map & validate", key=f"rm{aid}"):
                        con.execute("""
                            UPDATE okoz_assignment
                            SET okoz_code = ?, method = 'owner_override',
                                confidence = 1.0, validated_by = ?, validated_at = now()
                            WHERE assignment_id = ?
                        """, [okoz_options[alt], validator, aid])
                        con.commit()
                        st.rerun()


# ---------------------------------------------------------------------------
def page_health() -> None:
    st.header("Corpus health")
    m = st.columns(5)
    m[0].metric("Acts", f"{q('SELECT count(*) FROM act')[0][0]:,}")
    m[1].metric("General Part articles", q("SELECT count(*) FROM norm_unit")[0][0])
    m[2].metric("Citation edges", f"{q('SELECT count(*) FROM link_edge')[0][0]:,}")
    m[3].metric("OKOZ nodes", f"{q('SELECT count(*) FROM okoz_node')[0][0]:,}")
    m[4].metric("With English text",
                q("SELECT count(*) FROM norm_unit WHERE article_text_en IS NOT NULL")[0][0])

    st.subheader("Coverage")
    cov, below = q("""
        SELECT count(DISTINCT dst_norm_id),
               count(DISTINCT CASE WHEN hierarchy_rel = 'below' THEN dst_norm_id END)
        FROM link_edge WHERE dst_doc_id = ? AND dst_norm_id IS NOT NULL
    """, [DOC_GENERAL])[0]
    st.write(f"- **{cov}/386** articles cited by at least one act; "
             f"**{below}/386** have a realizing act below the Code")
    st.write("- most-realized articles:")
    st.dataframe(qdf("""
        SELECT n.article_number AS article,
               coalesce(n.article_title_en, n.article_title_uz) AS title,
               count(DISTINCT e.src_doc_id) AS realizing_acts
        FROM link_edge e JOIN norm_unit n ON n.norm_id = e.dst_norm_id
        WHERE e.hierarchy_rel = 'below'
        GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10
    """), hide_index=True)

    st.subheader("Findings that need a lawyer's eye")
    st.write("**Dangling references** — acts citing General Part articles the "
             "2026 corpus no longer contains (repealed):")
    st.dataframe(qdf("""
        SELECT e.dst_article_number AS cited_article,
               count(*) AS citations, count(DISTINCT e.src_doc_id) AS acts,
               min(a.doc_title) AS example_act
        FROM link_edge e JOIN act a ON a.doc_id = e.src_doc_id
        WHERE e.dst_dangling GROUP BY 1 ORDER BY 2 DESC
    """), hide_index=True)
    st.write("**Version drift** — English (2025) vs Uzbek (2026):")
    st.dataframe(qdf("""
        SELECT en_display_number AS article, article_title_uz, article_title_en,
               en_align_status, en_align_note
        FROM norm_unit WHERE en_align_status <> 'aligned'
    """), hide_index=True)


# ---------------------------------------------------------------------------
st.set_page_config(page_title="Civil Code hierarchy", page_icon="⚖️", layout="wide")
st.sidebar.title("⚖️ Civil Code of Uzbekistan")
st.sidebar.caption("General Part · three-axis hierarchy explorer")
PAGES = {
    "Article explorer": page_article,
    "Structural tree": page_structure,
    "OKOZ classifier": page_okoz,
    "Validate OKOZ mappings": page_validate,
    "Corpus health": page_health,
}
PAGES[st.sidebar.radio("Page", list(PAGES))]()
