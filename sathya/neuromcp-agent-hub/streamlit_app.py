import streamlit as st
import requests
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="NeuroMCP Agent Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

# Professional Dark Theme CSS
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-bg: #0A1628;
        --secondary-bg: #1B2838;
        --card-bg: #243447;
        --accent-blue: #3B82F6;
        --accent-purple: #8B5CF6;
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --success: #10B981;
        --error: #EF4444;
        --border: #334155;
    }
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #0A1628 0%, #1B2838 100%);
    }
    
    /* Header styling */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Connection card */
    .connection-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .connection-card:hover {
        border-color: var(--accent-blue);
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-connected {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-disconnected {
        background: rgba(239, 68, 68, 0.1);
        color: var(--error);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Input field */
    .stTextArea textarea {
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        padding: 1rem !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Results card */
    .result-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1.5rem;
    }
    
    .result-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
    }
    
    /* Log item */
    .log-item {
        background: var(--secondary-bg);
        border-left: 3px solid var(--accent-blue);
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
    
    .log-agent {
        color: var(--accent-blue);
        font-weight: 600;
    }
    
    /* Success/Error messages */
    .success-box {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 10px;
        padding: 1rem;
        color: var(--success);
        margin: 1rem 0;
    }
    
    .error-box {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 10px;
        padding: 1rem;
        color: var(--error);
        margin: 1rem 0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--secondary-bg);
        border-radius: 10px;
        padding: 0.5rem;
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent-blue) !important;
        color: white !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--card-bg) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--secondary-bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent-blue);
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown('<div class="main-header">🤖 NeuroMCP Agent Hub</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Enterprise AI Agent with Multi-Tool Integration</div>', unsafe_allow_html=True)

# Sidebar - Connection Status
with st.sidebar:
    st.markdown("### 🔐 Connection Status")
    
    # Check OAuth status
    try:
        with open(".tokens.json", "r") as f:
            tokens = json.load(f)
            google_connected = "google" in tokens
            slack_connected = "slack" in tokens
    except:
        google_connected = False
        slack_connected = False
    
    # Google Calendar
    st.markdown(f"""
    <div class="connection-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #F8FAFC; font-weight: 600;">📅 Google Calendar</span>
            <span class="status-badge status-{'connected' if google_connected else 'disconnected'}">
                {'✓ Connected' if google_connected else '✗ Disconnected'}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not google_connected:
        if st.button("Connect Calendar", key="google_btn"):
            st.markdown(f"[Click to Authorize →]({API_BASE_URL}/auth/google/login)")
    
    # Slack
    st.markdown(f"""
    <div class="connection-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #F8FAFC; font-weight: 600;">💬 Slack</span>
            <span class="status-badge status-{'connected' if slack_connected else 'disconnected'}">
                {'✓ Connected' if slack_connected else '✗ Disconnected'}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not slack_connected:
        if st.button("Connect Slack", key="slack_btn"):
            st.markdown(f"[Click to Authorize →]({API_BASE_URL}/auth/slack/login)")
    
    st.markdown("---")
    
    # Backend status
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        backend_status = "🟢 Online" if response.status_code == 200 else "🔴 Error"
    except:
        backend_status = "🔴 Offline"
    
    st.markdown(f"""
    <div class="connection-card">
        <div style="color: #94A3B8; font-size: 0.875rem; margin-bottom: 0.5rem;">Backend Status</div>
        <div style="color: #F8FAFC; font-weight: 600;">{backend_status}</div>
    </div>
    """, unsafe_allow_html=True)

# Main tabs
tab1, tab2 = st.tabs(["🚀 Agent Execution", "📊 History"])

with tab1:
    # User input
    user_request = st.text_area(
        "What would you like the agent to do?",
        placeholder="Example: Schedule a presentation meeting with sathya@email.com at 9pm feb 1 and send notification to #social",
        height=120,
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        run_button = st.button("▶️ Execute Agent", type="primary", use_container_width=True)
    
    if run_button and user_request:
        with st.spinner("🔄 Agent executing workflow..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/agent/run",
                    json={"user_request": user_request},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Status
                    status = result.get("status", "UNKNOWN")
                    if status == "COMPLETED":
                        st.markdown('<div class="success-box">✅ Execution Completed Successfully</div>', unsafe_allow_html=True)
                    elif status == "FAILED":
                        st.markdown('<div class="error-box">❌ Execution Failed</div>', unsafe_allow_html=True)
                    
                    # Execution logs
                    if result.get("logs"):
                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        st.markdown('<div class="result-header">📝 Execution Trace</div>', unsafe_allow_html=True)
                        for log in result["logs"]:
                            agent = log.get("agent", "system")
                            msg = log.get("msg", "")
                            st.markdown(
                                f'<div class="log-item"><span class="log-agent">{agent}:</span> {msg}</div>',
                                unsafe_allow_html=True
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Results
                    if result.get("execution_results"):
                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        st.markdown('<div class="result-header">📊 Results</div>', unsafe_allow_html=True)
                        
                        results = result["execution_results"]
                        
                        # Show summaries
                        for step_id, step_result in results.items():
                            if isinstance(step_result, dict):
                                # AI Summary
                                if step_result.get("summary") and step_result.get("message_count", 0) > 0:
                                    st.success("✅ AI Summary Generated")
                                    st.info(f"📝 {step_result['summary']}")
                                    st.caption(f"Analyzed {step_result['message_count']} messages")
                                
                                # Calendar event
                                elif step_result.get("html_link"):
                                    st.success("✅ Calendar Event Created")
                                    st.markdown(f"**📅 {step_result.get('summary')}**")
                                    st.markdown(f"🕒 {step_result.get('start')} → {step_result.get('end')}")
                                    st.markdown(f"[View in Google Calendar →]({step_result['html_link']})")
                                
                                # Slack message
                                elif step_result.get("success") and step_result.get("ts"):
                                    st.success("✅ Slack Message Posted")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Raw data (collapsed)
                        with st.expander("🔍 View Raw Response"):
                            st.json(results)
                    
                else:
                    st.markdown(f'<div class="error-box">❌ Error: {response.status_code}</div>', unsafe_allow_html=True)
                    
            except requests.exceptions.Timeout:
                st.markdown('<div class="error-box">⏱️ Request timeout - agent may still be processing</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="error-box">❌ Error: {str(e)}</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown('<div class="result-header">📊 Execution History</div>', unsafe_allow_html=True)
    st.info("Feature coming soon - view past agent executions and analytics")
    st.markdown('</div>', unsafe_allow_html=True)
