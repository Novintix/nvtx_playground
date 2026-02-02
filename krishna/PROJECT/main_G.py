import os
import json
import asyncio
from typing import TypedDict, Annotated, Literal, List, Dict, Any
from dotenv import load_dotenv
import operator

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=1
)

# MCP client configuration
notion_client = MultiServerMCPClient(
    {
        "notion": {
            "transport": "streamable_http",
            "url": "http://127.0.0.1:8001/mcp"
        }
    }
)

filesystem_client = MultiServerMCPClient(
    {
        "filesystem": {
            "transport": "streamable_http",
            "url": "http://127.0.0.1:8002/mcp"
        }
    }
)

# Cached subgraphs and tools
_notion_tools = None
_filesystem_tools = None
_notion_subgraph = None
_filesystem_subgraph = None
_dynamic_tools: Dict[str, list] = {}
_dynamic_subgraphs: Dict[str, Any] = {}

# Dynamic MCP endpoints config
MCP_ENDPOINTS_JSON = os.path.join(
    os.path.dirname(__file__), 
    os.getenv("MCP_ENDPOINTS_JSON", "mcp_endpoints.json")
)

# ============================================================================
# 1. Define Agent States
# ============================================================================

class NotionState(TypedDict):
    """State for the Notion Subgraph"""
    messages: Annotated[List[BaseMessage], add_messages]

class FilesystemState(TypedDict):
    """State for the Filesystem Subgraph"""
    messages: Annotated[List[BaseMessage], add_messages]

class SupervisorState(TypedDict):
    """State for the Main Supervisor Graph"""
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: str
    current_task: str

class DynamicMCPState(TypedDict):
    """State for the Dynamic MCP Subgraph"""
    messages: Annotated[List[BaseMessage], add_messages]

# ============================================================================
# 2. Build Subgraphs
# ============================================================================

async def create_notion_subgraph():
    """Create the Notion subgraph"""
    global _notion_tools
    if _notion_tools is None:
        _notion_tools = await notion_client.get_tools()
    tools = _notion_tools
    
    # Define tool node
    from langgraph.prebuilt import ToolNode
    tool_node = ToolNode(tools)

    # Define the agent node
    async def agent_node(state: NotionState):
        messages = state["messages"]
        prompt = (
            "You are a Notion assistant. "
            "You can search Notion pages, retrieve page content, create pages, "
            "and manage Notion databases. "
            "Use the provided tools to interact with Notion and return clear results."
        )

        if messages and isinstance(messages[0], SystemMessage):
            final_messages = messages
        else:
            final_messages = [SystemMessage(content=prompt)] + messages

        model = llm.bind_tools(tools)
        response = await model.ainvoke(final_messages)
        return {"messages": [response]}

    # Define determining the next step
    def should_continue(state: NotionState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    # Build the graph
    workflow = StateGraph(NotionState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile()

async def create_filesystem_subgraph():
    """Create the Filesystem subgraph"""
    global _filesystem_tools
    if _filesystem_tools is None:
        _filesystem_tools = await filesystem_client.get_tools()
    tools = _filesystem_tools
    
    # Define tool node
    from langgraph.prebuilt import ToolNode
    tool_node = ToolNode(tools)

    # Define the agent node
    async def agent_node(state: FilesystemState):
        messages = state["messages"]
        # Bind tools to the LLM
        prompt = (
            "You are a Filesystem assistant. "
            "You can read, write, move, list, and manage files on the local system. "
            "If the user asks to write content but does not provide it, generate a brief placeholder "
            "or the requested content yourself if it is general knowledge before calling the write tool. "
            "Always verify paths and confirm actions."
        )
        
        # Add system prompt to messages
        if messages and isinstance(messages[0], SystemMessage):
            final_messages = messages
        else:
            final_messages = [SystemMessage(content=prompt)] + messages
            
        model = llm.bind_tools(tools)
        response = await model.ainvoke(final_messages)
        return {"messages": [response]}

    # Define determining the next step
    def should_continue(state: FilesystemState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    # Build the graph
    workflow = StateGraph(FilesystemState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile()

# ============================================================================
# 2b. Dynamic MCP Subgraph Helpers
# ============================================================================

def _load_endpoints_from_json(path: str) -> Dict[str, Dict[str, str]]:
    """Load MCP endpoints from JSON file with description field."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Expected format: {"name": {"transport": "streamable_http", "url": "http://...", "description": "..."}}
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def get_dynamic_endpoints() -> Dict[str, Dict[str, str]]:
    """Get all available MCP endpoints from JSON configuration."""
    return _load_endpoints_from_json(MCP_ENDPOINTS_JSON)


class EndpointChoice(BaseModel):
    endpoint: str = Field(..., description="Chosen MCP endpoint name")


async def choose_endpoint(user_query: str, endpoints: Dict[str, Dict[str, str]]) -> str:
    """Select the most appropriate MCP endpoint based on task and descriptions."""
    if not endpoints:
        return ""
    
    # Build description of available endpoints
    endpoint_info = []
    for name, config in endpoints.items():
        desc = config.get("description", "No description")
        endpoint_info.append(f"- {name}: {desc}")
    
    endpoint_list = "\n".join(endpoint_info)
    prompt = (
        "Select the best MCP endpoint for the user's task based on the descriptions below.\n\n"
        f"Available endpoints:\n{endpoint_list}\n\n"
        "Return only the endpoint name that best matches the task."
    )
    
    structured_llm = llm.with_structured_output(EndpointChoice)
    response = await structured_llm.ainvoke(
        [SystemMessage(content=prompt), HumanMessage(content=user_query)]
    )
    
    if response.endpoint in endpoints:
        return response.endpoint
    # Fallback to first endpoint
    return list(endpoints.keys())[0]


async def create_dynamic_subgraph(endpoint_name: str, endpoint_config: Dict[str, str]):
    """Create a subgraph for a dynamically selected MCP endpoint"""
    global _dynamic_tools
    if endpoint_name in _dynamic_tools:
        tools = _dynamic_tools[endpoint_name]
    else:
        # Filter out 'description' field - only pass transport and url to client
        client_config = {
            "transport": endpoint_config.get("transport", "streamable_http"),
            "url": endpoint_config["url"]
        }
        client = MultiServerMCPClient({endpoint_name: client_config})
        tools = await client.get_tools()
        _dynamic_tools[endpoint_name] = tools

    from langgraph.prebuilt import ToolNode
    tool_node = ToolNode(tools)

    async def agent_node(state: DynamicMCPState):
        messages = state["messages"]
        prompt = (
            "You are a dynamic MCP agent. "
            f"You are connected to the MCP server '{endpoint_name}'. "
            "Use the available tools to complete the task and return clear results."
        )
        if messages and isinstance(messages[0], SystemMessage):
            final_messages = messages
        else:
            final_messages = [SystemMessage(content=prompt)] + messages
        model = llm.bind_tools(tools)
        response = await model.ainvoke(final_messages)
        return {"messages": [response]}

    def should_continue(state: DynamicMCPState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(DynamicMCPState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile()

# ============================================================================
# 3. Define Supervisor Logic (Router)
# ============================================================================

# Structured output for the supervisor's decision
class AgentAction(BaseModel):
    """The action to take: which agent to call and with what task."""
    agent: Literal["notion", "filesystem", "dynamic", "FINISH"] = Field(
        ..., description="The next agent to call, or FINISH if the user request is complete."
    )
    task: str = Field(
        ..., description="The specific task or query for the agent. If FINISH, provide the final answer summary."
    )

async def supervisor_node(state: SupervisorState):
    """Supervisor determines the next step"""
    messages = state["messages"]
    
    system_prompt = """You are a Supervisor Agent.
    You manage a Notion Agent, a Filesystem Agent, and a Dynamic MCP Agent.
    
    Your goal is to satisfy the user's request by delegating tasks to these agents.
    
    1. Notion Agent: FIXED connection to http://127.0.0.1:8001/mcp for Notion operations.
    2. Filesystem Agent: FIXED connection to http://127.0.0.1:8002/mcp for file operations.
    3. Dynamic MCP Agent: Dynamically selects from available MCP servers based on task.
    
    Plan the workflow:
    - ONLY use 'notion' agent if the user specifically wants the DEFAULT Notion MCP (port 8001)
    - ONLY use 'filesystem' agent if the user wants local file operations (port 8002)
    - Use 'dynamic' agent for ALL OTHER tasks, including:
      * MongoDB operations
      * Weather queries
      * Any custom MCP endpoints added by the user
      * Tasks that explicitly mention a specific MCP server name
    - If the user's request is fully completed, return 'FINISH' with a summary.
    
    Example Workflows:
    1. "Use MongoDB to get collections" → Call 'dynamic' with the full task
    2. "Use dynamic_notion to get git notes" → Call 'dynamic' with the full task
    3. "Search my Notion for notes" (no specific MCP mentioned) → Call 'notion' with the task
    4. "Save this to a file" → Call 'filesystem' with the task
    """
    
    # Use structured output for reliable routing
    structured_llm = llm.with_structured_output(AgentAction)
    
    # We invoke the LLM with system prompt + chat history
    response = await structured_llm.ainvoke([SystemMessage(content=system_prompt)] + messages)
    
    return {
        "next_agent": response.agent,
        "current_task": response.task,
        # We optionally add the supervisor's thought process as a message if desired, 
        # but for now we just route.
    }

# ============================================================================
# 4. Node Wrappers for Subgraphs
# ============================================================================

async def call_notion_agent(state: SupervisorState):
    """Wrapper to invoke the Notion subgraph"""
    global _notion_subgraph
    task = state["current_task"]
    print(f"\n🔹 Handing off to NOTION agent with task: {task}")
    
    # Get the subgraph
    # In a real app, we might cache this, but for this simpler script we recreate or retrieve typical singleton
    if _notion_subgraph is None:
        _notion_subgraph = await create_notion_subgraph()
    subgraph = _notion_subgraph
    
    # Invoke subgraph with the specific task
    # We pass a new history containing just the task to keep the context clean for the sub-agent
    result = await subgraph.ainvoke({"messages": [HumanMessage(content=task)]})
    
    # Get the final response from the sub-agent
    last_message = result["messages"][-1]
    response_content = last_message.content
    print(f"🔹 Notion Agent finished. Output length: {len(response_content)}")
    
    # Return directly to update main state
    # We wrap the output as a ToolMessage or AIMessage "from" the agent
    return {
        "messages": [
            AIMessage(content=f"Notion Agent Result: {response_content}", name="notion_agent")
        ]
    }

async def call_filesystem_agent(state: SupervisorState):
    """Wrapper to invoke the Filesystem subgraph"""
    global _filesystem_subgraph
    task = state["current_task"]
    print(f"\n🔸 Handing off to FILESYSTEM agent with task: {task}")
    
    if _filesystem_subgraph is None:
        _filesystem_subgraph = await create_filesystem_subgraph()
    subgraph = _filesystem_subgraph
    
    result = await subgraph.ainvoke({"messages": [HumanMessage(content=task)]})
    
    last_message = result["messages"][-1]
    response_content = last_message.content
    
    print(f"🔸 Filesystem Agent finished.")
    
    return {
        "messages": [
            AIMessage(content=f"Filesystem Agent Result: {response_content}", name="filesystem_agent")
        ]
    }

async def call_dynamic_agent(state: SupervisorState):
    """Wrapper to invoke a dynamically selected MCP subgraph"""
    global _dynamic_subgraphs
    task = state["current_task"]
    print(f"\n🟣 Selecting MCP endpoint for task: {task}")

    endpoints = get_dynamic_endpoints()
    if not endpoints:
        return {
            "messages": [
                AIMessage(
                    content="Dynamic MCP Agent Result: No MCP endpoints configured. "
                            "Provide mcp_endpoints.json or configure MCP_ENDPOINTS_MYSQL_URL.",
                    name="dynamic_agent"
                )
            ]
        }

    chosen = await choose_endpoint(task, endpoints)
    if not chosen:
        return {
            "messages": [
                AIMessage(
                    content="Dynamic MCP Agent Result: Could not select an endpoint.",
                    name="dynamic_agent"
                )
            ]
        }

    if chosen not in _dynamic_subgraphs:
        _dynamic_subgraphs[chosen] = await create_dynamic_subgraph(chosen, endpoints[chosen])

    subgraph = _dynamic_subgraphs[chosen]
    print(f"🟣 Using dynamic MCP endpoint: {chosen}")

    result = await subgraph.ainvoke({"messages": [HumanMessage(content=task)]})
    last_message = result["messages"][-1]
    response_content = last_message.content

    return {
        "messages": [
            AIMessage(content=f"Dynamic MCP Agent Result ({chosen}): {response_content}", name="dynamic_agent")
        ]
    }

# ============================================================================
# 5. Build Main Graph
# ============================================================================

def build_main_graph():
    """Construct the main supervisor graph"""
    workflow = StateGraph(SupervisorState)
    
    # Add Nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("notion", call_notion_agent)
    workflow.add_node("filesystem", call_filesystem_agent)
    workflow.add_node("dynamic", call_dynamic_agent)
    
    # Set Entry Point
    workflow.add_edge(START, "supervisor")
    
    # Define Routing Logic
    def router(state: SupervisorState):
        next_step = state["next_agent"]
        if next_step == "FINISH":
            return END
        return next_step # "notion" or "filesystem"
    
    # Add Conditional Edges
    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "notion": "notion",
            "filesystem": "filesystem",
            "dynamic": "dynamic",
            END: END
        }
    )
    
    # Edges from agents back to supervisor
    workflow.add_edge("notion", "supervisor")
    workflow.add_edge("filesystem", "supervisor")
    workflow.add_edge("dynamic", "supervisor")
    
    return workflow.compile(checkpointer=MemorySaver())

# ============================================================================
# 6. Main Execution
# ============================================================================

async def main():
    print("🚀 Initializing LangGraph Multi-Agent System...")
    
    # Initialize Clients (Wait for connection if needed)
    # The clients are initialized globally, but we ensure tools are ready
    global _notion_tools, _filesystem_tools, _notion_subgraph, _filesystem_subgraph
    try:
        _notion_tools = await notion_client.get_tools()
        _filesystem_tools = await filesystem_client.get_tools()
        _notion_subgraph = await create_notion_subgraph()
        _filesystem_subgraph = await create_filesystem_subgraph()
    except Exception as e:
        print(f"Error connecting to MCP servers: {e}")
        return

    graph = build_main_graph()
    
    print("✅ System Ready. Subgraphs loaded.")
    print("Type 'quit' to exit.\n")
    
    config = {"configurable": {"thread_id": "main_thread"}}
    
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() in ["quit", "exit", "bye"]:
            break
            
        print("\n--- Processing ---")
        
        # Stream the execution
        async for event in graph.astream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config
        ):
            for k, v in event.items():
                if k == "supervisor":
                    print(f"🤖 Supervisor decided: Call {v.get('next_agent')} with task: '{v.get('current_task')}'")
                elif k == "__end__":
                    pass 
                # Sub-agent outputs are printed inside the wrapper functions for cleaner logs

if __name__ == "__main__":
    asyncio.run(main())