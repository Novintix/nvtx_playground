from __future__ import annotations
from typing import Any, Dict

from app.agents.validator.agent import validate_plan_neurosymbolic

def run_validator(state: Dict[str, Any]) -> Dict[str, Any]:
    plan = state.get("plan")
    tools = state.get("available_tools", [])

    logs = state.get("logs", [])
    logs.append({"agent": "validator", "msg": "Running neurosymbolic validation rules..."})

    validation, pending, patched_plan = validate_plan_neurosymbolic(
        plan=plan,
        available_tools=tools,
        default_timezone="Asia/Kolkata",
    )

    state["validation"] = validation.model_dump()
    state["pending_approvals"] = [p.model_dump() for p in pending]
    state["plan"] = patched_plan

    if not validation.valid:
        state["status"] = "ERROR"
        logs.append({"agent": "validator", "msg": f"Validation failed: {validation.errors}"})
    elif len(pending) > 0:
        state["status"] = "WAITING_FOR_APPROVAL"
        logs.append({"agent": "validator", "msg": f"Waiting for approval for steps: {[p.step_id for p in pending]}"})
    else:
        state["status"] = "READY_TO_EXECUTE"
        logs.append({"agent": "validator", "msg": "Validation passed. No approvals needed."})

    state["logs"] = logs
    return state

   