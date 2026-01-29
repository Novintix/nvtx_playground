from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from src.agents import (
    DiscussionFocusAgent, 
    RequirementIntentAgent, 
    DriftAnalyzerAgent,
    CodeComplianceAgent,
    DiscussionAnalysis,
    RequirementIntent,
    DriftAnalysis,
    CodeDriftAnalysis
)
from src.github_tool import fetch_repo_structure

class DriftState(TypedDict):
    chat_transcript: str
    requirement_text: str
    repo_url: Optional[str]
    discussion_analysis: Optional[DiscussionAnalysis]
    requirement_intent: Optional[RequirementIntent]
    drift_analysis: Optional[DriftAnalysis]
    code_analysis: Optional[CodeDriftAnalysis]

def analyze_discussion(state: DriftState):
    agent = DiscussionFocusAgent()
    analysis = agent.analyze(state["chat_transcript"])
    return {"discussion_analysis": analysis}

def analyze_requirements(state: DriftState):
    agent = RequirementIntentAgent()
    intent = agent.analyze(state["requirement_text"])
    return {"requirement_intent": intent}

from src.vector_store import create_vector_store, retrieve_context

# ... (DriftState definition matches existing)

def analyze_drift(state: DriftState):
    agent = DriftAnalyzerAgent()
    
    # 1. Discussion Focus -> Search Queries
    focus_points = state["discussion_analysis"].primary_focus
    query = " ".join(focus_points)
    
    # 2. RAG Retrieval
    # Note: For efficiency in a real app, vector_store should be created once in a separate node.
    # Here we creates it on the fly for simplicity.
    try:
        if state["requirement_text"]:
            vector_store = create_vector_store(state["requirement_text"])
            context = retrieve_context(vector_store, query)
        else:
            context = ""
    except Exception as e:
        print(f"RAG Error: {e}")
        context = ""

    # 3. Analyze with Context
    drift = agent.analyze(state["discussion_analysis"], state["requirement_intent"], additional_context=context)
    return {"drift_analysis": drift}

def analyze_codebase(state: DriftState):
    if not state.get("repo_url"):
        return {}
    
    # 1. Fetch Structure
    structure = fetch_repo_structure(state["repo_url"])
    code_summary = f"File Structure: {structure}" 
    # (In a real app, we'd fetch content of key files here too)
    
    # 2. Analyze
    agent = CodeComplianceAgent()
    analysis = agent.analyze(state["requirement_intent"], code_summary)
    return {"code_analysis": analysis}

def create_drift_graph():
    workflow = StateGraph(DriftState)

    workflow.add_node("analyze_discussion", analyze_discussion)
    workflow.add_node("analyze_requirements", analyze_requirements)
    workflow.add_node("analyze_drift", analyze_drift)
    workflow.add_node("analyze_codebase", analyze_codebase)

    workflow.set_entry_point("analyze_discussion")
    
    workflow.add_edge("analyze_discussion", "analyze_requirements")
    workflow.add_edge("analyze_requirements", "analyze_drift")
    workflow.add_edge("analyze_drift", "analyze_codebase")
    workflow.add_edge("analyze_codebase", END)

    return workflow.compile()
