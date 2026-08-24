import streamlit as st
import duckdb
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Uzbek Legal Corpus Explorer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .stat-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2563EB;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .article-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .article-badge {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1D4ED8;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 12px;
        margin-right: 8px;
    }
    .article-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #0F172A;
        margin-top: 10px;
        margin-bottom: 8px;
    }
    .article-hierarchy {
        font-size: 0.9rem;
        color: #475569;
        font-style: italic;
        margin-bottom: 12px;
    }
    .article-body {
        font-size: 1.0rem;
        line-height: 1.6;
        color: #334155;
        white-space: pre-wrap;
        background: #F8FAFC;
        padding: 15px;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Database Connection (Cached)
PARQUET_PATH = "c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet"

@st.cache_resource
def get_db_connection():
    conn = duckdb.connect(database=':memory:')
    return conn

conn = get_db_connection()

# Get Summary Stats (Cached)
@st.cache_data
def get_summary_stats():
    total_articles = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{PARQUET_PATH}')").fetchone()[0]
    total_acts = conn.execute(f"SELECT COUNT(DISTINCT doc_id) FROM read_parquet('{PARQUET_PATH}')").fetchone()[0]
    doc_types = conn.execute(f"SELECT DISTINCT doc_type FROM read_parquet('{PARQUET_PATH}') WHERE doc_type IS NOT NULL").fetchall()
    doc_types_list = [dt[0] for dt in doc_types if dt[0]]
    return total_articles, total_acts, sorted(doc_types_list)

try:
    total_articles, total_acts, doc_types_list = get_summary_stats()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# Header
st.markdown('<div class="main-header">⚖️ Oʻzbekiston Qonunchiligi Qidiruv Tizimi</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Uzbek Legal Corpus Interactive Search & Research Tool (24,267 acts · 54,173 articles)</div>', unsafe_allow_html=True)

# Sidebar Filters
st.sidebar.header("🔍 Qidiruv va Filtrlash (Filters)")

search_query = st.sidebar.text_input(
    "Kalit soʻz / Keyword Search",
    placeholder="Masalan: shartnoma, soliq, mehnat, javobgarlik...",
    help="Modda matnidan yoki sarlavhadan qidirish uchun soʻz kiriting"
)

selected_doc_types = st.sidebar.multiselect(
    "Hujjat turi (Document Type)",
    options=doc_types_list,
    default=[]
)

# Date range filter
year_range = st.sidebar.slider(
    "Qabul qilingan yili (Year of Adoption)",
    min_value=1991,
    max_value=2026,
    value=(1991, 2026)
)

limit_results = st.sidebar.number_input(
    "Natijalar soni (Max Results)",
    min_value=10,
    max_value=500,
    value=50,
    step=10
)

# Top Bar Statistics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{total_acts:,}</div><div class="stat-label">Hujjatlar (Acts)</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{total_articles:,}</div><div class="stat-label">Moddalar (Articles)</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{year_range[0]} – {year_range[1]}</div><div class="stat-label">Yillar Oraligʻi</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="stat-card"><div class="stat-value">uz-Latin</div><div class="stat-label">Til & Yozuv</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Build Query dynamically
where_clauses = ["1=1"]
params = []

if search_query.strip():
    where_clauses.append("(LOWER(article_text) LIKE LOWER(?) OR LOWER(doc_title) LIKE LOWER(?) OR LOWER(article_title) LIKE LOWER(?))")
    kw = f"%{search_query.strip()}%"
    params.extend([kw, kw, kw])

if selected_doc_types:
    placeholders = ",".join(["?"] * len(selected_doc_types))
    where_clauses.append(f"doc_type IN ({placeholders})")
    params.extend(selected_doc_types)

where_clauses.append("YEAR(CAST(doc_date AS DATE)) BETWEEN ? AND ?")
params.extend([year_range[0], year_range[1]])

where_sql = " AND ".join(where_clauses)

query_sql = f"""
    SELECT 
        id, doc_id, doc_title, doc_type, doc_date,
        part, chapter, article_number, article_title, article_text,
        amendment_note, cross_references, source_url
    FROM read_parquet('{PARQUET_PATH}')
    WHERE {where_sql}
    LIMIT {limit_results}
"""

@st.cache_data
def run_search(sql, query_params):
    return conn.execute(sql, query_params).fetchdf()

try:
    results_df = run_search(query_sql, params)
except Exception as e:
    st.error(f"Qidiruvda xatolik yuz berdi: {e}")
    results_df = pd.DataFrame()

# Display Results Header
st.subheader(f"📋 Qidiruv natijalari ({len(results_df)} ta modda koʻrsatilmoqda)")

if search_query:
    st.info(f"🔍 Topildi soʻrovi boʻyicha: **'{search_query}'**")

if results_df.empty:
    st.warning("Hech qanday natija topilmadi. Qidiruv soʻzini yoki filtrlarni oʻzgartirib koʻring.")
else:
    # Tabs: Card View & Table View
    tab_cards, tab_table = st.tabs(["📇 Karta koʻrinishi (Cards)", "📊 Jadval koʻrinishi (Table)"])

    with tab_cards:
        for idx, row in results_df.iterrows():
            doc_title = row['doc_title'] if pd.notna(row['doc_title']) else "Noma'lum hujjat"
            art_num = row['article_number'] if pd.notna(row['article_number']) and row['article_number'] else ""
            art_title = row['article_title'] if pd.notna(row['article_title']) and row['article_title'] else ""
            doc_type = str(row['doc_type']).upper() if pd.notna(row['doc_type']) else "HUJJAT"
            doc_date = str(row['doc_date'])[:10] if pd.notna(row['doc_date']) else ""
            
            hierarchy_parts = []
            if pd.notna(row['part']) and row['part']:
                hierarchy_parts.append(f"Boʻlim: {row['part']}")
            if pd.notna(row['chapter']) and row['chapter']:
                hierarchy_parts.append(f"Bob: {row['chapter']}")
            hierarchy_str = " | ".join(hierarchy_parts)

            source_url = row['source_url'] if pd.notna(row['source_url']) else f"https://lex.uz/uz/docs/{abs(row['doc_id'])}"

            with st.container():
                st.markdown(f"""
                <div class="article-card">
                    <div>
                        <span class="article-badge">{doc_type}</span>
                        <span class="article-badge">Sana: {doc_date}</span>
                        <span style="font-size:0.85rem; color:#64748B;">ID: {row['id']}</span>
                    </div>
                    <div style="font-weight:600; font-size:1.05rem; color:#1E3A8A; margin-top:8px;">
                        📜 {doc_title}
                    </div>
                    <div class="article-title">
                        {f"{art_num}-modda. " if art_num else ""}{art_title}
                    </div>
                    {f'<div class="article-hierarchy">📌 {hierarchy_str}</div>' if hierarchy_str else ''}
                    <div class="article-body">{row['article_text']}</div>
                    <div style="margin-top:10px;">
                        <a href="{source_url}" target="_blank" style="color:#2563EB; font-weight:500; font-size:0.9rem; text-decoration:none;">
                            🔗 Lex.uz saytida asl manbasini koʻrish →
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab_table:
        st.dataframe(
            results_df[['doc_title', 'doc_type', 'doc_date', 'article_number', 'article_title', 'article_text']],
            use_container_width=True,
            hide_index=True
        )
        
        # Download Option
        csv_data = results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Natijalarni CSV faylida yuklab olish",
            data=csv_data,
            file_name="qidiruv_natijalari.csv",
            mime="text/csv"
        )

# Disclaimer Footer
st.markdown("---")
st.caption("⚠️ **Eslatma**: Ushbu tizim tadqiqot va ma'lumot olish uchun mo'ljallangan snapshot hisoblanadi. Rasmiy va amaldagi huquqiy kuchga ega matnlarni har doim [lex.uz](https://lex.uz) rasmiy portalidan tekshiring.")
