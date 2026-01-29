import streamlit as st
import os
import time
from dotenv import load_dotenv
from src.graph import create_drift_graph
from src.utils import read_file_content
from src.styles import CUSTOM_CSS
import src.db as db

load_dotenv()

st.set_page_config(page_title="DRIFT-X", layout="wide", page_icon="⚡")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Function to handle analysis ---
def run_analysis(room_id, uploaded_file, repo_url=None):
    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("Google API Key not found in .env file.")
        return

    with st.spinner("Analyzing discussion, requirements, and code..."):
        # Fetch full chat history
        messages = db.get_messages(room_id)
        chat_transcript = "\n".join([f"{m['username']} ({m['timestamp']}): {m['content']}" for m in messages])
        req_text = read_file_content(uploaded_file)
        
        # Run Graph
        graph = create_drift_graph()
        inputs = {
            "chat_transcript": chat_transcript,
            "requirement_text": req_text,
            "repo_url": repo_url
        }
        results = graph.invoke(inputs)
        return results

# --- Main Page Layout ---
st.title("DRIFT-X: Requirement Drift Tracker")

# Session State Initialization
if "current_view" not in st.session_state:
    st.session_state.current_view = "HOME"
if "room_id" not in st.session_state:
    st.session_state.room_id = None
if "username" not in st.session_state:
    st.session_state.username = "Anonymous"
if "drift_results" not in st.session_state:
    st.session_state.drift_results = None

# VIEW: HOME
if st.session_state.current_view == "HOME":
    st.subheader("Join or Start a Discussion")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Create New Room")
        create_id = st.text_input("Set Room ID", key="create_input")
        create_user = st.text_input("Your Username", key="create_user")
        
        if st.button("Create & Enter"):
            if create_id and create_user:
                if db.create_room(create_id):
                    st.session_state.room_id = create_id
                    st.session_state.username = create_user
                    st.session_state.current_view = "CHAT"
                    st.rerun()
                else:
                    st.error("Room ID already exists. Try another.")
            else:
                st.error("Please fill in both fields.")

    with col2:
        st.markdown("### Join Existing Room")
        join_id = st.text_input("Enter Chat ID")
        username_input = st.text_input("Enter your Username", value="User")
        
        if st.button("Join Room"):
            if db.join_room(join_id):
                st.session_state.room_id = join_id
                st.session_state.username = username_input
                st.session_state.current_view = "CHAT"
                st.rerun()
            else:
                st.error("Room ID not found.")

# VIEW: CHAT
elif st.session_state.current_view == "CHAT":
    room_id = st.session_state.room_id
    status = db.get_room_status(room_id)
    
    # Header Info
    col_info, col_end = st.columns([4, 1])
    with col_info:
        st.markdown(f"### 💬 Room: <span style='color:#00e5ff'>{room_id}</span>", unsafe_allow_html=True)
        st.caption(f"Status: {status} | User: {st.session_state.username}")
    with col_end:
         if status == 'ACTIVE':
            if st.button("End Discussion", type="primary"):
                db.end_room(room_id)
                st.rerun()

    # --- Chat Messages (Auto-refresh) ---
    @st.fragment(run_every=1)
    def display_messages(room_id, current_user):
        messages = db.get_messages(room_id)
        
        with st.container():
            if not messages:
                st.markdown("<div style='text-align:center; color:gray;'>_No messages yet. Start the conversation!_</div>", unsafe_allow_html=True)
            
            for msg in messages:
                is_me = msg['username'] == current_user
                role_class = "role-user" if is_me else "role-other"
                align_style = "text-align: right;" if is_me else "text-align: left;"
                
                # HTML Bubble
                html = f"""
                <div style="display: flex; flex-direction: column; {align_style} margin-bottom: 10px;">
                    <div style="font-size: 0.8em; color: gray; margin-bottom: 2px;">{msg['username']} • {msg['timestamp']}</div>
                    <div class="chat-bubble {role_class}">
                        {msg['content']}
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

    # Render the message fragment
    display_messages(room_id, st.session_state.username)

    # --- Active Chat Input ---
    if status == 'ACTIVE':
        # st.chat_input is sticky to bottom and works well with fragments
        if prompt := st.chat_input("Type your message..."):
            db.add_message(room_id, st.session_state.username, prompt)
            st.rerun()

    # --- Discussion Ended / Analysis ---
    elif status == 'ENDED':
        st.warning("Discussion has ended.")
        
        st.subheader("Requirement Analysis Phase")
        col_up, col_repo = st.columns(2)
        with col_up:
            uploaded_file = st.file_uploader("Upload Requirement Document (PDF/Text)", type=["txt", "pdf"])
        with col_repo:
            repo_url = st.text_input("GitHub Repo URL (Optional)", placeholder="https://github.com/owner/repo")
        
        if uploaded_file and st.button("Analyze for Drift"):
            results = run_analysis(room_id, uploaded_file, repo_url)
            st.session_state.drift_results = results
            st.rerun()

    # --- Results Display ---
    if st.session_state.drift_results:
        results = st.session_state.drift_results
        drift_data = results["drift_analysis"]
        disc_data = results["discussion_analysis"]
        req_data = results["requirement_intent"]
        code_data = results.get("code_analysis")

        st.divider()
        st.markdown("## Analysis Results")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 💬 Discussion Focus")
            st.info(f"**Summary:** {disc_data.summary}")
            st.markdown("**Primary Focus:**")
            for f in disc_data.primary_focus:
                st.markdown(f"- {f}")
        with col2:
            st.markdown("#### 📄 Requirement Intent")
            st.markdown("**Goals:**")
            for g in req_data.goals:
                st.markdown(f"- {g}")

        with col3:
            st.markdown("#### 💻 Code Compliance")
            if code_data:
                score = code_data.compliance_score
                st.progress(score, text=f"Score: {int(score*100)}%")
                st.markdown(f"**Verdict:** {code_data.verdict}")
                if code_data.missing_features:
                    with st.expander("Missing Features"):
                        for m in code_data.missing_features:
                            st.write(f"- {m}")
            else:
                st.caption("No Repo Provided")

        st.markdown("---")
        
        if drift_data.drift_detected:
            st.error(f"### 🚨 Drift Detected: {', '.join(drift_data.drift_type)}")
            st.markdown(f"**Explanation:** {drift_data.explanation}")
            st.markdown("#### 🕵️ Evidence")
            for ev in drift_data.evidence:
                st.warning(f"_{ev}_")
        else:
            st.success("### ✅ No Drift Detected")
            st.markdown(f"**Explanation:** {drift_data.explanation}")
        
    if st.button("Exit / Home"):
        st.session_state.current_view = "HOME"
        st.session_state.drift_results = None
        st.rerun()
