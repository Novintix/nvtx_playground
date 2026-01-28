from __future__ import annotations
from typing import Any, Dict, List
from app.services.mcp.mcp_client import MCPClient

def discover_tools() -> List[Dict[str, Any]]:
    client = MCPClient()
    return client.list_tools()
