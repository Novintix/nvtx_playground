from __future__ import annotations
from typing import Any, Dict, List
import os
import requests


class MCPClient:
    """
    Simple in-process MCP Client.
    Calls your FastAPI MCP server endpoints:
      - GET /mcp/tools
      - POST /mcp/call
    """

    def __init__(self):
        self.base_url = os.getenv("MCP_BASE_URL", "http://localhost:8000")

    def list_tools(self) -> List[Dict[str, Any]]:
        r = requests.get(f"{self.base_url}/mcp/tools", timeout=30)
        r.raise_for_status()
        return r.json()["tools"]

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        # for simplicity (works fine for demo): run sync request inside async function
        payload = {"tool": tool_name, "args": args}
        r = requests.post(f"{self.base_url}/mcp/call", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()
