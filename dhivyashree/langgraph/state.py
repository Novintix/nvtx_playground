from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    topic: str
    messages: Annotated[List[BaseMessage], operator.add]
    pro_argument: str
    con_argument: str
    verdict: str
