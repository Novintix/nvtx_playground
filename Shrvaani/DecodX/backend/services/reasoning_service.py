from langgraph.graph import StateGraph, END
from backend.models.state import ReasoningState
from backend.services.intelligence_service import get_llm
from backend.services.vector_store_service import get_retriever
from datetime import datetime
import os
import json

# NODE: Analyzes financial data to identify business trends.
def analyze_data(state: ReasoningState):
    llm = get_llm()
    query = state["query"]
    context = state["financial_context"]
    
    prompt = f"Analyze following financial data for query: '{query}'\nData: {context}\nProvide concise analysis."
    response = llm.invoke(prompt)
    return {"analysis": response.content}

# NODE: Checks retrieved policies for compliance questions.
def check_policy(state: ReasoningState):
    llm = get_llm()
    query = state["query"]
    context = state["policy_context"]
    
    prompt = f"Check policy context for compliance regarding: '{query}'\nPolicies: {context}\nIdentify if compliant."
    response = llm.invoke(prompt)
    return {"policy_check": response.content}

# NODE: Handles the draft and conflict checking for policy updates.
def modify_policy(state: ReasoningState):
    """Smart Merge & Hurdle Detection."""
    llm = get_llm()
    query = state["query"]
    user_role = state["user_role"]
    
    policy_name = "sales_policy" if "sales" in query.lower() else "hr_policy"
    
    from backend.services.governance_service import read_policy, identify_policy_hurdles
    current_content = read_policy(policy_name)
    
    merge_prompt = f"Current Policy:\n{current_content}\nRequested Change:\n{query}\nReturn the FULL updated policy document body only."
    merged_doc = llm.invoke(merge_prompt).content
    
    hurdles = identify_policy_hurdles(merged_doc)
    
    return {
        "proposed_change": {"policy_name": policy_name, "new_content": merged_doc},
        "hurdles": hurdles,
        "interaction_needed": True,
        "final_answer": "I have drafted the policy update. Please review the changes and hurdles below."
    }

# NODE: Merges all reasoning results into a professional final response.
def synthesize_answer(state: ReasoningState):
    llm = get_llm()
    analysis = state.get("analysis", "")
    policy = state.get("policy_check", "")
    query = state["query"]
    
    prompt = f"Synthesize final answer for query: '{query}'\nAnalysis: {analysis}\nPolicy: {policy}\nCombine insights."
    response = llm.invoke(prompt)
    return {"final_answer": response.content}

# NODE: Researches external compliance standards for additional context.
def audit_compliance(state: ReasoningState):
    llm = get_llm()
    query = state["query"]
    prompt = f"Research external compliance standards for: {query}. Summary only."
    summary = llm.invoke(prompt).content
    return {"external_context": summary}

# ROUTER: Selects the appropriate initialization node for the graph.
def route_query(state: ReasoningState):
    query = state["query"].lower()
    if any(kw in query for kw in ["update", "modify", "change", "revise"]):
        return "modify"
    if any(kw in query for kw in ["audit", "compliance", "standard", "external"]):
        return "audit"
    return "analyze"

# COMPILER: Configures and compiles the LangGraph reasoning workflow.
def build_graph():
    workflow = StateGraph(ReasoningState)
    
    workflow.add_node("analyze", analyze_data)
    workflow.add_node("policy", check_policy)
    workflow.add_node("modify", modify_policy)
    workflow.add_node("audit", audit_compliance)
    workflow.add_node("synthesize", synthesize_answer)
    
    workflow.set_conditional_entry_point(
        route_query,
        {"modify": "modify", "audit": "audit", "analyze": "analyze"}
    )
    
    workflow.add_edge("analyze", "policy")
    workflow.add_edge("policy", "synthesize")
    workflow.add_edge("audit", "synthesize")
    workflow.add_edge("modify", END)
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()
