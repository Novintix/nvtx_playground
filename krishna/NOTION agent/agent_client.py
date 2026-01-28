import os
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict,Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()  # Load environment variables from .env file

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# MCP client for local FastMCP server
client = MultiServerMCPClient(
    {
        # "notion": {
        #     "transport": "streamable_http",  # if this fails, try "sse"
        #     "url": "http://127.0.0.1:8001/mcp"
        # },
        "filesystem": {
            "transport": "streamable_http",  # if this fails, try "sse"
            "url": "http://127.0.0.1:8002/mcp"
        }
    }
)

# state
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

async def build_graph():

    tools = await client.get_tools()

    llm_with_tools = llm.bind_tools(tools)

    # nodes
    async def chat_node(state: ChatState):

        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {'messages': [response]}

    tool_node = ToolNode(tools)

    # defining graph and nodes
    graph = StateGraph(ChatState)

    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    # defining graph connections
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
    graph.add_edge("chat_node", END)
    
    memory = MemorySaver()
    chatbot = graph.compile(checkpointer=memory)

    return chatbot

async def main():

    chatbot = await build_graph()

    thread_id = "chat-1"
    exit_words = {"bye", "exit", "quit"}

    while True:
        user_message = input("User: ").strip()
        if not user_message:
            continue

        if user_message.lower() in exit_words:
            print("Assistant: Bye!")
            break

        result = await chatbot.ainvoke(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": thread_id}}
        )

        print("Assistant:", result["messages"][-1].text)

if __name__ == '__main__':
    asyncio.run(main())