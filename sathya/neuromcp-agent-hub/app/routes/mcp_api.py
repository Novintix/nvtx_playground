# app/routes/mcp_api.py
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

router = APIRouter()

class MCPCallRequest(BaseModel):
    name: str
    args: Dict[str, Any] = {}

def _is_mock() -> bool:
    return os.getenv("MOCK_TOOLS", "false").lower() == "true"

@router.post("/mcp/call")
async def call_tool(req: MCPCallRequest):
    # ✅ HARD BYPASS (no Mongo, no token_store, no tool modules)
    if _is_mock():
        if req.name == "calendar.create_event":
            return {
                "ok": True,
                "mock": True,
                "event_id": f"mock-event-{datetime.utcnow().isoformat()}",
                "input": req.args,
            }
        if req.name == "slack.post_message":
            return {
                "ok": True,
                "mock": True,
                "message_id": f"mock-msg-{datetime.utcnow().isoformat()}",
                "input": req.args,
            }
        raise HTTPException(status_code=404, detail=f"Unknown tool: {req.name}")

    # 🔻 normal flow (real tools)
    try:
        # your existing handler lookup
        handler = TOOL_REGISTRY[req.name]  # whatever you use
        out = await handler(req.args)
        return out
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {req.name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
