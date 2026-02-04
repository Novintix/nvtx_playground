from backend.services.reasoning_service import build_graph

def run_agent_reasoning(state_data: dict):
    """
    Invokes the reasoning graph with the provided state.
    """
    agent = build_graph()
    return agent.invoke(state_data)
