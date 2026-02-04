import os
from langchain_groq import ChatGroq
from backend.config.settings import LLM_MODEL

# Initializes and returns a configured ChatGroq instance.
def get_llm():
    """Returns a configured ChatGroq instance."""
    return ChatGroq(
        temperature=0,
        model_name=LLM_MODEL,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

# Utility to directly generate completions from the LLM.
def generate_response(prompt):
    """Directly generates a response using the LLM."""
    llm = get_llm()
    return llm.invoke(prompt).content
