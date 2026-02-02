from langgraph.graph import StateGraph, END
from reasoning.state import ReasoningState
from reasoning.nodes import (
    analyze_performance,
    compare_history,
    validate_policy,
    recommend_actions,
    explain,
    policy_only_response
)

def route_query(state):
    query = state["query"].lower()
    policy_keywords = [
        "policy", "policies", "rule", "rules", 
        "guideline", "guidelines", "allowed", 
        "approval", "limit", "limits", "compliance",
        "approve", "can i", "may i", "permitted"
    ]
    
    if any(keyword in query for keyword in policy_keywords):
        return "policy_only"
    return "analyze"

def build_graph():
    graph = StateGraph(ReasoningState)

    graph.add_node("analyze", analyze_performance)
    graph.add_node("compare", compare_history)
    graph.add_node("policy", validate_policy)
    graph.add_node("recommend", recommend_actions)
    graph.add_node("explain", explain)
    graph.add_node("policy_only", policy_only_response)

    graph.set_conditional_entry_point(
        route_query,
        {
            "analyze": "analyze",
            "policy_only": "policy_only"
        }
    )

    graph.add_edge("analyze", "compare")
    graph.add_edge("compare", "policy")
    graph.add_edge("policy", "recommend")
    graph.add_edge("recommend", "explain")
    graph.add_edge("explain", END)
    graph.add_edge("policy_only", END)

    return graph.compile()
