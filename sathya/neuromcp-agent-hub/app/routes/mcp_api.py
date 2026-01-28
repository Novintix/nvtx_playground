from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

from app.services.mcp.tool_registry import TOOL_REGISTRY

router = APIRouter(prefix="/mcp", tags=["MCP"])


@router.get("/tools")
def list_tools() -> Dict[str, Any]:
    return {"tools": TOOL_REGISTRY}


@router.post("/call")
async def call_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    tool_name = payload.get("tool")
    args = payload.get("args", {})

    tool = next((t for t in TOOL_REGISTRY if t["name"] == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    handler = tool["handler"]
    out = await handler(args)  # handler must be async
    return out
