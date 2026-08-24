import sys, duckdb
sys.stdout.reconfigure(encoding='utf-8')
P = 'c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet'
conn = duckdb.connect()

# First find the exact Civil Code doc_id
print("=== 1. Find the exact Fuqarolik Kodeksi (Civil Code) ===")
for r in conn.execute(f"""
    SELECT doc_id, doc_title, COUNT(*) as cnt 
    FROM read_parquet('{P}') 
    WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik kodeksi%' AND doc_title NOT LIKE '%protsessual%'
    GROUP BY doc_id, doc_title
""").fetchall():
    print(r)

# Use the main Civil Code doc_id
# The Civil Code of Uzbekistan should be "Oʻzbekiston Respublikasining Fuqarolik kodeksi"
print("\n=== 2. All doc_type='code' titles (to find the right one) ===")
for r in conn.execute(f"""
    SELECT doc_id, doc_title, COUNT(*) as cnt 
    FROM read_parquet('{P}') 
    WHERE doc_type = 'code'
    GROUP BY doc_id, doc_title
    ORDER BY cnt DESC
    LIMIT 20
""").fetchall():
    print(f"  doc_id={r[0]} | articles={r[2]} | {r[1]}")

print("\n=== 3. Search for 'Fuqarolik kodeksi' by article count (should be ~1190) ===")
for r in conn.execute(f"""
    SELECT doc_id, doc_title, COUNT(*) as cnt 
    FROM read_parquet('{P}') 
    WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik kodeksi%'
    GROUP BY doc_id, doc_title
    ORDER BY cnt DESC
""").fetchall():
    print(f"  doc_id={r[0]} | articles={r[2]} | {r[1]}")

print("\n=== 4. Try broader search for the Civil Code ===")
for r in conn.execute(f"""
    SELECT doc_id, doc_title, COUNT(*) as cnt 
    FROM read_parquet('{P}') 
    WHERE doc_type = 'code'
    GROUP BY doc_id, doc_title
    HAVING cnt > 100
    ORDER BY cnt DESC
""").fetchall():
    print(f"  doc_id={r[0]} | articles={r[2]} | {r[1]}")
