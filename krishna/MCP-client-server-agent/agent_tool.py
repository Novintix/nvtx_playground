import asyncio
from fastmcp import Client
from langchain.tools import tool

import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp")

async def call_tool(name: str):
    async with client:
        result = await client.call_tool("reverse_text", {"text": name})
        print(result)

async def agent_tool_call(tool_name: str, params: dict):
    async with client:
        result = await client.call_tool(tool_name, params)
        print(result)

async def list_tools():
    async with client:
        tools = await client.list_tools()
        # tools -> list[mcp.types.Tool]
        
        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"Description: {tool.description}")
            if tool.inputSchema:
                print(f"Parameters: {tool.inputSchema}")
            # Access tags and other metadata
            if hasattr(tool, 'meta') and tool.meta:
                fastmcp_meta = tool.meta.get('_fastmcp', {})
                print(f"Tags: {fastmcp_meta.get('tags', [])}")

# asyncio.run(list_tools())
# asyncio.run(call_tool("Ford"))

tool_name = input("Enter tool name: ")
params = {"text": "Hello World"}

asyncio.run(agent_tool_call(tool_name, params))

























# @tool
# def mcp_uppercase_text(text: str) -> str:
#     """Convert text to uppercase using MCP."""

#     async def _call():
#         async with Client("http://127.0.0.1:8000/mcp") as client:
#             result = await client.call_tool(
#                 "uppercase_text",
#                 {"text": text}
#             )
#             return result.data

#     return asyncio.run(_call())


# @tool
# def mcp_slugify_text(text: str) -> str:
#     """Convert text to a URL-friendly slug using MCP."""

#     async def _call():
#         async with Client("http://127.0.0.1:8000/mcp") as client:
#             result = await client.call_tool(
#                 "slugify_text",
#                 {"text": text}
#             )
#             return result.data

#     return asyncio.run(_call())


# @tool
# def mcp_reverse_text(text: str) -> str:
#     """Reverse text using MCP."""

#     async def _call():
#         async with Client("http://127.0.0.1:8000/mcp") as client:
#             result = await client.call_tool(
#                 "reverse_text",
#                 {"text": text}
#             )
#             return result.data

#     return asyncio.run(_call())


# @tool
# def mcp_word_count(text: str) -> int:
#     """Count words using MCP."""

#     async def _call():
#         async with Client("http://127.0.0.1:8000/mcp") as client:
#             result = await client.call_tool(
#                 "word_count",
#                 {"text": text}
#             )
#             return result.data

#     return asyncio.run(_call())
