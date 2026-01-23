from __future__ import annotations

from typing import Any, Dict, Optional, Literal
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from app.services.session_service import create_session, get_session, update_session
from app.services.question_policy import enforce_followup_policy
from app.services.notes_postprocess import patch_triage_summary

from app.agents.symptom_interpretation.agent_main import run_symptom_agent
from app.agents.risk_hypothesis.agent_main import run_risk_agent
from app.agents.risk_scoring_safety.agent_main import run_risk_scoring_agent
from app.agents.specialist_routing.agent_main import run_specialist_routing_agent
from app.agents.human_escalation.agent_main import run_human_escalation_agent


# ✅ Keep in sync with your policy
MAX_QUESTIONS_PER_TURN = 5
MAX_CLARIFICATION_ROUNDS = 3


class TriageGraphState(TypedDict, total=False):
    mode: Literal["start", "continue"]

    # inputs
    user_input: str
    session_id: str
    answers: Dict[str, Any]

    # persisted session notes
    notes: Dict[str, Any]
    full_notes_for_next: Dict[str, Any]

    # agent outputs
    agent1_output: Dict[str, Any]
    risk_agent: Dict[str, Any]
    risk_scoring_agent: Dict[str, Any]
    specialist_routing_agent: Dict[str, Any]
    human_escalation_agent: Optional[Dict[str, Any]]

    # flow flags
    next_step: str

    # final response
    response: Dict[str, Any]


def _normalize_answer(v: Any) -> Any:
    """normalize only strings, keep numbers intact"""
    if isinstance(v, str):
        return " ".join(v.split()).strip()
    return v


# -----------------------
# Nodes
# -----------------------

async def node_start_session(state: TriageGraphState) -> TriageGraphState:
    """only used for mode=start"""
    session_id = await create_session()
    return {"session_id": session_id, "notes": {}}


async def node_load_session(state: TriageGraphState) -> TriageGraphState:
    """used for mode=continue"""
    session = await get_session(state["session_id"])
    if not session:
        raise ValueError("Invalid session_id")
    return {"notes": session.get("notes", {})}


async def node_agent1_start(state: TriageGraphState) -> TriageGraphState:
    """Agent1 for /start"""
    result = await run_symptom_agent(state["user_input"], previous_notes={})

    notes = patch_triage_summary(result.clinical_notes.model_dump())
    notes["_round_count"] = 1
    notes["_asked_keys"] = []

    raw_followups = [q.model_dump() for q in result.follow_up_questions]
    filtered_followups, notes = enforce_followup_policy(
        followups=raw_followups,
        notes=notes,
        max_questions=MAX_QUESTIONS_PER_TURN,
    )

    agent1_output = result.model_dump()
    agent1_output["follow_up_questions"] = filtered_followups
    agent1_output["ready_for_next_agent"] = (len(filtered_followups) == 0)
    agent1_output["clinical_notes"] = patch_triage_summary(agent1_output["clinical_notes"])

    await update_session(
        session_id=state["session_id"],
        notes=notes,
        history_item={
            "type": "start",
            "user_input": state["user_input"],
            "agent_output": agent1_output,
        },
    )

    return {"notes": notes, "agent1_output": agent1_output}


async def node_agent1_continue(state: TriageGraphState) -> TriageGraphState:
    """Agent1 for /continue"""
    notes = dict(state["notes"])

    # ✅ merge new answers
    for k, v in (state.get("answers") or {}).items():
        notes[k] = _normalize_answer(v)

    # ✅ increment clarification rounds
    prev_round = int(notes.get("_round_count", 0))
    notes["_round_count"] = prev_round + 1

    result = await run_symptom_agent(
        user_input=f"Additional patient answers: {state.get('answers')}",
        previous_notes=notes,
    )

    # ✅ merge agent clinical notes into notes
    agent_notes = result.clinical_notes.model_dump()
    notes.update(agent_notes)
    notes = patch_triage_summary(notes)

    raw_followups = [q.model_dump() for q in result.follow_up_questions]
    filtered_followups, notes = enforce_followup_policy(
        followups=raw_followups,
        notes=notes,
        max_questions=MAX_QUESTIONS_PER_TURN,
    )

    agent1_output = result.model_dump()
    agent1_output["follow_up_questions"] = filtered_followups
    agent1_output["clinical_notes"] = patch_triage_summary(agent1_output["clinical_notes"])

    # ✅ FORCE proceed if max rounds reached
    round_count = int(notes.get("_round_count", 0))
    if round_count >= MAX_CLARIFICATION_ROUNDS:
        agent1_output["ready_for_next_agent"] = True
        agent1_output["follow_up_questions"] = []
        agent1_output["clinical_notes"]["triage_summary"] += (
            f" | Max clarification rounds reached ({MAX_CLARIFICATION_ROUNDS}). Proceeding."
        )
    else:
        agent1_output["ready_for_next_agent"] = (len(filtered_followups) == 0)

    await update_session(
        session_id=state["session_id"],
        notes=notes,
        history_item={
            "type": "continue",
            "answers": state.get("answers") or {},
            "agent_output": agent1_output,
        },
    )

    return {"notes": notes, "agent1_output": agent1_output}


async def node_prepare_full_notes_for_next(state: TriageGraphState) -> TriageGraphState:
    """Remove internal keys before giving to next agents"""
    full_notes = dict(state["notes"])
    full_notes.pop("_round_count", None)
    full_notes.pop("_asked_keys", None)
    return {"full_notes_for_next": full_notes}


async def node_agent2_risk(state: TriageGraphState) -> TriageGraphState:
    a1 = state["agent1_output"]
    risk = await run_risk_agent(
        identified_symptoms=a1["identified_symptoms"],
        clinical_notes=state["full_notes_for_next"],
    )
    return {"risk_agent": risk.model_dump()}


async def node_agent3_scoring(state: TriageGraphState) -> TriageGraphState:
    scoring = await run_risk_scoring_agent(
        risk_output=state["risk_agent"],
        clinical_notes=state["full_notes_for_next"],
    )
    return {"risk_scoring_agent": scoring.model_dump()}


async def node_agent4_routing(state: TriageGraphState) -> TriageGraphState:
    a1 = state["agent1_output"]
    routing = await run_specialist_routing_agent(
        identified_symptoms=a1["identified_symptoms"],
        clinical_notes=state["full_notes_for_next"],
        risk_hypothesis=state["risk_agent"],
        risk_scoring=state["risk_scoring_agent"],
    )
    return {"specialist_routing_agent": routing.model_dump()}


def route_after_agent4(state):
    flags = state["risk_scoring_agent"].get("safety_flags") or []
    needs_immediate = "requires_immediate_attention" in flags

    state["next_step"] = "human_escalation" if needs_immediate else "specialist_routing"
    return "agent5_escalation" if needs_immediate else "final_bundle"




async def node_agent5_escalation(state: TriageGraphState) -> TriageGraphState:
    a1 = state["agent1_output"]
    escalation = await run_human_escalation_agent(
        session_id=state["session_id"],
        identified_symptoms=a1["identified_symptoms"],
        clinical_notes=state["full_notes_for_next"],
        risk_hypothesis=state["risk_agent"],
        risk_scoring=state["risk_scoring_agent"],
        routing_hint=state.get("specialist_routing_agent"),
    )
    return {"human_escalation_agent": escalation.model_dump()}


async def node_final_agent1(state: TriageGraphState) -> TriageGraphState:
    """Stop after Agent1 (still collecting info)"""
    return {
        "response": {
            "session_id": state["session_id"],
            "passed_to_agent2": False,
            "agent_output": state["agent1_output"],
        }
    }


async def node_final_bundle(state: TriageGraphState) -> TriageGraphState:
    """Bundle Agent1 + Agent2+3+4 (+ maybe Agent5)"""
    resp: Dict[str, Any] = {
        "session_id": state["session_id"],
        "passed_to_agent2": True,
        "symptom_agent": state["agent1_output"],
        "risk_agent": state["risk_agent"],
        "risk_scoring_agent": state["risk_scoring_agent"],
        "specialist_routing_agent": state["specialist_routing_agent"],
        "next_step": state.get("next_step", "specialist_routing"),
    }

    if state.get("human_escalation_agent"):
        resp["human_escalation_agent"] = state["human_escalation_agent"]

    await update_session(
        session_id=state["session_id"],
        notes=state["notes"],
        history_item={
            "type": "risk_routing_bundle",
            "risk_output": state.get("risk_agent"),
            "risk_scoring_output": state.get("risk_scoring_agent"),
            "routing_output": state.get("specialist_routing_agent"),
            "human_escalation_output": state.get("human_escalation_agent"),
        },
    )

    return {"response": resp}


# -----------------------
# Routing
# -----------------------

def route_from_start(state: TriageGraphState) -> Literal["start_session", "load_session"]:
    """START should go to start_session only if mode=start"""
    if state.get("mode") == "start":
        return "start_session"
    return "load_session"


def route_after_start_session(state: TriageGraphState) -> Literal["agent1_start"]:
    return "agent1_start"


def route_after_load_session(state: TriageGraphState) -> Literal["agent1_continue"]:
    return "agent1_continue"


def route_after_agent1(state: TriageGraphState) -> Literal["final_agent1", "prepare_full_notes"]:
    """If Agent1 done, proceed pipeline; else return agent1 response"""
    a1 = state["agent1_output"]
    if a1.get("ready_for_next_agent") is True:
        return "prepare_full_notes"
    return "final_agent1"


# -----------------------
# Build Graph
# -----------------------

def build_triage_graph():
    g = StateGraph(TriageGraphState)

    # Nodes
    g.add_node("start_session", node_start_session)
    g.add_node("load_session", node_load_session)

    g.add_node("agent1_start", node_agent1_start)
    g.add_node("agent1_continue", node_agent1_continue)

    g.add_node("prepare_full_notes", node_prepare_full_notes_for_next)

    g.add_node("agent2_risk", node_agent2_risk)
    g.add_node("agent3_scoring", node_agent3_scoring)
    g.add_node("agent4_routing", node_agent4_routing)
    g.add_node("agent5_escalation", node_agent5_escalation)

    g.add_node("final_agent1", node_final_agent1)
    g.add_node("final_bundle", node_final_bundle)

    # ✅ START routing by mode
    g.add_conditional_edges(
        START,
        route_from_start,
        ["start_session", "load_session"],
    )

    # ✅ start path
    g.add_conditional_edges(
        "start_session",
        route_after_start_session,
        ["agent1_start"],
    )

    # ✅ continue path
    g.add_conditional_edges(
        "load_session",
        route_after_load_session,
        ["agent1_continue"],
    )

    # after agent1, stop or proceed
    g.add_conditional_edges(
        "agent1_start",
        route_after_agent1,
        ["final_agent1", "prepare_full_notes"],
    )
    g.add_conditional_edges(
        "agent1_continue",
        route_after_agent1,
        ["final_agent1", "prepare_full_notes"],
    )

    # ✅ proceed pipeline: prepare -> agent2 -> agent3 -> agent4 -> maybe agent5 -> final
    g.add_edge("prepare_full_notes", "agent2_risk")
    g.add_edge("agent2_risk", "agent3_scoring")
    g.add_edge("agent3_scoring", "agent4_routing")

    g.add_conditional_edges(
        "agent4_routing",
        route_after_agent4,
        ["agent5_escalation", "final_bundle"],
    )

    g.add_edge("agent5_escalation", "final_bundle")

    g.add_edge("final_agent1", END)
    g.add_edge("final_bundle", END)

    return g.compile()
