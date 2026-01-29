import operator
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The state of our graph.
    It tracks the conversation history, the user's settings, and context.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    mode: str
    target_company: str
    resume_text: str     # Raw text for broad context
    retrieved_docs: str  # RAG + Search results