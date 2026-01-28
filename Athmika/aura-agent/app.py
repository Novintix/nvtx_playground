import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from src.retrieval import ingest_resume

# --- 1. SETUP & CONFIGURATION ---
load_dotenv()  # Load environment variables (like OpenAI API Key)

st.set_page_config(
    page_title="AURA: Career Architect",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for the "Pro" Aesthetic
st.markdown("""
<style>
    /* Chat Message Bubbles */
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f9fafb;
        border-right: 1px solid #e5e7eb;
    }
    /* Headers */
    h1 {
        font-family: 'Helvetica', sans-serif;
        color: #111827;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR: THE CONTROL PANEL ---
with st.sidebar:
    st.title("AURA ✨")
    st.caption("Adaptive User Readiness Agent")
    st.divider()

    # SECTION A: CONTEXT INGESTION
    st.subheader("1. Context Setup 📥")
    
    # Target Company Input
    target_company = st.text_input(
        "Target Company", 
        value="Cognizant (CTS)",
        help="AURA will customize questions for this company."
    )
    
    # Resume Uploader
    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)", 
        type="pdf",
        help="AURA reads this to know your projects."
    )
    
    if uploaded_file:
        # 1. Save the file locally so the backend can read it
        save_path = os.path.join("data", "resume.pdf")
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 2. Trigger the Ingestion (The AI Processing)
        with st.spinner("🧠 Ingesting Resume..."):
            try:
                # We assume ingest_resume returns (text, vectorstore)
                # We just need it to run successfully
                ingest_resume(save_path)
                st.success("✅ Resume Indexed! Brain Ready.")
            except Exception as e:
                st.error(f"Ingestion Failed: {e}")
        
    st.divider()

    # SECTION B: MODE SWITCH
    st.subheader("2. Select Mode 🔀")
    mode = st.radio(
        "Choose your interaction style:",
        ["🛡️ Trainer Mode (Mentor)", "⚔️ Interview Mode (Simulation)"],
        index=0,
        help="Trainer explains answers. Interviewer tests you."
    )
    
    st.divider()
    
    # Utility Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        st.caption("v1.0.0")


# --- 3. MAIN CHAT INTERFACE ---
st.title("Interview Simulation Workspace")
st.caption(f"Currently connected to: **{target_company}** Knowledge Base")

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add a welcoming starting message
    welcome_msg = "Hello! I am AURA. Upload your resume and tell me which company you are prepping for. Shall we start?"
    st.session_state.messages.append(AIMessage(content=welcome_msg))

# Display Existing Chat History
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(message.content)

# --- 4. THE INTERACTION LOOP ---
user_input = st.chat_input("Type your answer or ask a question...")

if user_input:
    # A. Display User Message Immediately
    st.chat_message("user", avatar="🧑‍💻").markdown(user_input)
    st.session_state.messages.append(HumanMessage(content=user_input))

    # B. Prepare State for Backend (The "Brain")
    # This dictionary is what we will pass to LangGraph
    current_state = {
        "messages": st.session_state.messages,
        "target_company": target_company,
        "mode": "trainer" if "Trainer" in mode else "interviewer",
        "resume_context": "Resume data would go here" # Placeholder
    }

    # C. Call the Agent (Placeholder for now)
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("AURA is thinking..."):
            
            # --- CRITICAL: CONNECTION TO BACKEND ---
            # Right now, we simulate a response because src.graph isn't built yet.
            # Once we build src/graph.py, we will uncomment the real import.
            
            try:
                # Import the graph we just built
                from src.graph import graph
                
                # Run the Graph!
                # We use .invoke() to send the state in and get the result out
                response = graph.invoke(current_state)
                
                # Extract the final AI message
                ai_response = response["messages"][-1].content
            
            except Exception as e:
                ai_response = f"⚠️ Error: {str(e)}"
            
            # Display the response
            st.markdown(ai_response)
    
    # D. Save AI Response to History
    st.session_state.messages.append(AIMessage(content=ai_response))