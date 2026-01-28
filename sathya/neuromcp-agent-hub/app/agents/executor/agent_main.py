from __future__ import annotations
from typing import Any, Dict

from app.agents.executor.agent import execute_plan


async def run_executor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Executor Node
    Executes approved tool steps and stores execution_results in state.
    """
    logs = state.get("logs", [])
    logs.append({"agent": "executor", "msg": "Running executor..."})

    plan = state.get("plan", {})
    approved = state.get("approved_step_ids", []) or []

    state["execution_results"] = await execute_plan(plan, approved)

    # status handling
    results = state.get("execution_results", {})
    any_error = any(v.get("status") == "error" for v in results.values())
    any_blocked = any(v.get("status") == "blocked" for v in results.values())

    if any_error:
        state["status"] = "ERROR"
        logs.append({"agent": "executor", "msg": "Execution finished with errors."})
    elif any_blocked:
        state["status"] = "WAITING_FOR_APPROVAL"
        logs.append({"agent": "executor", "msg": "Execution blocked (missing approvals)."})
    else:
        state["status"] = "DONE"
        logs.append({"agent": "executor", "msg": "Execution completed successfully."})

    state["logs"] = logs
    return state
