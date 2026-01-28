from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes import retrieve_node, generate_node

# 1. Initialize the Graph with our TypedDict (Memory Schema)
workflow = StateGraph(AgentState)

# 2. Add the Nodes (The "Workers")
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

# 3. Define the Flow (The "Edges")
# Logic: Start -> Retrieve Context -> Generate Answer -> End
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

# 4. Compile the Graph (Builds the executable)
graph = workflow.compile()