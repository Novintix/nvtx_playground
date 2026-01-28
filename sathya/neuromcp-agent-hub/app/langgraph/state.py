from __future__ import annotations
from typing import Any, Dict, List, TypedDict

class GraphState(TypedDict, total=False):
    user_request: str
    available_tools: List[Dict[str, Any]]
    plan: Dict[str, Any]
    validation: Dict[str, Any]
    pending_approvals: List[Dict[str, Any]]
    status: str
    logs: List[Dict[str, str]]
