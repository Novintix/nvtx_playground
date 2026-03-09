# app.py
import streamlit as st
from multihop_rag import MultiHopRAG
from db import init_db, get_db_stats, migrate_db
from error_handler import log_info
import traceback

# ==================================================
# Page Configuration
# ==================================================
st.set_page_config(
    page_title="MedGuard Evidence - Medical Research Literature Navigator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# Initialize Database
# ==================================================
try:
    init_db()
    migrate_db()
except Exception as e:
    st.error(f"Database initialization failed: {e}")

# ==================================================
# 🎨 MEDGUARD UI CSS - FIXED SIDEBAR SELECTBOX
# ==================================================
st.markdown("""
<style>

/* ===== GLOBAL ===== */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.main {
    background-color: #f8fafc;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label {
    color: #f8fafc !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: #cbd5e1 !important;
}

/* FIX: Selectbox container - light background */
[data-testid="stSidebar"] .stSelectbox > div {
    background-color: #f8fafc !important;
}

/* FIX: Selectbox input/control - dark text */
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

/* FIX: Selected value text - FORCE DARK */
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div,
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div > div,
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] input {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}

/* FIX: Dropdown menu options */
[data-testid="stSidebar"] .stSelectbox [role="listbox"] {
    background-color: #f8fafc !important;
}

[data-testid="stSidebar"] .stSelectbox [role="option"] {
    color: #0f172a !important;
    background-color: #f8fafc !important;
}

[data-testid="stSidebar"] .stSelectbox [role="option"]:hover {
    background-color: #e2e8f0 !important;
}

/* ===== HEADER ===== */
.title {
    color: #0f4c81;
    font-weight: 800;
    font-size: 2.8rem;
}

.subtitle {
    color: #2563eb;
    font-size: 1.1rem;
    margin-bottom: 1.5rem;
}

/* ===== DOMAIN GUARD ALERT ===== */
.domain-guard-box {
    background-color: #fef2f2;
    border: 2px solid #dc2626;
    padding: 20px;
    border-radius: 12px;
    margin: 20px 0;
}

.domain-guard-box h3 {
    color: #dc2626 !important;
    margin-top: 0;
}

/* ===== QUERY BOX ===== */
.query-box {
    background-color: #e0f2fe;
    padding: 18px;
    border-radius: 10px;
    border-left: 5px solid #0284c7;
    color: #0f172a;
    font-size: 1rem;
}

/* ===== CONFIDENCE BADGES ===== */
.confidence-high {
    background-color: #dcfce7;
    color: #166534;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
}

.confidence-medium {
    background-color: #fef3c7;
    color: #92400e;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
}

.confidence-low {
    background-color: #fee2e2;
    color: #991b1b;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
}

/* ===== METRICS ===== */
[data-testid="stMetricValue"] {
    color: #38bdf8 !important;
    font-size: 1.6rem !important;
}

[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}

/* ===== BUTTON ===== */
button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: white !important;
    font-weight: 600;
    border-radius: 8px;
}

/* ===== FOOTER ===== */
.footer {
    text-align: center;
    color: #64748b;
    font-size: 0.85rem;
    margin-top: 30px;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# Header
# ==================================================
st.markdown("<h1 class='title'>🛡️ MedGuard Evidence</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitle'> Medical Research Literature Navigator</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# ==================================================
# UI CSS
# ==================================================
with st.sidebar:
    st.header("⚙️ Settings")

    response_mode = st.selectbox(
        "Response Length",
        ["Concise", "Detailed", "Comprehensive"],
        index=1,
        help="Choose answer detail level: Concise (brief), Detailed (standard), or Comprehensive (in-depth)"
    )

    st.markdown("---")

    st.header("📊 System Stats")
    try:
        stats = get_db_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Queries", stats.get("total_queries", 0))
        with col2:
            st.metric("Cached Papers", stats.get("total_papers", 0))
    except:
        st.info("Stats unavailable")

    st.markdown("---")
    st.header("ℹ️ About")
    st.markdown("""
    **MedGuard Evidence** uses:
    - 🛡️ Domain validation (rejects off-topic queries)
    - 🔬 PubMed / NCBI API
    - 🧠 PubMedBERT embeddings
    - 🔗 LangGraph orchestration
    - ⚖️ Cross-encoder re-ranking
    - 📊 Uncertainty quantification
    """)

# ==================================================
# Main Content - NO EXAMPLE BUTTONS
# ==================================================
st.markdown("### 🔍 Enter your biomedical research question:")

# Simple clean text input - NO EXAMPLES
query = st.text_area(
    label="query_input",
    placeholder="e.g., How do pro-inflammatory cytokines impair insulin signaling pathways?",
    height=120,
    label_visibility="collapsed",
    help="Enter a specific medical or biomedical research question"
)

st.markdown("---")

# Search button centered
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    search_btn = st.button("🔎 Search Literature", type="primary", use_container_width=True)

# ==================================================
# Helper: Get confidence badge
# ==================================================
def get_confidence_badge(answer_text: str) -> str:
    """Extract and format confidence info"""
    if "⚠️ Low Confidence" in answer_text or "INSUFFICIENT CONFIDENCE" in answer_text:
        return '<span class="confidence-low">⚠️ Low Confidence</span>'
    elif "Confidence Score:" in answer_text:
        import re
        match = re.search(r'Confidence Score:\s*([0-9.]+)', answer_text)
        if match:
            score = float(match.group(1))
            if score >= 0.7:
                return f'<span class="confidence-high">✓ High Confidence ({score:.2f})</span>'
            elif score >= 0.5:
                return f'<span class="confidence-medium">~ Medium Confidence ({score:.2f})</span>'
            else:
                return f'<span class="confidence-low">✗ Low Confidence ({score:.2f})</span>'
    return ""

# ==================================================
# Run Search
# ==================================================
if search_btn:
    if not query.strip():
        st.warning("⚠️ Please enter a valid medical query.")
    else:
        try:
            with st.spinner("🛡️ Validating domain..."):
                rag = MultiHopRAG()
                # PASS response_mode TO THE PIPELINE
                answer, papers = rag.run(query.strip(), response_mode=response_mode)

            st.success("✅ Analysis complete!")
            st.markdown("---")

            # Display query
            st.subheader("🧾 Your Query")
            st.markdown(f"<div class='query-box'>{query}</div>", unsafe_allow_html=True)
            
            # Check if it was rejected
            if "Query Rejected" in answer or "🚫" in answer:
                st.markdown("---")
                st.markdown(f"<div class='domain-guard-box'>{answer}</div>", unsafe_allow_html=True)
                
                # Still show any papers that were found (for debugging)
                if papers:
                    with st.expander("🔍 Debug: Papers that would have been used"):
                        for paper in papers[:3]:
                            st.write(f"- {paper.get('title', 'Unknown')}")
            else:
                # Normal answer display
                st.subheader("🧠 Generated Answer")
                
                # Confidence badge
                badge = get_confidence_badge(answer)
                if badge:
                    st.markdown(badge, unsafe_allow_html=True)
                
                # Display formatted answer with markdown (does NOT include Reference Papers anymore)
                st.markdown(answer)
                
                # Reference papers section - NOW ONLY HERE (not duplicated)
                st.subheader(f"📚 Reference Papers ({min(5, len(papers))} shown)")
                
                for i, paper in enumerate(papers[:5], 1):
                    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{paper.get('pmid')}/"
                    
                    # Create paper card - NO SCORE BREAKDOWN, NO Re/CE
                    with st.container():
                        cols = st.columns([4, 1])
                        with cols[0]:
                            st.markdown(f"**{i}. {paper.get('title')}**")
                            st.caption(f"*{paper.get('journal')}* • {paper.get('year')}")
                        with cols[1]:
                            st.metric("Score", f"{paper.get('final_score', 0):.3f}")
                        
                        st.markdown(f"[🔗 View on PubMed →]({pubmed_url})")
                        st.divider()

        except Exception as e:
            st.error("❌ An error occurred.")
            with st.expander("🔍 Technical Details"):
                st.code(traceback.format_exc())

# ==================================================
# Footer
# ==================================================
st.markdown("---")
st.markdown(
    "<div class='footer'>MedGuard Evidence | Research-only tool. Not for clinical decisions without expert review.</div>",
    unsafe_allow_html=True
)