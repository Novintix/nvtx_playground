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
# Custom CSS - FIXED SIDEBAR & SEARCH ICON
# ==================================================
st.markdown("""
<style>
    /* Main background */
    .main { 
        background-color: #f9fbfd; 
    }
    
    /* Fix sidebar background and text */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #cbd5e1 !important;
    }
    
    /* Sidebar metrics */
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #22d3ee !important;
        font-size: 1.5rem !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }
    
    .title { 
        color: #0b4f6c; 
        font-weight: 700; 
        font-size: 3rem; 
    }
    
    .subtitle { 
        color: #1b6f8a; 
        font-size: 1.2rem; 
        margin-bottom: 2rem; 
    }
    
    /* Fix for answer text visibility */
    .answer-box {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border-left: 5px solid #0b4f6c;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 20px 0;
        color: #2c3e50 !important;
        font-size: 1.05rem;
        line-height: 1.8;
    }
    
    .answer-box p, .answer-box div, .answer-box span {
        color: #2c3e50 !important;
    }
    
    .paper-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        transition: box-shadow 0.3s;
    }
    
    .paper-box:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .paper-box h4 {
        color: #0b4f6c !important;
        margin: 10px 0 !important;
    }
    
    .paper-box p {
        color: #555 !important;
        margin: 8px 0 !important;
    }
    
    .score-badge {
        background-color: #e8f4f8;
        color: #0b4f6c;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 8px;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    
    /* Ensure all Streamlit elements have proper text color */
    .stMarkdown {
        color: #2c3e50 !important;
    }
    
    /* Fix subheaders */
    h2, h3, h4 {
        color: #0b4f6c !important;
    }
    
    /* Fix info/warning boxes */
    .stAlert {
        color: #2c3e50 !important;
    }
    
    .stAlert > div {
        color: #2c3e50 !important;
    }
    
    /* Query display box */
    .query-box {
        background-color: #e8f4f8;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1b6f8a;
        color: #2c3e50 !important;
        font-size: 1rem;
        margin: 15px 0;
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
        ["Crisp", "Short", "Brief", "Detailed", "Long"],
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
    - 🔬 PubMed/NCBI API
    - 🧠 PubMedBERT embeddings
    - 🔗 LangGraph orchestration
    - 🎯 Multi-hop retrieval
    - ⚖️ Intelligent re-ranking
    """)
    
    st.markdown("---")
    st.caption("Built with LangChain + LangGraph + RAG")

# ==================================================
# Main Content
# ==================================================

# Query Input - FIXED LABEL
st.markdown("### 🔍 Enter your medical research question:")
query = st.text_area(
    label="query_input",
    value="",
    placeholder="Example: How do lifestyle factors influence insulin resistance through inflammatory pathways?",
    height=100,
    label_visibility="collapsed"
)

st.markdown("")  # Add spacing

# Search Button
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    search_btn = st.button("🔎 Search Literature", type="primary", use_container_width=True)

# ==================================================
# Helper: Format Answer by Length
# ==================================================
def format_answer(answer: str, mode: str) -> str:
    """Format answer based on selected mode"""
    if not answer:
        return "No answer available."
    
    sentences = [s.strip() + "." for s in answer.split(".") if s.strip()]
    
    mode_map = {
        "Crisp": 2,
        "Short": 3,
        "Brief": 5,
        "Detailed": len(sentences),
        "Long": len(sentences)
    }
    
    num_sentences = mode_map.get(mode, 5)
    result = " ".join(sentences[:num_sentences])
    
    if mode == "Long" and len(sentences) > 5:
        result += "\n\n" + " ".join(sentences)
    
    return result

# ==================================================
# Run Search
# ==================================================
if search_btn:
    if not query or not query.strip():
        st.warning("⚠️ Please enter a valid medical query.")
    else:
        try:
            with st.spinner("🔬 Analyzing biomedical literature with Multi-Hop RAG..."):
                
                # Initialize RAG
                rag = MultiHopRAG()
                
                # Run pipeline
                answer, papers = rag.run(query.strip())
                
                log_info(f"Search completed: {len(papers)} papers found")
            
            # Success message
            st.success("✅ Analysis complete!")
            
            st.markdown("---")
            
            # ==================================================
            # Display Query
            # ==================================================
            st.subheader("🧾 Your Query")
            st.markdown(
                f"<div class='query-box'>{query}</div>",
                unsafe_allow_html=True
            )
            
            # ==================================================
            # Display Answer - UPDATED FOR VISIBILITY
            # ==================================================
            st.subheader("🧠 Generated Answer")
            formatted_answer = format_answer(answer, response_mode)
            st.markdown(
                f"""
                <div class='answer-box'>
                    <p style='color: #2c3e50; margin: 0; line-height: 1.8;'>{formatted_answer}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # ==================================================
            # Display Papers
            # ==================================================
            st.subheader(f"📚 Reference Papers ({len(papers)} found)")
            
            if not papers:
                st.info("No reference papers found.")
            else:
                for i, paper in enumerate(papers, start=1):
                    pmid = paper.get("pmid", "")
                    title = paper.get("title", "Unknown Title")
                    journal = paper.get("journal", "Unknown Journal")
                    year = paper.get("year", "N/A")
                    score = paper.get("final_score", 0.0)
                    
                    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    
                    st.markdown(
                        f"""
                        <div class="paper-box">
                            <div style="margin-bottom: 10px;">
                                <span class="score-badge">Score: {score:.3f}</span>
                                <span style="color: #888; font-size: 0.9rem;">#{i}</span>
                            </div>
                            <h4 style="color: #0b4f6c; margin: 10px 0;">{title}</h4>
                            <p style="color: #555; margin: 8px 0;">
                                <i>{journal}</i> • {year} • PMID: {pmid}
                            </p>
                            <a href="{pubmed_url}" target="_blank" style="color: #1b6f8a; text-decoration: none; font-weight: 500;">
                                🔗 View on PubMed →
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # ==================================================
            # Download Results
            # ==================================================
            if papers:
                st.markdown("---")
                st.subheader("💾 Export Results")
                
                # Create downloadable text
                export_text = f"Query: {query}\n\n"
                export_text += f"Answer:\n{answer}\n\n"
                export_text += "="*80 + "\n\n"
                export_text += "Reference Papers:\n\n"
                
                for i, paper in enumerate(papers, start=1):
                    export_text += f"{i}. {paper.get('title', 'Unknown')}\n"
                    export_text += f"   Journal: {paper.get('journal', 'Unknown')} ({paper.get('year', 'N/A')})\n"
                    export_text += f"   PMID: {paper.get('pmid', 'N/A')}\n"
                    export_text += f"   Score: {paper.get('final_score', 0):.3f}\n\n"
                
                st.download_button(
                    label="📄 Download Results as Text",
                    data=export_text,
                    file_name=f"medlink_results_{pmid}.txt",
                    mime="text/plain"
                )
        
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.error("Please try again or contact support if the issue persists.")
            
            # Show detailed error in expander
            with st.expander("🔍 Technical Details"):
                st.code(traceback.format_exc())

# ==================================================
# Footer
# ==================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>MedLink AI | Powered by LangChain, LangGraph & PubMedBERT</p>
        <p style="font-size: 0.85rem;">For research purposes only. Consult medical professionals for clinical decisions.</p>
    </div>
    """,
    unsafe_allow_html=True
)