"""End-to-end demo of the LLC slice, printed as a walkthrough."""
import sys
import duckdb

sys.stdout.reconfigure(encoding="utf-8")
con = duckdb.connect(r"C:\uzbek-legal-corpus\corpus.duckdb", read_only=True)
W = 78


def rule(t=""):
    print("\n" + "=" * W)
    if t:
        print(t)
        print("=" * W)


rule("DEMO 1 — the LLC skeleton, derived from the current law's own chapters")
for n, label, a, b, c, f in con.execute(
        "SELECT * FROM llc_stage ORDER BY stage_no").fetchall():
    print(f"  {n}. {label[:52]:<52} arts {a:>2}-{b:<3} CC:{f}")

rule("DEMO 2 — follow ONE norm down three tiers (charter capital)")
cc = con.execute("""SELECT article_number, article_title, substr(article_text,1,300)
                    FROM llc_norm WHERE norm_key='F3-62'""").fetchone()
print(f"  TIER 2  Civil Code art. {cc[0]} — {cc[1]}")
print(f"          {cc[2][:260]}…")
print(f"\n  TIER 3  LLC Law, chapter 3 — the stage that specialises it:")
for a, t in con.execute("""SELECT article_number, article_title FROM llc_norm
        WHERE stage_no=3 AND layer='special' ORDER BY CAST(article_number AS INT) LIMIT 6""").fetchall():
    print(f"            art. {a:<3} {t[:62]}")
print("            … 9 more")

rule("DEMO 3 — THE FIX: implementing acts now show a NORM, not a pointer")
row = con.execute("""
    SELECT src_doc_title, evidence_kind, confidence, src_prov_number,
           src_prov_title, src_prov_text, evidence_clean
    FROM v_llc_realization
    WHERE cc_article='53' AND src_prov_number IS NOT NULL AND NOT is_whole_act_blob
      AND derived_status <> 'superseded'
    ORDER BY confidence DESC LIMIT 1""").fetchone()
print(f"  citing act : {row[0][:66]}")
print(f"  evidence   : {row[1]} (confidence {row[2]})")
print(f"\n  BEFORE — all the UI could show was the citation window:")
print(f"    …{row[6][:150]}…")
print(f"\n  AFTER  — the implementing provision itself:")
print(f"    art. {row[3]}. {row[4]}")
print(f"    {(row[5] or '')[:400]}…")

rule("DEMO 4 — evidence is now labelled by what it was mined from")
for k, n, a, c in con.execute("""
        SELECT evidence_kind, count(*), count(DISTINCT src_doc_id), round(avg(confidence),2)
        FROM link_edge WHERE hierarchy_rel='below' GROUP BY 1 ORDER BY 2 DESC""").fetchall():
    print(f"  {k:<10} {n:>5} edges  {a:>4} acts  avg confidence {c}")
n_ed = con.execute("""SELECT count(*) FROM link_edge WHERE hierarchy_rel='below'
    AND (evidence ILIKE '%Oldingi tahrirga%' OR evidence ILIKE '%LexUZ sharhi%')""").fetchone()[0]
print(f"\n  {n_ed} of these had raw evidence that was pure LexUZ apparatus —")
print("  previously displayed verbatim as if it were the norm.")

rule("DEMO 5 — currency: the LLC's governing law changed in April 2026")
for d, dt, st_, by, t in con.execute("""
        SELECT doc_id, doc_date, derived_status, repealed_by, coalesce(repealed_by_title,'')
        FROM v_act_currency WHERE doc_id IN (-22525,-8151376) ORDER BY doc_date""").fetchall():
    n = con.execute("SELECT n_articles FROM act WHERE doc_id=?", [d]).fetchone()[0]
    mark = "SUPERSEDED" if st_ == "superseded" else "current"
    print(f"  {dt}  {d:>9}  {n:>2} articles  -> {mark}")
    if by:
        print(f"             repealed by {t[:50]} ({by})")
print(f"\n  corpus-wide: {con.execute(chr(34)*0 + 'SELECT count(DISTINCT doc_id) FROM v_act_currency WHERE derived_status=' + chr(39) + 'superseded' + chr(39)).fetchone()[0]} acts provably superseded,")
print(f"  {con.execute('''SELECT count(*) FROM link_edge e JOIN v_act_currency c ON c.doc_id=e.src_doc_id WHERE c.derived_status='superseded' AND e.hierarchy_rel='below' ''').fetchone()[0]} realization edges come from repealed law (now flagged).")

rule("DEMO 6 — the Code's company-form articles that no longer exist")
for a, n, k in con.execute("""
        SELECT dst_article_number, count(*), count(DISTINCT src_doc_id) FROM link_edge
        WHERE dst_dangling AND dst_article_number IN ('63','65','66','70','71','72')
        GROUP BY 1 ORDER BY CAST(dst_article_number AS INT)""").fetchall():
    print(f"  CC art. {a}: still cited {n}x by {k} acts — repealed when the special laws took over")
con.close()
print()
