#!/usr/bin/env python
"""
LLC dossier — one institution, all three axes.

    streamlit run app_llc.py

Narrower than app_hierarchy.py on purpose: instead of navigating 386 General
Part articles, this follows a single institution (masʼuliyati cheklangan
jamiyat) down the hierarchy, stage by stage, using the Civil Code as its
foundation and the LLC Law's own chapters as the skeleton.
"""
from __future__ import annotations

import re
from pathlib import Path

import duckdb
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "corpus.duckdb"
LLC_LAW_CURRENT = -8151376
LLC_LAW_PRIOR = -22525

TIER_LABEL = {1: "Constitution", 2: "Code", 3: "Law", 4: "Presidential decree",
              5: "Government resolution", 6: "Departmental order", 9: "Unclassified"}
KIND_BADGE = {
    "normative": ("🟩", "the act's own words invoke the Code"),
    "editorial": ("🟦", "LexUZ editorial cross-reference, not the act speaking"),
    "amendment": ("🟨", "drawn from an amendment note (legislative history)"),
}


@st.cache_resource
def get_con():
    return duckdb.connect(str(DB_PATH), read_only=True)


def q(sql: str, params: list | None = None):
    return get_con().execute(sql, params or []).fetchall()


def qdf(sql: str, params: list | None = None):
    return get_con().execute(sql, params or []).df()


def excerpt(text: str, around: str, pad: int = 400) -> str:
    """Paragraph-sized window of a whole-act blob around the citation."""
    if not text:
        return ""
    i = text.lower().find((around or "")[:40].lower()) if around else -1
    if i < 0:
        i = text.lower().find("fuqarolik kodeksi")
    if i < 0:
        return text[:pad]
    return ("…" if i > pad else "") + text[max(0, i - pad): i + pad] + "…"


def status_chip(derived: str) -> str:
    return ("🔴 **superseded** — repealed by a later act"
            if derived == "superseded" else "🟢 no repeal found")


# ---------------------------------------------------------------------------
def page_skeleton() -> None:
    st.header("LLC skeleton")
    st.caption("The stages are the current LLC Law's own chapters. Under each, the "
               "Civil Code articles that stage rests on — the general norm the "
               "special law specialises.")

    for s_no, label, a_from, a_to, n_art, n_f in q(
            "SELECT * FROM llc_stage ORDER BY stage_no"):
        with st.expander(f"**{s_no}. {label}** — LLC Law arts. {a_from}–{a_to} "
                         f"({n_art} articles, {n_f} Code foundations)", expanded=s_no == 1):
            found = q("""
                SELECT article_number, article_title, article_title_en, rationale
                FROM llc_norm WHERE stage_no = ? AND layer = 'foundation'
                ORDER BY CAST(article_number AS INT)
            """, [s_no])
            if found:
                st.markdown("**Civil Code foundation**")
                for a, t_uz, t_en, why in found:
                    st.markdown(f"- **CC art. {a}** — {t_uz}"
                                + (f" *({t_en})*" if t_en else ""))
                    st.caption(f"  ↳ {why}")
            else:
                st.caption("No distinct General Part anchor for this stage.")

            st.markdown("**LLC Law articles**")
            for a, t in q("""
                SELECT article_number, article_title FROM llc_norm
                WHERE stage_no = ? AND layer = 'special'
                ORDER BY CAST(article_number AS INT)
            """, [s_no]):
                st.markdown(f"- art. {a} — {t}")


# ---------------------------------------------------------------------------
def page_norm() -> None:
    st.header("Follow one norm down the hierarchy")

    stages = {f"{n}. {l}": n for n, l in q(
        "SELECT stage_no, stage_label FROM llc_stage ORDER BY stage_no")}
    stage = stages[st.selectbox("Stage", list(stages))]

    founds = q("""
        SELECT article_number, article_title, article_title_en, rationale,
               article_text, cc_norm_id
        FROM llc_norm WHERE stage_no = ? AND layer = 'foundation'
        ORDER BY CAST(article_number AS INT)
    """, [stage])
    if not founds:
        st.info("This stage has no distinct Civil Code anchor — it is governed "
                "by the special law alone.")
        return
    labels = {f"CC art. {a} — {t}": a for a, t, _, _, _, _ in founds}
    art = labels[st.selectbox("Civil Code foundation article", list(labels))]
    rec = next(f for f in founds if f[0] == art)

    st.subheader(f"Tier 2 · Civil Code art. {art}")
    st.markdown(f"**{rec[1]}**" + (f" — *{rec[2]}*" if rec[2] else ""))
    st.caption(f"Why it founds this stage: {rec[3]}")
    with st.expander("Read the Code article"):
        st.write(rec[4])

    st.divider()
    st.subheader(f"Tier 3 · LLC Law — the stage that specialises it")
    for a, t, txt in q("""
        SELECT article_number, article_title, article_text FROM llc_norm
        WHERE stage_no = ? AND layer = 'special' ORDER BY CAST(article_number AS INT)
    """, [stage]):
        with st.expander(f"art. {a} — {t}"):
            st.write(txt)

    st.divider()
    st.subheader("Below · acts implementing this Code article")

    rows = q("""
        SELECT src_doc_id, src_doc_title, src_tier, doc_date, source_url,
               evidence_kind, confidence, evidence_clean,
               src_prov_number, src_prov_title, src_prov_text, is_whole_act_blob,
               derived_status, repealed_by_title
        FROM v_llc_realization WHERE cc_article = ?
        ORDER BY (derived_status = 'superseded'), src_tier,
                 (evidence_kind <> 'normative'), confidence DESC
    """, [art])
    if not rows:
        st.info("No act below the Code cites this article.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Implementing acts", len({r[0] for r in rows}))
    c2.metric("Normative citations", sum(1 for r in rows if r[5] == "normative"))
    c3.metric("Superseded acts", len({r[0] for r in rows if r[12] == "superseded"}))

    hide_dead = st.toggle("Hide superseded acts", value=True)
    only_norm = st.toggle("Only the act's own words (hide editorial pointers)", value=False)

    shown = [r for r in rows
             if not (hide_dead and r[12] == "superseded")
             and not (only_norm and r[5] != "normative")]
    if not shown:
        st.warning("Every citation to this article was filtered out — "
                   "turn a filter off to see them.")
        return

    for tier in sorted({r[2] for r in shown}):
        st.markdown(f"### Tier {tier} — {TIER_LABEL.get(tier, '?')}")
        for r in [x for x in shown if x[2] == tier]:
            (doc_id, title, _, date, url, kind, conf, ev,
             p_no, p_title, p_text, is_blob, derived, rep_by) = r
            badge, why = KIND_BADGE.get(kind, ("", ""))
            dead = " 🔴" if derived == "superseded" else ""
            head = f"{badge} {title[:95]} · {date or 'no date'}{dead}"
            with st.expander(head):
                if derived == "superseded":
                    st.error(f"This act was repealed by: {rep_by or 'a later act'}. "
                             "It is not current law.")
                st.caption(f"{badge} **{kind}** — {why} · confidence `{conf}`"
                           + (f" · [source]({url})" if url else ""))

                # The realizing norm itself.
                if p_no and not is_blob:
                    st.markdown(f"**Implementing provision — art. {p_no}"
                                + (f". {p_title}" if p_title else "") + "**")
                    st.write(p_text)
                elif p_text:
                    st.markdown("**Implementing provision** *(the act is stored as a "
                                "single block; excerpt around the citation)*")
                    st.write(excerpt(p_text, ev))
                else:
                    st.caption("No provision text stored for this citation.")

                st.markdown("**Citation as found**")
                st.caption(f"…{ev}…")


# ---------------------------------------------------------------------------
def page_currency() -> None:
    st.header("Is this still law?")
    st.warning("The corpus marks **all 24,267 acts** `in-force` — the status field "
               "carries no information. Currency below is derived from repeal "
               "clauses in the acts themselves (“… oʻz kuchini yoʻqotgan deb "
               "topilsin”), matched by date and quoted title.")

    n_sup, n_items, n_actors = q("""
        SELECT (SELECT count(DISTINCT doc_id) FROM v_act_currency
                WHERE derived_status = 'superseded'),
               (SELECT count(*) FROM repeal_clause),
               (SELECT count(DISTINCT src_doc_id) FROM repeal_clause)
    """)[0]
    c = st.columns(3)
    c[0].metric("Acts provably superseded", n_sup)
    c[1].metric("Repeal items extracted", n_items)
    c[2].metric("Acts doing the repealing", n_actors)

    st.subheader("The LLC's own governing law")
    for doc_id, date, derived, rep_by, rep_title in q("""
        SELECT doc_id, doc_date, derived_status, repealed_by,
               coalesce(repealed_by_title, '')
        FROM v_act_currency WHERE doc_id IN (?, ?) ORDER BY doc_date
    """, [LLC_LAW_PRIOR, LLC_LAW_CURRENT]):
        n_art = q("SELECT n_articles FROM act WHERE doc_id = ?", [doc_id])[0][0]
        st.markdown(f"**{date}** · `{doc_id}` · {n_art} articles — {status_chip(derived)}")
        if rep_by:
            st.caption(f"repealed by {rep_title[:70]} (`{rep_by}`)")
            ev = q("""SELECT evidence FROM repeal_clause WHERE dst_doc_id = ? LIMIT 1""",
                   [doc_id])
            if ev:
                st.caption(f"…{ev[0][0][:320]}…")

    st.subheader("Superseded acts still feeding the realization graph")
    st.caption("These acts were repealed, yet still contribute 'realizes' edges — "
               "without the repeal layer they would read as current law.")
    st.dataframe(qdf("""
        SELECT a.doc_title AS act, a.doc_date AS dated, count(*) AS edges,
               max(c.repealed_by_title) AS repealed_by
        FROM link_edge e JOIN act a ON a.doc_id = e.src_doc_id
        JOIN v_act_currency c ON c.doc_id = e.src_doc_id
        WHERE c.derived_status = 'superseded' AND e.hierarchy_rel = 'below'
        GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 15
    """), hide_index=True, width="stretch")

    st.subheader("Company-form articles the Code no longer has")
    st.caption("Articles 63, 65, 66, 70, 71 and 72 governed company forms and were "
               "repealed as the special laws took over — but acts still cite them.")
    st.dataframe(qdf("""
        SELECT e.dst_article_number AS cc_article, count(*) AS citations,
               count(DISTINCT e.src_doc_id) AS acts, min(a.doc_title) AS example_act
        FROM link_edge e JOIN act a ON a.doc_id = e.src_doc_id
        WHERE e.dst_dangling AND e.dst_article_number IN ('63','65','66','70','71','72')
        GROUP BY 1 ORDER BY CAST(cc_article AS INT)
    """), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
def page_evidence() -> None:
    st.header("Evidence quality")
    st.caption("Every realization edge is labelled by what it was mined from. Only "
               "`normative` evidence is the act itself invoking the Code.")

    st.dataframe(qdf("""
        SELECT evidence_kind AS kind, count(*) AS edges,
               count(DISTINCT src_doc_id) AS acts, round(avg(confidence), 3) AS avg_conf
        FROM link_edge WHERE hierarchy_rel = 'below'
        GROUP BY 1 ORDER BY 2 DESC
    """), hide_index=True, width="stretch")

    st.subheader("Why this distinction was needed")
    st.markdown(
        "A LexUZ editorial cross-reference reads like this in the raw field:\n\n"
        "> `Oldingi tahrirga qarang. LexUZ sharhiQarang: Oʻzbekiston Respublikasi "
        "Fuqarolik kodeksining 49-moddasi.`\n\n"
        "That is the site's apparatus — a version-history link plus an editor's "
        "pointer. It says two provisions are related; it is **not** a legal norm, "
        "and it is not the act speaking. The dossier now shows the citing act's "
        "actual article text alongside it."
    )
    n_app = q("""
        SELECT count(*) FROM link_edge WHERE hierarchy_rel = 'below'
          AND (evidence ILIKE '%Oldingi tahrirga qarang%' OR evidence ILIKE '%LexUZ sharhi%')
    """)[0][0]
    tot = q("SELECT count(*) FROM link_edge WHERE hierarchy_rel = 'below'")[0][0]
    st.metric("Realization edges whose raw evidence was editorial apparatus",
              f"{n_app} of {tot}", f"{100*n_app/tot:.0f}% now labelled and cleaned")

    st.subheader("Implementing provisions now available")
    st.dataframe(qdf("""
        SELECT CASE WHEN is_whole_act_blob THEN 'whole-act blob (excerpted)'
                    ELSE 'single article (shown in full)' END AS provision_form,
               count(*) AS rows, round(avg(text_len)) AS avg_chars
        FROM src_provision GROUP BY 1 ORDER BY 2 DESC
    """), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
def page_acts() -> None:
    st.header("Acts implementing the LLC")
    st.caption("Two independent routes: an act either cites a Civil Code article "
               "the LLC rests on, or names the LLC Law itself.")

    route = st.radio("Route", ["cites_cc_foundation", "names_llc_law"], horizontal=True)
    hide_dead = st.toggle("Hide superseded", value=True)
    rows = q("""
        SELECT tier, doc_title, doc_date, n_hits, stages, derived_status, evidence
        FROM llc_implementing_act
        WHERE route = ? AND (? OR derived_status <> 'superseded')
        ORDER BY tier, n_hits DESC
    """, [route, not hide_dead])
    st.write(f"**{len(rows)}** acts")
    for tier in sorted({r[0] for r in rows}):
        st.markdown(f"### Tier {tier} — {TIER_LABEL.get(tier, '?')}")
        for t_, title, date, n, stages, derived, ev in [r for r in rows if r[0] == tier]:
            dead = " 🔴" if derived == "superseded" else ""
            with st.expander(f"{title[:95]} · {date or '—'} · {n} hit(s){dead}"):
                if stages:
                    st.caption(f"touches LLC stage(s): {stages}")
                if derived == "superseded":
                    st.error("Superseded by a later act — not current law.")
                st.caption(f"…{ev}…")


# ---------------------------------------------------------------------------
st.set_page_config(page_title="LLC dossier", page_icon="🏛️", layout="wide")
st.sidebar.title("🏛️ Limited Liability Company")
st.sidebar.caption("Masʼuliyati cheklangan jamiyat · OKOZ 03.03.05.04")
st.sidebar.markdown("---")
st.sidebar.caption("A single-institution slice built on the Civil Code General "
                   "Part foundation. The wider explorer is `app_hierarchy.py`.")
PAGES = {
    "LLC skeleton": page_skeleton,
    "Follow a norm down": page_norm,
    "Implementing acts": page_acts,
    "Is this still law?": page_currency,
    "Evidence quality": page_evidence,
}
PAGES[st.sidebar.radio("Page", list(PAGES))]()
