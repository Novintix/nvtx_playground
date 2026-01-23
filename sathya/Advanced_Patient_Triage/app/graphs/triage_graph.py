# app/graphs/triage_graph.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END

from app.agents.risk_hypothesis.agent_main import run_risk_agent
from app.agents.risk_scoring_safety.agent_main import run_risk_scoring_agent
from app.agents.specialist_routing.agent_main import run_specialist_routing_agent
from app.agents.human_escalation.agent_main import run_human_escalation_agent


class TriageGraphState(TypedDict, total=False):
    # Inputs to the graph (coming from your /triage/continue when ready)
    identified_symptoms: List[str]
    clinical_notes: Dict[str, Any]

    # Outputs added by nodes
    risk_agent: Dict[str, Any]
    risk_scoring_agent: Dict[str, Any]
    specialist_routing_agent: Dict[str, Any]
    human_escalation_agent: Dict[str, Any]

    next_step: str  # "human_escalation" | "specialist_routing"


async def node_agent2_risk(state: TriageGraphState) -> TriageGraphState:
    risk = await run_risk_agent(
        identified_symptoms=state["identified_symptoms"],
        clinical_notes=state["clinical_notes"],
    )
    state["risk_agent"] = risk.model_dump()
    return state


async def node_agent3_scoring(state: TriageGraphState) -> TriageGraphState:
    risk_scoring = await run_risk_scoring_agent(
        risk_output=state["risk_agent"],
        clinical_notes=state["clinical_notes"],
    )
    state["risk_scoring_agent"] = risk_scoring.model_dump()
    return state


async def node_agent4_routing(state: TriageGraphState) -> TriageGraphState:
    routing = await run_specialist_routing_agent(
        identified_symptoms=state["identified_symptoms"],
        clinical_notes=state["clinical_notes"],
        risk_hypothesis=state["risk_agent"],
        risk_scoring=state["risk_scoring_agent"],
    )
    state["specialist_routing_agent"] = routing.model_dump()
    return state


async def node_agent5_human_escalation(state: TriageGraphState) -> TriageGraphState:
    escalation = await run_human_escalation_agent(
        identified_symptoms=state["identified_symptoms"],
        clinical_notes=state["clinical_notes"],
        risk_hypothesis=state["risk_agent"],
        risk_scoring=state["risk_scoring_agent"],
        routing_hint=state.get("specialist_routing_agent"),
    )
    state["human_escalation_agent"] = escalation.model_dump()
    return state


def route_after_agent3(state: TriageGraphState) -> str:
    scoring = state.get("risk_scoring_agent", {}) or {}
    level = str(scoring.get("risk_level", "")).upper()
    flags = scoring.get("safety_flags", []) or []

    high_by_level = (level == "HIGH")
    high_by_flag = any(str(f).lower() == "requires_immediate_attention" for f in flags)

    if high_by_level or high_by_flag:
        state["next_step"] = "human_escalation"
        return "agent5_human_escalation"

    state["next_step"] = "specialist_routing"
    return "agent4_specialist_routing"


def build_triage_graph():
    g = StateGraph(TriageGraphState)

    g.add_node("agent2_risk", node_agent2_risk)
    g.add_node("agent3_scoring", node_agent3_scoring)
    g.add_node("agent4_specialist_routing", node_agent4_routing)
    g.add_node("agent5_human_escalation", node_agent5_human_escalation)

    # Flow: 2 -> 3 -> conditional -> 4 or 5 -> END
    g.set_entry_point("agent2_risk")
    g.add_edge("agent2_risk", "agent3_scoring")

    g.add_conditional_edges(
        "agent3_scoring",
        route_after_agent3,
        {
            "agent4_specialist_routing": "agent4_specialist_routing",
            "agent5_human_escalation": "agent5_human_escalation",
        },
    )

    g.add_edge("agent4_specialist_routing", END)
    g.add_edge("agent5_human_escalation", END)

    return g.compile()


TRIAGE_GRAPH = build_triage_graph()
