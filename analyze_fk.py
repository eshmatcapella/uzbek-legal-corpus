import sys, duckdb
sys.stdout.reconfigure(encoding='utf-8')
P = 'c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet'
conn = duckdb.connect()

# Civil Code doc_ids: -180552 (new, 811 articles) and -111189 (old, 386 articles)
CC_IDS = "(-180552, -111189)"

print("=== 1. PART (BOʻLIM) structure of Civil Code ===")
for r in conn.execute(f"""
    SELECT doc_id, part, COUNT(*) as cnt 
    FROM read_parquet('{P}') 
    WHERE doc_id IN {CC_IDS}
    GROUP BY doc_id, part 
    ORDER BY doc_id DESC, part
""").fetchall():
    print(f"  doc_id={r[0]} | {r[2]:>4} articles | {r[1]}")

print("\n=== 2. CHAPTER (bob) structure of NEWER Civil Code (-180552) ===")
for r in conn.execute(f"""
    SELECT part, chapter, COUNT(*) as cnt 
    FROM read_parquet('{P}') 
    WHERE doc_id = -180552
    GROUP BY part, chapter 
    ORDER BY part, chapter
""").fetchall():
    print(f"  {r[2]:>3} arts | {r[0][:40] if r[0] else '(no part)':<40} | {r[1]}")

print("\n=== 3. Cross-references count in Civil Code ===")
cr = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{P}') WHERE doc_id IN {CC_IDS} AND cross_references IS NOT NULL AND TRIM(cross_references) != ''").fetchone()[0]
am = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{P}') WHERE doc_id IN {CC_IDS} AND amendment_note IS NOT NULL AND TRIM(amendment_note) != ''").fetchone()[0]
print(f"Articles with cross_references: {cr}")
print(f"Articles with amendment_note: {am}")

print("\n=== 4. Sample cross_references from Civil Code ===")
for r in conn.execute(f"""
    SELECT article_number, article_title, LEFT(cross_references, 300) 
    FROM read_parquet('{P}') 
    WHERE doc_id = -180552 AND cross_references IS NOT NULL AND TRIM(cross_references) != ''
    LIMIT 8
""").fetchall():
    print(f"  Art {r[0]} ({r[1]}): {r[2]}")
    print()

print("\n=== 5. OKOZ codes for Civil Code ===")
for r in conn.execute(f"SELECT okoz_codes, COUNT(*) FROM read_parquet('{P}') WHERE doc_id IN {CC_IDS} GROUP BY okoz_codes").fetchall():
    print(r)

print("\n=== 6. How many OTHER acts reference 'Fuqarolik kodeksi' (by doc_type) ===")
for r in conn.execute(f"""
    SELECT doc_type, COUNT(DISTINCT doc_id) as distinct_acts, COUNT(*) as total_articles 
    FROM read_parquet('{P}') 
    WHERE doc_id NOT IN {CC_IDS} AND LOWER(article_text) LIKE '%fuqarolik kodeksi%'
    GROUP BY doc_type 
    ORDER BY total_articles DESC
""").fetchall():
    print(f"  {r[0]:<15} | {r[1]:>4} acts | {r[2]:>5} articles")

print("\n=== 7. Sample General Part articles (Umumiy qism) ===")
for r in conn.execute(f"""
    SELECT article_number, article_title, LEFT(article_text, 200), part, chapter 
    FROM read_parquet('{P}') 
    WHERE doc_id = -180552 AND part LIKE '%UMUMIY%'
    ORDER BY CAST(REPLACE(article_number,'-','') AS INTEGER)
    LIMIT 8
""").fetchall():
    print(f"  Art {r[0]}: {r[1]}")
    print(f"    Part: {r[3]}")
    print(f"    Chapter: {r[4]}")
    print(f"    Text: {r[2][:120]}...")
    print()

print("\n=== 8. Sample Specific Part articles ===")
for r in conn.execute(f"""
    SELECT article_number, article_title, LEFT(article_text, 150), part, chapter 
    FROM read_parquet('{P}') 
    WHERE doc_id = -180552 AND part NOT LIKE '%UMUMIY%' AND part != ''
    ORDER BY CAST(REPLACE(REPLACE(article_number,'-',''),'1','1') AS INTEGER)
    LIMIT 8
""").fetchall():
    print(f"  Art {r[0]}: {r[1]}")
    print(f"    Part: {r[3]}")
    print(f"    Chapter: {r[4]}")
    print()
