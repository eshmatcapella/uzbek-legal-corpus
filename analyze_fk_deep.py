import sys, duckdb
sys.stdout.reconfigure(encoding='utf-8')
P = 'c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet'
conn = duckdb.connect()

# The OLD Civil Code (-111189) has the proper part structure
# The NEW Civil Code (-180552) has 811 articles in the Specific Part (no part label)

print("=== OLD Civil Code (-111189): General Part sample ===")
for r in conn.execute(f"""
    SELECT article_number, article_title, LEFT(article_text, 180), part, chapter 
    FROM read_parquet('{P}') 
    WHERE doc_id = -111189 AND part LIKE '%UMUMIY%'
    ORDER BY CAST(article_number AS INTEGER)
    LIMIT 10
""").fetchall():
    print(f"  Art {r[0]}: {r[1]}")
    print(f"    {r[3]} | {r[4]}")
    print(f"    {r[2][:120]}...")
    print()

print("=== OLD Civil Code (-111189): Chapters list ===")
for r in conn.execute(f"""
    SELECT part, chapter, MIN(CAST(article_number AS INTEGER)) as first_art, MAX(CAST(article_number AS INTEGER)) as last_art, COUNT(*) as cnt
    FROM read_parquet('{P}') 
    WHERE doc_id = -111189 AND article_number != ''
    GROUP BY part, chapter 
    ORDER BY first_art
""").fetchall():
    print(f"  Arts {r[2]}-{r[3]} ({r[4]} arts) | {r[0][:50]} | {r[1]}")

print("\n=== NEW Civil Code (-180552): Chapters list ===")
for r in conn.execute(f"""
    SELECT chapter, MIN(CAST(REPLACE(article_number,'-1','') AS INTEGER)) as first_art, 
           MAX(CAST(REPLACE(article_number,'-1','') AS INTEGER)) as last_art, 
           COUNT(*) as cnt
    FROM read_parquet('{P}') 
    WHERE doc_id = -180552 AND article_number != ''
    GROUP BY chapter 
    ORDER BY first_art
""").fetchall():
    print(f"  Arts ~{r[1]}-{r[2]} ({r[3]} arts) | {r[0]}")

print("\n=== Cross-refs from Civil Code TO other laws (explicit) ===")
for r in conn.execute(f"""
    SELECT article_number, article_title, cross_references 
    FROM read_parquet('{P}') 
    WHERE doc_id IN (-180552, -111189) 
      AND cross_references IS NOT NULL 
      AND (cross_references LIKE '%Qonun%' OR cross_references LIKE '%qonun%' OR cross_references LIKE '%Konstitutsiya%')
    LIMIT 10
""").fetchall():
    print(f"  Art {r[0]} ({r[1]}):")
    print(f"    -> {r[2][:250]}")
    print()

print("\n=== 5 example Laws that reference Civil Code ===")
for r in conn.execute(f"""
    SELECT doc_title, article_number, article_title, LEFT(article_text, 250)
    FROM read_parquet('{P}') 
    WHERE doc_type = 'law' AND LOWER(article_text) LIKE '%fuqarolik kodeksi%'
    LIMIT 5
""").fetchall():
    print(f"  LAW: {r[0]}")
    print(f"  Art {r[1]} ({r[2]}): {r[3][:200]}...")
    print()

print("\n=== 5 example Cabinet Resolutions referencing Civil Code ===")
for r in conn.execute(f"""
    SELECT doc_title, LEFT(article_text, 250)
    FROM read_parquet('{P}') 
    WHERE doc_type = 'resolution' AND LOWER(article_text) LIKE '%fuqarolik kodeksi%'
    LIMIT 5
""").fetchall():
    print(f"  RESOLUTION: {r[0]}")
    print(f"  Text: {r[1][:200]}...")
    print()
