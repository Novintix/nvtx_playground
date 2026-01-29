# app.py
import streamlit as st
from multihop_rag import MultiHopRAG

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Medical Research Literature Navigator",
    page_icon="🧬",
    layout="wide"
)

# --------------------------------------------------
# Custom CSS (medical theme)
# --------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #f9fbfd; }
    .title { color: #0b4f6c; font-weight: 700; }
    .subtitle { color: #1b6f8a; font-size: 18px; }
    .answer-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0b4f6c;
    }
    .paper-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("<h1 class='title'>🧬 Medical Research Literature Navigator</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitle'>Multi-hop Retrieval-Augmented Generation for Biomedical Research</p>",
    unsafe_allow_html=True
)

st.divider()

# --------------------------------------------------
# User Input
# --------------------------------------------------
query = st.text_input(
    "🔍 Enter your medical/scientific query",
    placeholder="e.g. How do lifestyle factors influence insulin resistance through inflammatory pathways?"
)

response_type = st.selectbox(
    "Response Length",
    ["Crisp", "Short", "Brief", "Detailed", "Long"],
    index=2
)

search_btn = st.button("🔎 Search Literature")

# --------------------------------------------------
# Helper: Format answer length
# --------------------------------------------------
def format_answer(answer: str, mode: str) -> str:
    sentences = answer.split(". ")

    if mode == "Crisp":
        return ". ".join(sentences[:2]) + "."
    if mode == "Short":
        return ". ".join(sentences[:3]) + "."
    if mode == "Brief":
        return ". ".join(sentences[:5]) + "."
    if mode == "Detailed":
        return answer
    if mode == "Long":
        return answer + "\n\n" + answer

    return answer

# --------------------------------------------------
# Run Search
# --------------------------------------------------
if search_btn:
    if not query.strip():
        st.warning("Please enter a valid medical query.")
    else:
        with st.spinner("🔬 Analyzing biomedical literature..."):
            rag = MultiHopRAG()
            answer, papers = rag.run(query)

        st.divider()

        # ----------------------------
        # Display Query
        # ----------------------------
        st.subheader("🧾 Your Query")
        st.write(query)

        # ----------------------------
        # Display Answer
        # ----------------------------
        st.subheader("🧠 Generated Answer")
        st.markdown(
            f"<div class='answer-box'>{format_answer(answer, response_type)}</div>",
            unsafe_allow_html=True
        )

        # ----------------------------
        # Display References
        # ----------------------------
        st.subheader("📚 Reference Papers")

        if not papers:
            st.info("No reference papers found.")
        else:
            for i, p in enumerate(papers, start=1):
                pmid = p.get("pmid", "")
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                st.markdown(
                    f"""
                    <div class="paper-box">
                        <b>{i}. {p.get('title')}</b><br>
                        <i>{p.get('journal', 'Unknown Journal')} ({p.get('year', 'N/A')})</i><br>
                        <a href="{pubmed_url}" target="_blank">🔗 View on PubMed</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
