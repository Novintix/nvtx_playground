import asyncio
import json
import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client
from pathlib import Path

class MCPService:
    """
    Handles communication with the persistent DecodX Governance SSE Server.
    """
    def __init__(self, sse_url="http://localhost:8000/sse"):
        self.sse_url = sse_url
        self._loop = asyncio.new_event_loop()
        
    def call(self, tool_name, **kwargs):
        """
        Executes a synchronous call to the persistent SSE backend.
        """
        try:
            return self._loop.run_until_complete(self._async_call(tool_name, **kwargs))
        except Exception as e:
            print(f"MCP Connection Error: {e}")
            return {"allowed": False, "reason": f"Connection failed. Ensure backend is running at {self.sse_url}"}

    async def _async_call(self, tool_name, **kwargs):
        async with sse_client(self.sse_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Verify tool existence
                tools = await session.list_tools()
                if not any(t.name == tool_name for t in tools.tools):
                    return None
                    
                result = await session.call_tool(tool_name, arguments=kwargs)
                
                # Safely extract response
                if hasattr(result, 'content') and len(result.content) > 0:
                    text_content = result.content[0].text
                    try:
                        # FastMCP often returns results as JSON strings
                        return json.loads(text_content)
                    except:
                        # Fallback for plain text
                        return text_content
                return None

mcp_service = MCPService()
