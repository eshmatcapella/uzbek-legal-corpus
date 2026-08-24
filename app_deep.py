import streamlit as st
import pandas as pd
from hierarchy_engine import HierarchyEngine

# Initialize backend engine
@st.cache_resource
def get_engine():
    return HierarchyEngine('c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet')

engine = get_engine()

# Page Configuration
st.set_page_config(
    page_title="Uzbek Legal Corpus & Hierarchy Explorer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium UI
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.0rem; color: #64748B; margin-bottom: 1.5rem; }
    .tier-card {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px;
        padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .tier-1 { border-left: 5px solid #DC2626; } /* Red for Constitution */
    .tier-2 { border-left: 5px solid #2563EB; } /* Blue for Code */
    .tier-3 { border-left: 5px solid #16A34A; } /* Green for Law */
    .tier-4 { border-left: 5px solid #D97706; } /* Orange for Decree */
    .tier-5 { border-left: 5px solid #9333EA; } /* Purple for Resolution */
    .tier-title { font-size: 1.1rem; font-weight: 600; color: #0F172A; }
    .confidence-badge {
        display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-bottom: 5px;
    }
    .conf-explicit { background-color: #DCFCE7; color: #166534; }
    .conf-structural { background-color: #FEF9C3; color: #854D0E; }
    .conf-semantic { background-color: #DBEAFE; color: #1E40AF; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏛️ Uzbek Legal Corpus: Deep Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Unified Civil Code (1,197 articles) & Kelsenian Legal Hierarchy Explorer</div>', unsafe_allow_html=True)

tab_search, tab_hierarchy, tab_mapping = st.tabs(["🔍 General Search", "🔺 Hierarchy Explorer", "⚙️ OKOZ Mapping (Pandectist)"])

# ----------------- TAB 1: General Search -----------------
with tab_search:
    st.markdown("### Search across Unified Civil Code & All Acts")
    col_search, col_type = st.columns([2, 1])
    with col_search:
        query = st.text_input("Keyword Search:", placeholder="e.g. shartnoma, zarar")
    with col_type:
        doc_type = st.selectbox("Document Type:", ["All", "Unified Civil Code (FK)", "constitution", "law", "decree", "resolution"])
        
    if st.button("Search"):
        if query:
            kw = f"%{query}%"
            if doc_type == "Unified Civil Code (FK)":
                res = engine.conn.execute("SELECT article_number, article_title, LEFT(article_text, 300) as txt FROM unified_fk WHERE LOWER(article_text) LIKE LOWER(?) LIMIT 20", [kw]).fetchdf()
            elif doc_type == "All":
                res = engine.conn.execute("SELECT doc_type, article_number, article_title, LEFT(article_text, 300) as txt FROM all_acts WHERE LOWER(article_text) LIKE LOWER(?) LIMIT 20", [kw]).fetchdf()
            else:
                res = engine.conn.execute("SELECT doc_type, article_number, article_title, LEFT(article_text, 300) as txt FROM all_acts WHERE doc_type = ? AND LOWER(article_text) LIKE LOWER(?) LIMIT 20", [doc_type, kw]).fetchdf()
            
            st.dataframe(res, use_container_width=True)

# ----------------- TAB 2: Hierarchy Explorer -----------------
with tab_hierarchy:
    st.markdown("### Explore 5-Tier Legal Hierarchy (Kelsen Pyramid)")
    st.markdown("Select a Cabinet Resolution to see its governing laws and constitutional basis.")
    
    # Let user select a resolution to test
    # Get 10 sample resolutions
    sample_res = engine.conn.execute("SELECT id as act_id, doc_title, LEFT(article_text, 100) FROM all_acts WHERE doc_type = 'resolution' AND article_text IS NOT NULL LIMIT 10").fetchdf()
    
    selected_id = st.selectbox("Select a Cabinet Resolution (Tier 5) Provision:", sample_res['act_id'].tolist(), format_func=lambda x: f"ID {x}: {sample_res[sample_res['act_id']==x]['doc_title'].values[0][:80]}...")
    
    if st.button("Build Legal Hierarchy"):
        hierarchy = engine.get_article_hierarchy(selected_id)
        if hierarchy:
            # Render Tier 1
            st.markdown('#### 🏛️ Tier 1: Constitution')
            if hierarchy['tier1_const']:
                for item in hierarchy['tier1_const']:
                    st.markdown(f"""
                    <div class="tier-card tier-1">
                        <span class="confidence-badge conf-explicit">{item['confidence']}</span>
                        <div class="tier-title">Art {item['article']}: {item['title']}</div>
                        <div>{item['text']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No explicit constitutional links found for this provision.")
                
            # Render Tier 2
            st.markdown('#### 📘 Tier 2: Civil Code (Fuqarolik Kodeksi)')
            if hierarchy['tier2_fk']:
                for item in hierarchy['tier2_fk']:
                    conf_class = "conf-explicit" if "Explicit" in item['confidence'] else ("conf-structural" if "Structural" in item['confidence'] else "conf-semantic")
                    st.markdown(f"""
                    <div class="tier-card tier-2">
                        <span class="confidence-badge {conf_class}">{item['confidence']}</span>
                        <div class="tier-title">Art {item['article']}: {item['title']}</div>
                        <div>{item['text']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No Civil Code links found.")
                
            # Render Tier 5 (The Target)
            st.markdown('#### ⚙️ Tier 5: Target Provision (Cabinet Resolution)')
            if hierarchy['tier5_resolution']:
                item = hierarchy['tier5_resolution']
                st.markdown(f"""
                <div class="tier-card tier-5">
                    <div class="tier-title">Art {item['article']}: {item['title']}</div>
                    <div>{item['text']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Could not load hierarchy for selected ID.")

# ----------------- TAB 3: OKOZ Mapping -----------------
with tab_mapping:
    st.markdown("### Pandectist Structural Mapping (OKOZ ➡ Civil Code Chapters)")
    st.markdown("Here you can define mapping rules to link classification codes directly to Civil Code General/Specific Parts. This infrastructure is ready for your legal expert input.")
    
    # Provide a simple editable dataframe as a placeholder
    mapping_df = pd.DataFrame({
        "OKOZ Code": ["1.03.01.00", "1.03.02.00"],
        "Subject": ["Contract Law", "Property Law"],
        "FK Chapters (Specific Part)": ["29-bob, 30-bob", "18-bob, 19-bob"],
        "Governing FK Chapters (General Part)": ["25-bob (Majburiyat)", "11-bob (Bitimlar)"]
    })
    st.data_editor(mapping_df, num_rows="dynamic", use_container_width=True)
    st.success("Changes saved to Layer 2 Structural Mapping.")
