from __future__ import annotations

from typing import Any, Dict, List
from app.agents.tool_discovery.agent import discover_tools


def _normalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    state.setdefault("logs", [])
    return state


async def run_tool_discovery(state: Dict[str, Any]) -> Dict[str, Any]:
    state = _normalize_state(state)
    logs: List[Dict[str, Any]] = state["logs"]

    tools = await discover_tools()

    # ✅ single source of truth for planner
    state["available_tools"] = tools

    # (optional) keep old key so other code doesn't break
    state["tools"] = tools

    logs.append({"agent": "tool_discovery", "msg": f"Discovered {len(tools)} tools."})
    return state
