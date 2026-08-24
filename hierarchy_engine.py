import duckdb
import pandas as pd
import re

class HierarchyEngine:
    def __init__(self, parquet_path):
        self.parquet_path = parquet_path
        self.conn = duckdb.connect()
        # Enable full text search extension if needed later
        # self.conn.execute("INSTALL fts; LOAD fts;")
        self._setup_views()

    def _setup_views(self):
        # Create a view that unifies the two Civil Code versions (-111189 and -180552)
        # We consider doc_id in (-111189, -180552) as the unified Civil Code.
        # We'll normalize the doc_id to 'FK' for these unified articles.
        self.conn.execute(f"""
            CREATE OR REPLACE VIEW unified_fk AS
            SELECT 
                'FK' as act_group_id,
                -111189 as doc_id, -- Use a single nominal ID for the unified code
                'Oʻzbekiston Respublikasining Fuqarolik kodeksi (Birlashgan)' as doc_title,
                doc_type,
                doc_date,
                part,
                chapter,
                article_number,
                article_title,
                article_text,
                amendment_note,
                cross_references,
                source_url,
                okoz_codes,
                id as original_id
            FROM read_parquet('{self.parquet_path}')
            WHERE doc_id IN (-111189, -180552)
        """)
        
        # Create a general view for all acts, replacing the FK pieces with the unified one
        self.conn.execute(f"""
            CREATE OR REPLACE VIEW all_acts AS
            SELECT 
                act_group_id, doc_id, doc_title, doc_type, doc_date, part, chapter, 
                article_number, article_title, article_text, amendment_note, 
                cross_references, source_url, okoz_codes, id
            FROM read_parquet('{self.parquet_path}')
            WHERE doc_id NOT IN (-111189, -180552)
            
            UNION ALL
            
            SELECT 
                act_group_id, doc_id, doc_title, doc_type, doc_date, part, chapter, 
                article_number, article_title, article_text, amendment_note, 
                cross_references, source_url, okoz_codes, original_id as id
            FROM unified_fk
        """)

    def get_unified_fk_stats(self):
        return self.conn.execute("SELECT COUNT(*) FROM unified_fk").fetchone()[0]

    def extract_explicit_citations(self, text):
        """
        Approach A: Regex to extract citations.
        Returns a list of extracted citations (e.g. {'type': 'fk', 'article': '14'})
        """
        if not text or pd.isna(text):
            return []
        citations = []
        
        # Match 'Fuqarolik kodeksining N-moddasi' or similar
        fk_pattern = r"(?i)fuqarolik\s+kodeksi(?:ning)?\s+(\d+)\s*-\s*moddasi"
        for match in re.finditer(fk_pattern, text):
            citations.append({'type': 'fk', 'article': match.group(1)})
            
        # Match 'Konstitutsiyasining N-moddasi'
        const_pattern = r"(?i)konstitutsiyasi(?:ning)?\s+(\d+)\s*-\s*moddasi"
        for match in re.finditer(const_pattern, text):
            citations.append({'type': 'constitution', 'article': match.group(1)})
            
        return citations

    def get_article_hierarchy(self, target_id):
        """
        Given a target article ID (e.g. from a Cabinet Resolution),
        find its 5-tier hierarchy using the Hybrid Approach (A + B).
        """
        # Fetch the target article
        target = self.conn.execute(f"""
            SELECT doc_type, doc_title, article_number, article_text, okoz_codes, cross_references 
            FROM all_acts 
            WHERE id = ?
        """, [target_id]).fetchone()
        
        if not target:
            return None
            
        doc_type, doc_title, art_num, text, okoz_codes, cross_refs = target
        
        hierarchy = {
            'tier5_resolution': None,
            'tier4_decree': None,
            'tier3_law': None,
            'tier2_fk': [],
            'tier1_const': []
        }
        
        # Populate the target in its respective tier
        if doc_type == 'resolution':
            hierarchy['tier5_resolution'] = {'title': doc_title, 'article': art_num, 'text': text}
        elif doc_type == 'decree':
            hierarchy['tier4_decree'] = {'title': doc_title, 'article': art_num, 'text': text}
        elif doc_type == 'law':
            hierarchy['tier3_law'] = {'title': doc_title, 'article': art_num, 'text': text}

        # Approach A: Explicit Citations (Layer 1 - High Confidence)
        citations = self.extract_explicit_citations(str(cross_refs) + " " + str(text))
        for cit in citations:
            if cit['type'] == 'fk':
                # Fetch FK article
                fk_art = self.conn.execute(f"SELECT article_title, article_text FROM unified_fk WHERE article_number = '{cit['article']}'").fetchone()
                if fk_art:
                    hierarchy['tier2_fk'].append({
                        'article': cit['article'],
                        'title': fk_art[0],
                        'text': fk_art[1],
                        'confidence': '🟢 Explicit (Citation)'
                    })
            elif cit['type'] == 'constitution':
                const_art = self.conn.execute(f"SELECT article_title, article_text FROM all_acts WHERE doc_type = 'constitution' AND article_number = '{cit['article']}'").fetchone()
                if const_art:
                    hierarchy['tier1_const'].append({
                        'article': cit['article'],
                        'title': const_art[0],
                        'text': const_art[1],
                        'confidence': '🟢 Explicit (Citation)'
                    })

        # Approach B: OKOZ Mapping (Layer 2 - Structural)
        # Placeholder for user's pandectist mapping
        okoz_to_fk_map = {
            # User will fill this later. Example: '1.03.01.00': ['29-bob', '30-bob']
        }
        
        # If no explicit FK citations were found, try OKOZ mapping
        if not hierarchy['tier2_fk'] and okoz_codes:
            for code in okoz_codes:
                if code in okoz_to_fk_map:
                    chapters = okoz_to_fk_map[code]
                    for chap in chapters:
                        # Fetch representative articles for the chapter
                        fk_arts = self.conn.execute(f"SELECT article_number, article_title, article_text FROM unified_fk WHERE chapter = '{chap}' LIMIT 2").fetchall()
                        for fk_art in fk_arts:
                            hierarchy['tier2_fk'].append({
                                'article': fk_art[0],
                                'title': fk_art[1],
                                'text': fk_art[2],
                                'confidence': f'🟡 Structural (OKOZ {code})'
                            })

        # Approach C: Semantic/Textual Search (Layer 3 - Discovery)
        # As a fallback, use DuckDB's LIKE/ILIKE on FK text based on key terms from the target text
        if not hierarchy['tier2_fk']:
            # Extremely simplified 'semantic' fallback: pick top 3 longest words from text to search
            words = [w for w in re.findall(r'\b\w{6,}\b', str(text).lower()) if w not in ('uchun', 'bilan', 'haqida', 'toʻgʻrisida', 'qilish', 'etish')]
            if words:
                keyword = words[0] # Just use the most prominent word for demo
                fk_arts = self.conn.execute(f"SELECT article_number, article_title, article_text FROM unified_fk WHERE LOWER(article_text) LIKE '%{keyword}%' LIMIT 2").fetchall()
                for fk_art in fk_arts:
                    hierarchy['tier2_fk'].append({
                        'article': fk_art[0],
                        'title': fk_art[1],
                        'text': fk_art[2],
                        'confidence': f'🔵 Textual Match ({keyword})'
                    })

        return hierarchy

if __name__ == "__main__":
    engine = HierarchyEngine('c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet')
    print(f"Unified Civil Code Articles: {engine.get_unified_fk_stats()}")
