import streamlit as st
from multihop_rag import MultiHopRAG
from db import init_db, get_db_stats, migrate_db
from error_handler import log_info
import traceback

# ==================================================
# Page Configuration
# ==================================================
st.set_page_config(
    page_title="MedLink AI - Medical Research Navigator",
    page_icon="🧬",
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
# 🎨 PROFESSIONAL MEDICAL UI CSS (FIXED)
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

/* Fix selectbox dropdown visibility */
[data-testid="stSidebar"] select {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

/* ===== HEADER ===== */
.title {
    color: #0f4c81;
    font-weight: 800;
    font-size: 3rem;
}

.subtitle {
    color: #2563eb;
    font-size: 1.15rem;
    margin-bottom: 1.5rem;
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

/* ===== ANSWER BOX ===== */
.answer-box {
    background-color: #ffffff;
    padding: 26px;
    border-radius: 14px;
    border-left: 6px solid #0f4c81;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    margin: 20px 0;
    color: #0f172a;
    font-size: 1.05rem;
    line-height: 1.9;
}

/* ===== PAPER CARDS ===== */
.paper-box {
    background-color: #ffffff;
    padding: 22px;
    border-radius: 12px;
    margin-bottom: 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

.paper-box:hover {
    box-shadow: 0 6px 18px rgba(0,0,0,0.12);
}

.paper-box h4 {
    color: #0f4c81 !important;
    font-weight: 600;
}

.paper-box p {
    color: #334155 !important;
}

/* ===== SCORE BADGE ===== */
.score-badge {
    background-color: #e0f2fe;
    color: #0369a1;
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
st.markdown("<h1 class='title'>🧬 MedLink AI</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitle'>Medical Research Literature Navigator with Multi-Hop RAG</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# ==================================================
# Sidebar
# ==================================================
with st.sidebar:
    st.header("⚙️ Settings")

    response_mode = st.selectbox(
        "Response Length",
        ["Short", "Brief", "Detailed", "Long"],
        index=2
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
    **MedLink AI** uses:
    - 🔬 PubMed / NCBI API
    - 🧠 PubMedBERT embeddings
    - 🔗 LangGraph orchestration
    - 🎯 Multi-hop retrieval
    - ⚖️ Intelligent re-ranking
    """)

# ==================================================
# Main Content
# ==================================================
st.markdown("### 🔍 Enter your medical research question:")
query = st.text_area(
    label="query_input",
    placeholder="Example: How do pro-inflammatory cytokines impair insulin signaling pathways?",
    height=100,
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    search_btn = st.button("🔎 Search Literature", type="primary", use_container_width=True)

# ==================================================
# Helper: Format Answer by Length
# ==================================================
def format_answer(answer: str, mode: str) -> str:
    if not answer:
        return "No answer available."

    sentences = [s.strip() + "." for s in answer.split(".") if s.strip()]

    mode_map = {
        "Short": len(sentences),
        "Brief": len(sentences),
        "Detailed": len(sentences),
        "Long": len(sentences)
    }

    return " ".join(sentences[:mode_map.get(mode, 5)])

# ==================================================
# Run Search
# ==================================================
if search_btn:
    if not query.strip():
        st.warning("⚠️ Please enter a valid medical query.")
    else:
        try:
            with st.spinner("🔬 Analyzing biomedical literature with Multi-Hop RAG..."):
                rag = MultiHopRAG()
                answer, papers = rag.run(query.strip())
                log_info(f"Search completed: {len(papers)} papers found")

            st.success("✅ Analysis complete!")
            st.markdown("---")

            st.subheader("🧾 Your Query")
            st.markdown(f"<div class='query-box'>{query}</div>", unsafe_allow_html=True)

            st.subheader("🧠 Generated Answer")
            st.markdown(
                f"<div class='answer-box'>{format_answer(answer, response_mode)}</div>",
                unsafe_allow_html=True
            )

            st.subheader(f"📚 Reference Papers ({len(papers)} found)")
            for i, paper in enumerate(papers, 1):
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{paper.get('pmid')}/"
                st.markdown(
                    f"""
                    <div class="paper-box">
                        <span class="score-badge">Score: {paper.get('final_score', 0):.3f}</span>
                        <h4>{paper.get('title')}</h4>
                        <p><i>{paper.get('journal')}</i> • {paper.get('year')}</p>
                        <a href="{pubmed_url}" target="_blank">🔗 View on PubMed →</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        except Exception as e:
            st.error("❌ An error occurred.")
            with st.expander("🔍 Technical Details"):
                st.code(traceback.format_exc())

# ==================================================
# Footer
# ==================================================
st.markdown("---")
st.markdown(
    "<div class='footer'>MedLink AI | Research-only tool. Not for clinical decisions.</div>",
    unsafe_allow_html=True
)
