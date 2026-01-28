from __future__ import annotations
from typing import Any, Dict
from app.agents.tool_discovery.agent import discover_tools

def run_tool_discovery(state: Dict[str, Any]) -> Dict[str, Any]:
    tools = discover_tools()

    logs = state.get("logs", [])
    logs.append({"agent": "tool_discovery", "msg": f"Discovered {len(tools)} tools."})

    state["available_tools"] = tools
    state["logs"] = logs
    return state
