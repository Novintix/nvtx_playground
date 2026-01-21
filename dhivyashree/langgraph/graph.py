from langgraph.graph import StateGraph, START, END
from state import AgentState
from agents import pro_agent, con_agent, judge_agent

def compile_graph():
    """
    Builds and compiles the LangGraph for the debate agent.
    """
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("pro", pro_agent)
    builder.add_node("con", con_agent)
    builder.add_node("judge", judge_agent)
    
    # Define edges
    # Standard flow: START -> Pro -> Con -> Judge -> END
    builder.add_edge(START, "pro")
    builder.add_edge("pro", "con")
    builder.add_edge("con", "judge")
    builder.add_edge("judge", END)
    
    # Compile
    graph = builder.compile()
    return graph
