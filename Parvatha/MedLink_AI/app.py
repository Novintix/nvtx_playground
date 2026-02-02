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
    page_title="MedGuard Evidence - Medical Research Navigator",
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
# 🎨 MEDGUARD UI CSS
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

/* ===== ANSWER BOXES ===== */
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

.answer-box-low-confidence {
    background-color: #fffbeb;
    border-left: 6px solid #f59e0b;
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

/* ===== VALIDATION INFO ===== */
.validation-info {
    background-color: #f0fdf4;
    border: 1px solid #22c55e;
    padding: 10px 15px;
    border-radius: 8px;
    margin-top: 10px;
    font-size: 0.9rem;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# Header
# ==================================================
st.markdown("<h1 class='title'>🛡️ MedGuard Evidence</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitle'>Domain-Guarded Medical Research Navigator with Uncertainty Quantification</p>",
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
        ["Concise", "Detailed", "Comprehensive"],
        index=1
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
    
    **New:** Rejects non-medical queries like "Taj Mahal" 
    """)

# ==================================================
# Main Content
# ==================================================
st.markdown("### 🔍 Enter your biomedical research question:")

# Example queries
example_queries = [
    "How do pro-inflammatory cytokines impair insulin signaling pathways?",
    "What is the relationship between obesity and type 2 diabetes mechanisms?",
    "How does metformin affect mitochondrial function in cancer cells?"
]

query = st.text_area(
    label="query_input",
    placeholder=example_queries[0],
    height=100,
    label_visibility="collapsed"
)

# Show examples
col1, col2, col3 = st.columns(3)
for i, col in enumerate([col1, col2, col3]):
    with col:
        if st.button(f"Example {i+1}", key=f"ex_{i}"):
            st.session_state["query"] = example_queries[i]
            st.rerun()

st.markdown("---")

col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    search_btn = st.button("🔎 Search Literature", type="primary", use_container_width=True)

# ==================================================
# Helper: Format Answer by Length
# ==================================================
def format_answer(answer: str, mode: str) -> str:
    """Format answer based on selected length"""
    if not answer:
        return "No answer available."
    
    if mode == "Concise":
        # Return first 2-3 sentences or first paragraph
        paragraphs = answer.split('\\n\\n')
        return paragraphs[0] if paragraphs else answer[:500]
    elif mode == "Comprehensive":
        return answer  # Full answer
    else:  # Detailed
        return answer

# ==================================================
# Helper: Get confidence badge
# ==================================================
def get_confidence_badge(answer_text: str) -> str:
    """Extract and format confidence info"""
    if "INSUFFICIENT CONFIDENCE" in answer_text:
        return '<span class="confidence-low">⚠️ Low Confidence</span>'
    elif "Confidence Score:" in answer_text:
        # Try to extract score
        import re
        match = re.search(r'Confidence Score:\\s*([0-9.]+)', answer_text)
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
            with st.spinner("🛡️ Validating domain... 🔬 Retrieving evidence... ⚖️ Ranking... 🧠 Synthesizing..."):
                rag = MultiHopRAG()
                answer, papers = rag.run(query.strip())
                log_info(f"Search completed: {len(papers)} papers processed")

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
                
                # Answer box styling based on confidence
                box_class = "answer-box"
                if "INSUFFICIENT CONFIDENCE" in answer:
                    box_class = "answer-box answer-box-low-confidence"
                
                formatted_answer = format_answer(answer, response_mode)
                st.markdown(
                    f"<div class='{box_class}'>{formatted_answer}</div>",
                    unsafe_allow_html=True
                )

                # Reference papers
                st.subheader(f"📚 Reference Papers ({len(papers)} found)")
                
                for i, paper in enumerate(papers, 1):
                    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{paper.get('pmid')}/"
                    
                    # Get score breakdown if available
                    breakdown = paper.get('score_breakdown', {})
                    breakdown_str = ""
                    if breakdown:
                        breakdown_str = f"Re: {breakdown.get('relevance', 0):.2f} | CE: {breakdown.get('cross_encoder', 0):.2f}"
                    
                    st.markdown(
                        f"""
                        <div class="paper-box">
                            <span class="score-badge">Score: {paper.get('final_score', 0):.3f} {breakdown_str}</span>
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
    "<div class='footer'>MedGuard Evidence | Research-only tool. Not for clinical decisions without expert review.</div>",
    unsafe_allow_html=True
)
 
