import streamlit as st
from src.services.mcp_service import mcp_service

def render_compliance_handshake(user_role):
    """
    Renders the interactive compliance handshake UI for pending policy updates.
    """
    if "pending_update" not in st.session_state:
        return

    pending = st.session_state.pending_update
    prop = pending.get("prop")
    hurdles = pending.get("hurdles", [])

    st.warning("⚖️ **Governance Review Required**")
    
    # 1. Display Hurdles
    if hurdles:
        st.markdown("##### Detected Hurdles & Risks")
        for hurdle in hurdles:
            st.error(f"🚩 {hurdle}")
    
    # 2. Display Proposed Change
    if prop:
        with st.expander(f"📝 Proposed Update for {prop.get('policy_name', 'POLICY').upper()}", expanded=True):
            st.code(prop.get('new_content', ''), language="text")
            
            if user_role == "Admin":
                if st.button("Confirm and Apply Change", key="confirm_btn"):
                    with st.spinner("Applying Governance Action..."):
                        final_result = mcp_service.call(
                            "update_policy_document",
                            policy_name=prop['policy_name'],
                            new_content=prop['new_content'],
                            user_role=user_role
                        )
                        if final_result and "Success" in final_result:
                            st.success(final_result)
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": f"### ✅ Policy Updated\n{final_result}\n\n*Applied by Admin via Interactive Approval*"
                            })
                            # Clear session and refresh
                            del st.session_state.pending_update
                            from src.utils.persistence import save_chat_history
                            save_chat_history(st.session_state.messages, user_role)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to apply update: {final_result}")
            else:
                st.info("🔒 This modification is pending Admin approval.")
    
    if st.button("Cancel Proposed Change", key="cancel_btn"):
        del st.session_state.pending_update
        st.rerun()
