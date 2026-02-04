import sys
from pathlib import Path

# Corporate Pathing
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import json
import os
from src.services.mcp_service import mcp_service
from src.layouts.sidebar import render_sidebar
from src.layouts.header import render_header
from src.components.chat_interface import render_chat_messages, get_chat_input
from src.components.dashboard import render_analytics_dashboard
from src.components.compliance_approval import render_compliance_handshake
from src.utils.persistence import save_chat_history, load_chat_history

# 1. Setup
st.set_page_config(
    page_title="DecodX — Decision Intelligence",
    page_icon="🤖",
    layout="wide"
)

# 3. Session Initialization
if "user_role" not in st.session_state:
    st.session_state.user_role = "Guest"

# Handle Role-Specific History Loading
if "messages" not in st.session_state or st.session_state.get("last_loaded_role") != st.session_state.user_role:
    st.session_state.messages = load_chat_history(st.session_state.user_role)
    st.session_state.last_loaded_role = st.session_state.user_role

# 4. Load Custom Styling
css_path = SRC_DIR / "assets" / "css" / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 5. Render Layout
render_sidebar()
render_header()

user_role = st.session_state.user_role
user_id = "simulated_user_01"

# 6. Chat Logic
if "trigger_query" in st.session_state:
    query = st.session_state.pop("trigger_query")
    st.session_state.messages.append({"role": "user", "content": query})

# Render Existing History
render_chat_messages(st.session_state.messages)

# Render Handshake if needed (Outside input loop for persistence)
render_compliance_handshake(user_role)

# 7. Handle New Input
if query := get_chat_input():
    st.session_state.messages.append({"role": "user", "content": query})
    save_chat_history(st.session_state.messages, user_role)
    
    with st.chat_message("user"):
        st.markdown(query)

    # Governance Audit & Auth
    mcp_service.call("audit_event", event_type="ENTRY", user_id=user_id, user_role=user_role, query=query, details="Corporate interaction started")
    
    auth_result = mcp_service.call("authorize_request", query=query, user_role=user_role)
    is_allowed = auth_result.get("allowed", False) if isinstance(auth_result, dict) else False
    
    if not is_allowed:
        reason = auth_result.get("reason", "Unauthorized") if isinstance(auth_result, dict) else "Blocked"
        st.error(f"🚫 Access Denied: {reason}")
        st.session_state.messages.append({"role": "assistant", "content": f"🚫 Access Denied: {reason}"})
        save_chat_history(st.session_state.messages, user_role)
        st.stop()

    # Visual Analytics
    financial_data = mcp_service.call("get_financial_data", user_role=user_role)
    render_analytics_dashboard(financial_data, user_role, query)

    # Retrieval & Reasoning
    with st.spinner("Retrieving grounded context..."):
        context = mcp_service.call("get_grounded_context", query=query, user_role=user_role)
        if not isinstance(context, dict):
            context = {"financial_context": [], "policy_context": []}

    with st.chat_message("assistant"):
        with st.spinner("Reasoning..."):
            # Prepare state for agent
            state = {
                "query": query,
                "user_role": user_role,
                "user_id": user_id,
                "financial_context": context.get("financial_context", []),
                "policy_context": context.get("policy_context", []),
                "analysis": "",
                "comparison": "",
                "policy_check": "",
                "recommendations": "",
                "final_answer": ""
            }
            
            result = mcp_service.call("execute_agent_reasoning", state_data=state)
            
            if result.get("interaction_needed"):
                st.session_state.pending_update = {
                    "prop": result.get("proposed_change", {}),
                    "hurdles": result.get("hurdles", [])
                }
                st.rerun()
            
            response_content = result.get("final_answer", "No response.")
            st.markdown(response_content)
            
            # Show Evidence
            if context.get("financial_context"):
                with st.expander("📎 Financial Evidence"):
                    st.write(context["financial_context"])
            if context.get("policy_context"):
                with st.expander("📎 Policy Evidence"):
                    st.write(context["policy_context"])

    # Final Audit & Save
    mcp_service.call("audit_event", event_type="EXIT", user_id=user_id, user_role=user_role, query=query, details="Success")
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "financial_context": context.get("financial_context"),
        "policy_context": context.get("policy_context")
    })
    save_chat_history(st.session_state.messages, user_role)
