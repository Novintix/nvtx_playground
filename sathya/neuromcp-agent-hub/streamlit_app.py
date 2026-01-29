import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="NeuroMCP Agent Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.875rem;
        display: inline-block;
    }
    .status-connected {
        background-color: #d4edda;
        color: #155724;
    }
    .status-disconnected {
        background-color: #f8d7da;
        color: #721c24;
    }
    .log-item {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🤖 NeuroMCP Agent Hub</h1>', unsafe_allow_html=True)
st.markdown("**Intelligent AI Agent with Multi-Tool Integration**")
st.markdown("---")

# Sidebar - OAuth Connections
with st.sidebar:
    st.header("🔐 OAuth Connections")
    
    # Check OAuth status
    try:
        with open(".tokens.json", "r") as f:
            tokens = json.load(f)
            google_connected = "google" in tokens
            slack_connected = "slack" in tokens
    except:
        google_connected = False
        slack_connected = False
    
    # Google OAuth
    st.subheader("📅 Google Calendar")
    if google_connected:
        st.markdown('<span class="status-badge status-connected">✓ Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">✗ Not Connected</span>', unsafe_allow_html=True)
        if st.button("Connect Google Calendar", key="google_connect"):
            st.markdown(f"[Click here to connect]({API_BASE_URL}/auth/google/login)")
    
    st.markdown("---")
    
    # Slack OAuth
    st.subheader("💬 Slack")
    if slack_connected:
        st.markdown('<span class="status-badge status-connected">✓ Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">✗ Not Connected</span>', unsafe_allow_html=True)
        if st.button("Connect Slack", key="slack_connect"):
            st.markdown(f"[Click here to connect]({API_BASE_URL}/auth/slack/login)")
    
    st.markdown("---")
    st.caption("🔗 Backend Status")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        if response.status_code == 200:
            st.success("✅ Backend Online")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Offline")

# Main content area
tab1, tab2, tab3 = st.tabs(["🚀 Agent Execution", "📊 Execution History", "⚙️ Settings"])

with tab1:
    st.header("Agent Execution")
    
    # User request input
    user_request = st.text_area(
        "What would you like the agent to do?",
        placeholder="Example: Schedule a team meeting for tomorrow at 2pm and send a Slack notification to #general",
        height=100
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        run_button = st.button("🚀 Run Agent", type="primary")
    
    with col2:
        if st.button("🗑️ Clear"):
            st.rerun()
    
    if run_button and user_request:
        with st.spinner("🔄 Agent is working..."):
            try:
                # Call the agent API
                response = requests.post(
                    f"{API_BASE_URL}/agent/run",
                    json={"user_request": user_request},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display status
                    st.subheader("📋 Execution Status")
                    status = result.get("status", "UNKNOWN")
                    if status == "COMPLETED":
                        st.success(f"✅ Status: {status}")
                    elif status == "FAILED":
                        st.error(f"❌ Status: {status}")
                    else:
                        st.info(f"ℹ️ Status: {status}")
                    
                    # Display plan
                    if result.get("plan"):
                        st.subheader("🎯 Execution Plan")
                        plan = result["plan"]
                        st.write(f"**Goal:** {plan.get('goal', 'N/A')}")
                        
                        if plan.get("steps"):
                            st.write("**Steps:**")
                            for step in plan["steps"]:
                                with st.expander(f"Step {step.get('id')}: {step.get('action')}"):
                                    st.json(step)
                    
                    # Display logs
                    if result.get("logs"):
                        st.subheader("📝 Execution Logs")
                        for log in result["logs"]:
                            st.markdown(
                                f'<div class="log-item"><strong>{log.get("agent", "System")}:</strong> {log.get("msg", "")}</div>',
                                unsafe_allow_html=True
                            )
                    
                    # Display execution results
                    if result.get("execution_results"):
                        st.subheader("📊 Results")
                        
                        # Show summary if available
                        for step_id, step_result in result["execution_results"].items():
                            if isinstance(step_result, dict) and step_result.get("summary"):
                                st.success("✅ AI Summary Generated!")
                                st.markdown("### 📝 Summary")
                                st.info(step_result.get("summary"))
                                st.caption(f"Analyzed {step_result.get('message_count', 0)} messages")
                                st.markdown("---")
                        
                        # Show calendar event links if available
                        for step_id, step_result in result["execution_results"].items():
                            if isinstance(step_result, dict) and step_result.get("html_link"):
                                st.success(f"✅ Event Created Successfully!")
                                st.markdown(f"**Event ID:** `{step_result.get('event_id')}`")
                                st.markdown(f"**📅 [View Event in Google Calendar]({step_result.get('html_link')})**")
                                st.write(f"**Title:** {step_result.get('summary')}") 
                                st.write(f"**Start:** {step_result.get('start')}")
                                st.write(f"**End:** {step_result.get('end')}")
                                st.markdown("---")
                        
                        # Show raw JSON for debugging
                        with st.expander("📋 Raw Response"):
                            st.json(result["execution_results"])
                        
                else:
                    st.error(f"❌ Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. The agent may still be processing.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with tab2:
    st.header("Execution History")
    st.info("📌 Feature coming soon! This will show past agent executions.")

with tab3:
    st.header("Settings")
    
    st.subheader("🔧 Configuration")
    
    mock_tools = st.checkbox("Enable Mock Tools", value=False)
    st.caption("Use mock tools instead of real API calls for testing")
    
    offline_planner = st.checkbox("Use Offline Planner", value=False)
    st.caption("Use rule-based planner instead of LLM-based planner")
    
    if st.button("Save Settings"):
        st.success("✅ Settings saved!")
    
    st.markdown("---")
    
    st.subheader("📊 System Info")
    st.write(f"**Backend URL:** {API_BASE_URL}")
    st.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Streamlit | NeuroMCP Agent Hub v1.0")
