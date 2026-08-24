import sys, duckdb
sys.stdout.reconfigure(encoding='utf-8')
P = 'c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet'
conn = duckdb.connect()

print("=== 1. Civil Code doc_ids and article counts ===")
for r in conn.execute(f"SELECT doc_id, doc_title, COUNT(*) as cnt FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' GROUP BY doc_id, doc_title").fetchall():
    print(r)

print("\n=== 2. Distinct PART values with counts ===")
for r in conn.execute(f"SELECT part, COUNT(*) as cnt FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' GROUP BY part ORDER BY part").fetchall():
    print(r)

print("\n=== 3. Distinct CHAPTER values (first 30) ===")
for r in conn.execute(f"SELECT DISTINCT chapter FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' ORDER BY chapter LIMIT 30").fetchall():
    print(r)

print("\n=== 4. OKOZ codes ===")
for r in conn.execute(f"SELECT okoz_codes, COUNT(*) as cnt FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' GROUP BY okoz_codes").fetchall():
    print(r)

print("\n=== 5. Cross-references count and 5 examples ===")
cr_count = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' AND cross_references IS NOT NULL AND TRIM(cross_references) != ''").fetchone()[0]
print(f"Count: {cr_count}")
for r in conn.execute(f"SELECT article_number, article_title, cross_references FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' AND cross_references IS NOT NULL AND TRIM(cross_references) != '' LIMIT 5").fetchall():
    print(r)

print("\n=== 6. Amendment notes count and 3 examples ===")
am_count = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' AND amendment_note IS NOT NULL AND TRIM(amendment_note) != ''").fetchone()[0]
print(f"Count: {am_count}")
for r in conn.execute(f"SELECT article_number, LEFT(amendment_note, 150) FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' AND amendment_note IS NOT NULL AND TRIM(amendment_note) != '' LIMIT 3").fetchall():
    print(r)

print("\n=== 7. Sample General Part articles ===")
for r in conn.execute(f"SELECT article_number, article_title, part, chapter FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' AND article_number != '' ORDER BY CAST(REPLACE(article_number,'-','') AS INTEGER) LIMIT 10").fetchall():
    print(r)

print("\n=== 8. How many OTHER acts reference 'Fuqarolik kodeks' ===")
ref_count = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{P}') WHERE doc_type != 'code' AND LOWER(article_text) LIKE '%fuqarolik kodeks%'").fetchone()[0]
print(f"Total articles in other acts referencing Civil Code: {ref_count}")
print("By doc_type:")
for r in conn.execute(f"SELECT doc_type, COUNT(*) as cnt FROM read_parquet('{P}') WHERE doc_type != 'code' AND LOWER(article_text) LIKE '%fuqarolik kodeks%' GROUP BY doc_type ORDER BY cnt DESC").fetchall():
    print(r)

print("\n=== 9. 5 sample references FROM other acts TO Civil Code ===")
for r in conn.execute(f"SELECT doc_type, doc_title, article_number, LEFT(article_text, 200) FROM read_parquet('{P}') WHERE doc_type != 'code' AND LOWER(article_text) LIKE '%fuqarolik kodeks%' LIMIT 5").fetchall():
    print(r)

print("\n=== 10. Civil Code articles that cross-ref other codes/laws ===")
for r in conn.execute(f"SELECT article_number, article_title, cross_references FROM read_parquet('{P}') WHERE doc_type = 'code' AND doc_title LIKE '%Fuqarolik%' AND (LOWER(cross_references) LIKE '%kodeks%' OR LOWER(cross_references) LIKE '%qonun%') LIMIT 10").fetchall():
    print(r)
