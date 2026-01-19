from langgraph.graph import StateGraph, START, END
from state import State
from nodes import (
    categorize_experience,
    assess_skill_match,
    schedule_interview,
    escalate_to_manager,
    reject_application,
)

def route_app(state: State) -> str:
    experience_level = state.get("experience_level", "").strip()
    skill_match = state.get("skill_match", "").strip()
    
    # Entry level + relevant Python skills → schedule HR interview
    if experience_level == "Entry-level" and skill_match == "Match":
        return "schedule_interview"
    
    # Experienced/Senior level + not much relevant skills → escalate to recruiter
    elif (experience_level in ["Mid-level", "Senior-level"]) and skill_match == "No Match":
        return "escalate_to_manager"
    
    # Entry level + no relevant skills → reject application
    elif experience_level == "Entry-level" and skill_match == "No Match":
        return "reject_application"
    
    # Experienced/Senior level + relevant skills → also schedule interview
    elif (experience_level in ["Mid-level", "Senior-level"]) and skill_match == "Match":
        return "schedule_interview"
    
    # Default: reject if unclear
    else:
        return "reject_application"


workflow = StateGraph(State)

workflow.add_node("categorize_experience", categorize_experience)
workflow.add_node("assess_skill_match", assess_skill_match)
workflow.add_node("schedule_interview", schedule_interview)
workflow.add_node("escalate_to_manager", escalate_to_manager)
workflow.add_node("reject_application", reject_application)

workflow.add_edge(START, "categorize_experience")
workflow.add_edge("categorize_experience", "assess_skill_match")

workflow.add_conditional_edges(
    "assess_skill_match",
    route_app,
    {
        "schedule_interview": "schedule_interview",
        "escalate_to_manager": "escalate_to_manager",
        "reject_application": "reject_application",
    }
)

workflow.add_edge("schedule_interview", END)
workflow.add_edge("escalate_to_manager", END)
workflow.add_edge("reject_application", END)

app = workflow.compile()   
