from __future__ import annotations
from typing import Any, Dict

from langgraph.graph import StateGraph, END

from app.agents.tool_discovery.agent_main import run_tool_discovery
from app.agents.planner.agent_main import run_planner
from app.agents.validator.agent_main import run_validator
from app.agents.executor.agent_main import run_executor
from app.agents.report.agent_main import run_report


def route_entry(state: Dict[str, Any]) -> str:
    status = state.get("status")
    if status == "READY_TO_EXECUTE":
        return "executor"
    return "tool_discovery"


def route_after_validator(state: Dict[str, Any]) -> str:
    status = state.get("status")
    if status == "WAITING_FOR_APPROVAL":
        return END
    if status == "READY_TO_EXECUTE":
        return "executor"
    return END


def route_after_executor(state: Dict[str, Any]) -> str:
    status = state.get("status")
    if status == "DONE":
        return "report"
    return END


def build_graph():
    sg = StateGraph(dict)

    sg.add_node("tool_discovery", run_tool_discovery)
    sg.add_node("planner", run_planner)
    sg.add_node("validator", run_validator)
    sg.add_node("executor", run_executor)
    sg.add_node("report", run_report)

    sg.set_conditional_entry_point(route_entry)

    sg.add_edge("tool_discovery", "planner")
    sg.add_edge("planner", "validator")

    sg.add_conditional_edges("validator", route_after_validator)
    sg.add_conditional_edges("executor", route_after_executor)

    sg.add_edge("report", END)

    return sg.compile()
