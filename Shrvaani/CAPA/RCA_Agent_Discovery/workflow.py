from langgraph.graph import StateGraph, END
from state import DiscoveryState
from nodes import risk_assessment_node, discovery_node, verification_node, synthesis_node

def create_discovery_graph():
    workflow = StateGraph(DiscoveryState)
    
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("discovery", discovery_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("synthesis", synthesis_node)
    
    workflow.set_entry_point("risk_assessment")
    
    workflow.add_conditional_edges(
        "risk_assessment",
        lambda x: "discovery" if x["is_rca_required"] else END
    )
    
    workflow.add_edge("discovery", "verification")
    workflow.add_edge("verification", "synthesis")
    workflow.add_edge("synthesis", END)
    
    return workflow.compile()
