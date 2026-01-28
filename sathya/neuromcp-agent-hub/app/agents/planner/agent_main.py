from __future__ import annotations
from typing import Any, Dict

from app.agents.planner.agent import create_plan_with_groq
from app.utils.datetime_utils import normalize_relative_times






def run_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    user_request = state.get("user_request", "")
    tools = state.get("available_tools", [])

    logs = state.get("logs", [])
    logs.append({"agent": "planner", "msg": "Running Groq Planner Agent..."})

    plan_obj = create_plan_with_groq(user_request, tools)
    # after plan_obj created:
    plan_obj = normalize_relative_times(plan_obj, tz="Asia/Kolkata")

    state["plan"] = plan_obj.model_dump()
    logs.append({"agent": "planner", "msg": f"Plan created successfully with {len(plan_obj.steps)} steps."})

    state["logs"] = logs
    return state
