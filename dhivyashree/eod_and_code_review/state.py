from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    git_context: Optional[str]
    task_logs: Optional[str]
    reasoning: Optional[str]
    eod_update: Optional[str]
    daily_standup: Optional[str]
