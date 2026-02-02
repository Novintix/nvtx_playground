import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import streamlit as st
from dotenv import load_dotenv

from ingestion.ingest import load_financial_data, load_policy_data
from vector_store.store import create_vector_store, retrieve_context
from reasoning.graph import build_graph
from MCP.guard import authorize, audit_log

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
    policy_docs = load_policy_data("data/sales_policy.txt")
    return create_vector_store(finance_docs + policy_docs)

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

    # 2. Audit & Governance
    # Check permissions BEFORE processing
    allowed = authorize(query, user_role=user_role)
    audit_log(query, user=user_id, role=user_role, outcome="Allowed" if allowed else "Blocked")

    if not allowed:
        error_msg = f"🚫 Access Denied: Your role '{user_role}' is not authorized to perform this action."
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.stop()

    # 3. Retrieve Context
    context = retrieve_context(vectordb, query)

    # 4. Agent Reasoning
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

    # 5. Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "financial_context": context.get("financial_context"),
        "policy_context": context.get("policy_context")
    })
