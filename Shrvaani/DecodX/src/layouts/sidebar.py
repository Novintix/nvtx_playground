import streamlit as st
import os
from src.services.mcp_service import mcp_service

def render_sidebar():
    """
    Renders the corporate-branded sidebar for DecodX.
    """
    with st.sidebar:
        st.markdown('<div class="sidebar-label">Identity Support</div>', unsafe_allow_html=True)
        st.title("DecodX Control")
        
        st.markdown('<div class="sidebar-label">👤 User Context</div>', unsafe_allow_html=True)
        
        role_options = ["Guest", "Analyst", "Admin"]
        
        try:
            current_role_index = role_options.index(st.session_state.get("user_role", "Guest"))
        except ValueError:
            current_role_index = 0

        user_role = st.selectbox(
            "Simulated Role",
            role_options,
            index=current_role_index,
            label_visibility="collapsed",
            help="Simulates different user permissions validated by the MCP layer.",
            key="role_selector"
        )
        
        if st.session_state.get("user_role") != user_role:
            st.session_state.user_role = user_role
            st.rerun()

        status_color = "#10b981" if user_role == "Admin" else "#f59e0b" if user_role == "Analyst" else "#94a3b8"
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid {status_color};'>
                <small style='color: #94a3b8;'>ACTIVE IDENTITY</small><br>
                <b>{user_role}</b>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-label">🗓️ Automated Triggers</div>', unsafe_allow_html=True)
        if st.button("Generate Monthly Audit"):
            st.toast("Synthesizing Monthly Financial Review...")
            st.session_state.trigger_query = "Perform a monthly financial review. Compare this year's sales to last year's."



        st.markdown('<div class="sidebar-label">🛡️ Governance Status</div>', unsafe_allow_html=True)
        
        # Check Connectivity (Simulated with simple tool call)
        test_auth = mcp_service.call("authorize_request", query="health_check", user_role="Guest")
        if test_auth:
            st.markdown('<div class="mcp-badge">● BACKEND LIVE</div> <div class="mcp-badge">● AUDIT ACTIVE</div>', unsafe_allow_html=True)
        else:
            st.error("⚠️ MCP Server Offline")
            st.warning("Please run: `python3 backend/main.py` in a separate terminal.")
