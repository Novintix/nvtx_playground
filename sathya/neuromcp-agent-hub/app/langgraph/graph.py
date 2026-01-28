from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.schemas.state import AgentState
from app.agents.tool_discovery.agent_main import run_tool_discovery
from app.agents.planner.agent_main import run_planner
from app.agents.validator.agent_main import run_validator
from app.agents.executor.agent_main import run_executor
from app.agents.report.agent_main import run_report


def _route_after_validator(state: AgentState) -> str:
    # If validator says we need approvals, stop here.
    if state.get("status") == "WAITING_FOR_APPROVAL":
        return END

    # Otherwise proceed to execution
    return "executor"


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("tool_discovery", run_tool_discovery)
    g.add_node("planner", run_planner)
    g.add_node("validator", run_validator)
    g.add_node("executor", run_executor)
    g.add_node("report", run_report)

    g.set_entry_point("tool_discovery")

    g.add_edge("tool_discovery", "planner")
    g.add_edge("planner", "validator")

    g.add_conditional_edges("validator", _route_after_validator)

    g.add_edge("executor", "report")
    g.add_edge("report", END)

    return g.compile()
