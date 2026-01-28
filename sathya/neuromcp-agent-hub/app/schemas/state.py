from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict

class AgentState(TypedDict, total=False):
    user_request: str

    # tool discovery
    available_tools: List[Dict[str, Any]]

    # planner
    plan: Dict[str, Any]

    # validator
    status: str  # e.g., WAITING_FOR_APPROVAL, READY_TO_EXECUTE, DONE, ERROR
    pending_approvals: List[Dict[str, Any]]
    approved_step_ids: List[str]
    validation: Dict[str, Any]

    # executor
    execution_results: Dict[str, Any]

    # report
    final_report: str

    # logs
    logs: List[Dict[str, Any]]
