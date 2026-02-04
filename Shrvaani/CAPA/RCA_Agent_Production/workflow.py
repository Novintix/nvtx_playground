from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import (
    risk_assessment_node,
    semantic_mapping_node,
    evidence_validation_node,
    five_why_node
)

def create_rca_graph():
    # 1. Initialize Graph
    workflow = StateGraph(AgentState)

    # 2. Add Nodes
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("semantic_mapping", semantic_mapping_node)
    workflow.add_node("evidence_validation", evidence_validation_node)
    workflow.add_node("five_why_analysis", five_why_node)

    # 3. Define Edges & Conditional Logic
    workflow.set_entry_point("risk_assessment")

    workflow.add_conditional_edges(
        "risk_assessment",
        lambda x: "semantic_mapping" if x["is_rca_required"] else END
    )

    workflow.add_edge("semantic_mapping", "evidence_validation")
    workflow.add_edge("evidence_validation", "five_why_analysis")
    workflow.add_edge("five_why_analysis", END)

    # 4. Compile
    return workflow.compile()
