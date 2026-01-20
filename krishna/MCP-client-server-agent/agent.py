import asyncio
import json
import os
from typing import List, TypedDict

from dotenv import load_dotenv
from fastmcp import Client
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph


load_dotenv()

class AgentState(TypedDict):
    messages: List[BaseMessage]
    tools_info: str
    tool_name: str
    tool_input: dict
    tool_output: str
    done: bool

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

async def list_tools():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        tools = await client.list_tools()
        print(tools)
        return tools

async def call_tool(tool_name: str, params: dict):
    async with Client("http://127.0.0.1:8000/mcp") as client:
        tool = await client.call_tool(tool_name, params)
        print(tool)
        return tool
    
def get_tools_info() -> str:
    try:
        tools = asyncio.run(list_tools())
        return "\n".join(
            [f"- {t['name']}: {t.get('description', '')}" for t in tools]
        )
    except Exception as e:
        return f"Error listing tools: {e}"

def ai_node(state: AgentState) -> AgentState:
    tools_info = get_tools_info()
    user_msg = next((m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None)
    user_text = user_msg.content if user_msg else ""

    system_prompt = (
        "You are a minimal tool-using agent.\n"
        "Available tools:\n"
        f"{tools_info}\n\n"
        "Pick ONE tool and parameters to solve the user request, or return tool: none if done.\n"
        "Respond with JSON only: {\"tool\": \"tool_name|none\", \"params\": {}}"
    )

    response = model.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_text),
    ])

    tool_name = "none"
    tool_input = {}
    try:
        data = json.loads(response.content.strip())
        tool_name = data.get("tool", "none")
        tool_input = data.get("params", {}) or {}
    except Exception:
        tool_name = "none"
        tool_input = {}

    return {
        "messages": state["messages"],
        "tools_info": tools_info,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": state.get("tool_output", ""),
        "done": tool_name == "none",
    }

def agent_tool_call(state: AgentState) -> AgentState:
    tool_name = state["tool_name"]
    tool_input = state["tool_input"]

    try:
        result = asyncio.run(call_tool(tool_name, tool_input))
        # Prefer clean text if present
        if hasattr(result, "content") and result.content:
            content = result.content[0]
            output = getattr(content, "text", str(result))
        else:
            output = getattr(result, "data", str(result))
    except Exception as e:
        output = f"Tool error: {e}"

    return {
        **state,
        "tool_output": str(output),
        "messages": state["messages"] + [AIMessage(content=str(output))],
    }

def should_continue(state: AgentState) -> str:
    return "end" if state.get("done") else "tool"

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("ai", ai_node)
    graph.add_node("agent_tool_call", agent_tool_call)

    graph.add_edge(START, "ai")
    graph.add_conditional_edges("ai", should_continue, {"tool": "agent_tool_call", "end": END})
    graph.add_edge("agent_tool_call", "ai")
    return graph.compile()

agent = build_graph()


user_query = "Slugify: Hello World from LangChain"
result = agent.invoke({
    "messages": [HumanMessage(content=user_query)],
    "tools_info": "",
    "tool_name": "",
    "tool_input": {},
    "tool_output": "",
    "done": False,
    })

last_msg = result["messages"][-1]
print("Final Answer:", getattr(last_msg, "content", str(last_msg)))

