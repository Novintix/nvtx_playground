import streamlit as st

def render_chat_messages(messages):
    """
    Renders the conversation history with semantic iconography.
    """
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "financial_context" in message and message["financial_context"]:
                with st.expander("📎 Financial Evidence"):
                    st.write(message["financial_context"])
            if "policy_context" in message and message["policy_context"]:
                with st.expander("📎 Policy Evidence"):
                    st.write(message["policy_context"])

def get_chat_input():
    """
    Returns the user input from the chat bar.
    """
    return st.chat_input("Ask a question (e.g. Why are sales lower in the South region?)")
