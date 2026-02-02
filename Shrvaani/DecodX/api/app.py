import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import streamlit as st
from dotenv import load_dotenv

from ingestion.ingest import load_financial_data, load_policy_data
from vector_store.store import create_vector_store, retrieve_context
from reasoning.graph import build_graph
from MCP.guard import authorize, audit_log, log_request_approval, audit_exit

# ---------------------------------------
# ---------------------------------------
load_dotenv()

st.set_page_config(
    page_title="DecodX — Enterprise Intelligence Agent",
    layout="wide"
)

# ---------------------------------------
# Sidebar: Governance & Simulation
# ---------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50) # Placeholder icon
    st.title("DecodX Control Panel")
    
    st.subheader("👤 User Identity (MCP)")
    user_role = st.selectbox(
        "Simulated Role",
        ["Guest", "Analyst", "Admin"],
        help="Simulates different user permissions validated by the MCP layer."
    )
    user_id = "simulated_user_01"
    st.success(f"Logged in as: {user_role}")

    st.subheader("🗓️ Scheduled Triggers")
    if st.button("Trigger Monthly Review"):
        st.toast("Running Monthly Financial Review...")
        # In a real app, this would call the scheduler or a background task
        # For Demo, we populate the chat with the trigger message
        st.session_state.trigger_query = "What is the monthly financial review status?"

st.title("DecodX — Decision Intelligence Agent")
st.caption("AI-assisted decision support · Grounded · Auditable")

# ---------------------------------------
@st.cache_resource
def init_vector_store():
    finance_docs = load_financial_data("data/sample_finance.csv")
    sales_policy = load_policy_data("data/sales_policy.txt")
    hr_policy = load_policy_data("data/hr_policy.txt")
    return create_vector_store(finance_docs + sales_policy + hr_policy)

def init_agent():
    return build_graph()

vectordb = init_vector_store()
agent = init_agent()

# ---------------------------------------
# Chat Logic
# ---------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# Check for manual trigger
if "trigger_query" in st.session_state:
    query = st.session_state.pop("trigger_query")
    st.session_state.messages.append({"role": "user", "content": query})

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "financial_context" in message:
            with st.expander("📎 Financial Evidence"):
                st.write(message["financial_context"])
        if "policy_context" in message:
            with st.expander("📎 Policy Evidence"):
                st.write(message["policy_context"])

# Handle new input
if query := st.chat_input("Ask a question (e.g. Why are sales lower in the South region?)"):
    # 1. Add user message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 2. MCP Entry Point Audit
    audit_log(query, user=user_id, role=user_role, outcome="Processing")
    
    # 3. Governance Check
    allowed = authorize(query, user_role=user_role)
    
    # 4. Log Approval Decision
    if not allowed:
        reason = f"Role '{user_role}' not authorized for this query"
        log_request_approval(query, user=user_id, role=user_role, approved=False, reason=reason)
        
        error_msg = f"🚫 Access Denied: Your role '{user_role}' is not authorized to perform this action."
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Exit Audit
        audit_exit(query, user=user_id, role=user_role, status="Blocked", response_summary="Access Denied")
        st.stop()
    
    # Request Approved
    log_request_approval(query, user=user_id, role=user_role, approved=True)

    # 5. Retrieve Context
    context = retrieve_context(vectordb, query)

    # 6. Agent Reasoning
    state = {
        "query": query,
        "financial_context": context["financial_context"],
        "policy_context": context["policy_context"],
        "analysis": "",
        "comparison": "",
        "policy_check": "",
        "recommendations": "",
        "final_answer": ""
    }

    with st.chat_message("assistant"):
        with st.spinner("DecodX is reasoning..."):
            result = agent.invoke(state)
            
            response_content = result["final_answer"]
            st.markdown(response_content)

            # Show evidence
            if context["financial_context"]:
                with st.expander("📎 Financial Evidence"):
                    st.write(context["financial_context"])
            if context["policy_context"]:
                with st.expander("📎 Policy Evidence"):
                    st.write(context["policy_context"])

    # 7. MCP Exit Point Audit
    response_length = len(response_content)
    audit_exit(query, user=user_id, role=user_role, status="Success", response_summary=f"{response_length} chars")
    
    # 8. Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "financial_context": context.get("financial_context"),
        "policy_context": context.get("policy_context")
    })
