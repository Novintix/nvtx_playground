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

# Premium Professional Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #F8FAFC;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Header */
    .app-header {
        background: #0B0B45;
        padding: 2.5rem 2rem;
        border-radius: 24px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(11, 11, 69, 0.3);
    }
    
    .app-title {
        font-size: 2.75rem;
        font-weight: 700;
        color: white;
        margin: 0;
        letter-spacing: -0.03em;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .app-subtitle {
        color: rgba(255,255,255,0.85);
        font-size: 1.125rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: white !important;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
    }
    
    [data-testid="stSidebar"] > div {
        padding: 2rem 1.5rem;
    }
    
    .sidebar-title {
        font-size: 0.875rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1.5rem;
    }
    
    /* Status Cards */
    .service-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .service-card:hover {
        border-color: #0B0B45;
        box-shadow: 0 8px 24px rgba(11, 11, 69, 0.15);
        transform: translateY(-2px);
    }
    
    .service-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .service-icon {
        font-size: 1.5rem;
    }
    
    .service-info {
        flex: 1;
        margin-left: 0.75rem;
    }
    
    .service-name {
        font-size: 0.9375rem;
        font-weight: 600;
        color: #1E293B;
    }
    
    .service-status {
        font-size: 0.8125rem;
        color: #64748B;
        margin-top: 0.125rem;
    }
    
    .status-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 0.375rem;
    }
    
    .status-connected { background: #10B981; }
    .status-disconnected { background: #EF4444; }
    
    /* Input Area */
    .stTextArea > label {
        font-size: 0.9375rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        margin-bottom: 0.75rem !important;
    }
    
    .stTextArea textarea {
        background: white !important;
        border: 2px solid #E2E8F0 !important;
        border-radius: 16px !important;
        font-size: 1rem !important;
        padding: 1.25rem !important;
        color: #1E293B !important;
        transition: all 0.2s ease !important;
        line-height: 1.6 !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #0B0B45 !important;
        box-shadow: 0 0 0 4px rgba(11, 11, 69, 0.1) !important;
    }
    
    .stTextArea textarea::placeholder {
        color: #94A3B8 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #0B0B45 !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.875rem 1.75rem !important;
        font-weight: 600 !important;
        font-size: 0.9375rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(11, 11, 69, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(11, 11, 69, 0.5) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 16px;
        padding: 0.5rem;
        gap: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #64748B !important;
        border-radius: 12px !important;
        padding: 0.875rem 1.75rem !important;
        font-weight: 600 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: #0B0B45 !important;
        color: white !important;
    }
    
    /* Results Container */
    .results-box {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        margin-bottom: 1.5rem;
        animation: slideUp 0.4s ease-out;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .section-header {
        font-size: 1.125rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #F1F5F9;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Alert Boxes */
    .alert {
        padding: 1.25rem 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-weight: 600;
        animation: slideUp 0.3s ease-out;
    }
    
    .alert-success {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        color: #047857;
        border-left: 4px solid #10B981;
    }
    
    .alert-error {
        background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
        color: #DC2626;
        border-left: 4px solid #EF4444;
    }
    
    .alert-icon {
        font-size: 1.5rem;
    }
    
    /* Log Items */
    .log-container {
        max-height: 500px;
        overflow-y: auto;
    }
    
    .log-item {
        background: #F8FAFC;
        border-left: 3px solid #0B0B45;
        padding: 1rem 1.25rem;
        margin: 0.625rem 0;
        border-radius: 10px;
        transition: all 0.2s ease;
        font-size: 0.9375rem;
    }
    
    .log-item:hover {
        background: #F1F5F9;
        transform: translateX(4px);
    }
    
    .log-agent {
        color: #0B0B45;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        text-transform: capitalize;
        font-size: 0.875rem;
    }
    
    .log-message {
        color: #475569;
        margin-top: 0.25rem;
        line-height: 1.6;
    }
    
    /* Result Cards */
    .result-item {
        background: linear-gradient(135deg, #FAFAFA 0%, #FFFFFF 100%);
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.75rem;
        margin-bottom: 1rem;
    }
    
    .result-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .badge-success {
        background: #D1FAE5;
        color: #047857;
    }
    
    .result-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 0.75rem;
    }
    
    .result-detail {
        color: #64748B;
        font-size: 0.9375rem;
        line-height: 1.6;
    }
    
    .result-link {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        color: #0B0B45;
        font-weight: 600;
        text-decoration: none;
        margin-top: 0.75rem;
        transition: all 0.2s ease;
    }
    
    .result-link:hover {
        color: #1a1a6e;
        gap: 0.625rem;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }
    
    /* Streamlit Components */
    .stSuccess {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%) !important;
        color: #047857 !important;
        border-left: 4px solid #10B981 !important;
        border-radius: 12px !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%) !important;
        color: #1E40AF !important;
        border-left: 4px solid #3B82F6 !important;
        border-radius: 12px !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F1F5F9;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="app-header">
    <div class="app-title">🤖 NeuroMCP Agent Hub</div>
    <div class="app-subtitle">Enterprise AI Agent Platform with Multi-Tool Integration</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-title">🔐 Service Connections</div>', unsafe_allow_html=True)
    
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
    status_text = "Connected" if google_connected else "Not Connected"
    status_class = "connected" if google_connected else "disconnected"
    
    st.markdown(f"""
    <div class="service-card">
        <div class="service-header">
            <span class="service-icon">📅</span>
            <div class="service-info">
                <div class="service-name">Google Calendar</div>
                <div class="service-status">
                    <span class="status-dot status-{status_class}"></span>{status_text}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not google_connected:
        if st.button("🔗 Connect", key="google_btn", use_container_width=True):
            st.markdown(f"[Authorize →]({API_BASE_URL}/auth/google/login)")
    
    # Slack
    status_text = "Connected" if slack_connected else "Not Connected"
    status_class = "connected" if slack_connected else "disconnected"
    
    st.markdown(f"""
    <div class="service-card">
        <div class="service-header">
            <span class="service-icon">💬</span>
            <div class="service-info">
                <div class="service-name">Slack Workspace</div>
                <div class="service-status">
                    <span class="status-dot status-{status_class}"></span>{status_text}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not slack_connected:
        if st.button("🔗 Connect", key="slack_btn", use_container_width=True):
            st.markdown(f"[Authorize →]({API_BASE_URL}/auth/slack/login)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Backend status
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        backend_online = response.status_code == 200
    except:
        backend_online = False
    
    status_text = "Online" if backend_online else "Offline"
    status_class = "connected" if backend_online else "disconnected"
    
    st.markdown(f"""
    <div class="service-card">
        <div class="service-header">
            <span class="service-icon">⚡</span>
            <div class="service-info">
                <div class="service-name">Backend API</div>
                <div class="service-status">
                    <span class="status-dot status-{status_class}"></span>{status_text}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main tabs
tab1, tab2 = st.tabs(["🚀 Agent Execution", "📊 Execution History"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # User input
    user_request = st.text_area(
        "💬 Your Request",
        placeholder="Describe what you'd like the agent to do...\n\nExample: Create a team meeting for Feb 5 at 6pm with sathya@company.com",
        height=120,
        key="user_input"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 6])
    
    with col1:
        run_button = st.button("▶️ Execute", type="primary", use_container_width=True)
    
    if run_button and user_request:
        with st.spinner("⚙️ Processing..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/agent/run",
                    json={"user_request": user_request},
                    timeout=120  # Increased to 120 seconds for validation + LLM processing
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Status
                    status = result.get("status", "UNKNOWN")
                    if status in ["COMPLETED", "DONE"]:
                        st.markdown("""
                        <div class="alert alert-success">
                            <span class="alert-icon">✅</span>
                            <span>Execution Completed Successfully</span>
                        </div>
                        """, unsafe_allow_html=True)
                    elif status == "FAILED":
                        st.markdown("""
                        <div class="alert alert-error">
                            <span class="alert-icon">❌</span>
                            <span>Execution Failed</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Execution logs (cleaned)
                    if result.get("logs"):
                        st.markdown('<div class="results-box">', unsafe_allow_html=True)
                        st.markdown('<div class="section-header">📝 Execution Trace</div>', unsafe_allow_html=True)
                        st.markdown('<div class="log-container">', unsafe_allow_html=True)
                        
                        for log in result["logs"]:
                            agent = log.get("agent", "system")
                            msg = log.get("msg", "")
                            
                            # Skip showing raw JSON plans in logs
                            if "Generated plan:" in msg or '"goal":' in msg or '"steps":' in msg:
                                # Show simplified version
                                msg = "Plan created successfully with multiple steps."
                            
                            st.markdown(
                                f'<div class="log-item">'
                                f'<div class="log-agent">{agent}</div>'
                                f'<div class="log-message">{msg}</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        
                        st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    # Results
                    if result.get("execution_results"):
                        st.markdown('<div class="results-box">', unsafe_allow_html=True)
                        st.markdown('<div class="section-header">📊 Results</div>', unsafe_allow_html=True)
                        
                        results = result["execution_results"]
                        
                        for step_id, step_result in results.items():
                            if isinstance(step_result, dict):
                                # Calendar event (check FIRST before summary, since it also has 'summary')
                                if step_result.get("html_link"):
                                    st.markdown(f"""
                                    <div class="result-item">
                                        <div class="result-badge badge-success">✅ Calendar Event Created</div>
                                        <div class="result-title">📅 {step_result.get('summary', 'Event')}</div>
                                        <div class="result-detail">
                                            🕒 {step_result.get('start')} → {step_result.get('end')}
                                        </div>
                                        <a href="{step_result['html_link']}" class="result-link" target="_blank">
                                            View in Google Calendar →
                                        </a>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # Slack message posted
                                elif step_result.get("success") and step_result.get("ts"):
                                    st.markdown("""
                                    <div class="result-item">
                                        <div class="result-badge badge-success">✅ Message Posted to Slack</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # AI Summary or formatted messages (check AFTER calendar/slack)
                                elif step_result.get("summary"):
                                    message_count = step_result.get("message_count", 0)
                                    if message_count > 0:
                                        st.markdown(f"""
                                        <div class="result-item">
                                            <div class="result-badge badge-success">✅ Summary Generated</div>
                                            <div class="result-detail">{step_result['summary']}</div>
                                            <div style="margin-top: 0.75rem; color: #94A3B8; font-size: 0.875rem;">
                                                📊 Analyzed {message_count} messages
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        # Formatted messages
                                        st.markdown(f"""
                                        <div class="result-item">
                                            <div class="result-badge badge-success">✅ Messages Retrieved</div>
                                            <div class="result-detail">{step_result['summary']}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Raw data
                        with st.expander("🔍 View Technical Details"):
                            st.json(results)
                    
                else:
                    st.markdown(f"""
                    <div class="alert alert-error">
                        <span class="alert-icon">❌</span>
                        <span>Server Error: {response.status_code}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except requests.exceptions.Timeout:
                st.markdown("""
                <div class="alert alert-error">
                    <span class="alert-icon">⏱️</span>
                    <span>Request timeout - Please try again</span>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class="alert alert-error">
                    <span class="alert-icon">❌</span>
                    <span>Error: {str(e)}</span>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="results-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📊 Execution History</div>', unsafe_allow_html=True)
    st.info("💡 Coming soon - View past executions and analytics")
    st.markdown('</div>', unsafe_allow_html=True)
