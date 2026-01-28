import operator
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The state of our graph.
    It tracks the conversation history, the user's settings, and context.
    """
    # The chat history (List of Human/AI messages)
    # operator.add ensures that new messages are appended, not overwritten
    messages: Annotated[List[BaseMessage], operator.add]
    
    # The user's settings from the Sidebar
    mode: str           # "trainer" or "interviewer"
    target_company: str # e.g. "CTS", "Adobe"
    
    # RAG Context
    resume_text: str    # The raw text extracted from the PDF
    retrieved_docs: str # The specific chunks found relevant for the current query