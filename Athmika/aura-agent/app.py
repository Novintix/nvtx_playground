import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from src.retrieval import ingest_resume

# --- 1. SETUP & CONFIGURATION ---
load_dotenv() 

st.set_page_config(
    page_title="AURA: Career Architect",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State for Resume Text if not present
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

# Custom CSS
st.markdown("""
<style>
    .stChatMessage { background-color: #f0f2f6; border-radius: 15px; padding: 10px; margin-bottom: 10px; }
    [data-testid="stSidebar"] { background-color: #f9fafb; border-right: 1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR: THE CONTROL PANEL ---
# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("AURA ✨")
    st.caption("Adaptive User Readiness Agent")
    st.divider()

    st.subheader("1. Context Setup 📥")
    target_company = st.text_input("Target Company", value="Cognizant (CTS)")
    
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
    
    if uploaded_file:
        save_path = os.path.join("data", "resume.pdf")
        if not os.path.exists("data"):
            os.makedirs("data")
            
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("🧠 Ingesting Resume..."):
            try:
                # Capture the text return value!
                full_text, _ = ingest_resume(save_path)
                st.session_state.resume_text = full_text
                st.success("✅ Resume Indexed! Brain Ready.")
            except Exception as e:
                st.error(f"Ingestion Failed: {e}")
        
    st.divider()

    st.subheader("2. Select Mode 🔀")
    mode = st.radio(
        "Choose your interaction style:",
        ["🛡️ Trainer Mode (Mentor)", "⚔️ Interview Mode (Simulation)"],
        index=0
    )
    
    st.divider()
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 3. MAIN CHAT ---
st.title("Interview Simulation Workspace")
st.caption(f"Target: **{target_company}** | Resume Loaded: **{'Yes' if st.session_state.resume_text else 'No'}**")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(AIMessage(content="Hello! I am AURA. Upload your resume and say **'Start'** to begin."))

for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(message.content)

# --- 4. INTERACTION ---
user_input = st.chat_input("Type your answer or ask a question...")

if user_input:
    st.chat_message("user", avatar="🧑‍💻").markdown(user_input)
    st.session_state.messages.append(HumanMessage(content=user_input))

    # Prepare State
    current_state = {
        "messages": st.session_state.messages,
        "target_company": target_company,
        "mode": "trainer" if "Trainer" in mode else "interviewer",
        "resume_text": st.session_state.resume_text, # Pass the full text
        "retrieved_docs": "" 
    }

    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("AURA is thinking..."):
            try:
                from src.graph import graph
                response = graph.invoke(current_state)
                ai_response = response["messages"][-1].content
            except Exception as e:
                ai_response = f"⚠️ System Error: {str(e)}"
            
            st.markdown(ai_response)
    
    st.session_state.messages.append(AIMessage(content=ai_response))