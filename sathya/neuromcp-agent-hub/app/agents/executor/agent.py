from __future__ import annotations
from typing import Any, Dict, List

from app.services.mcp.mcp_client import MCPClient


# tools that MUST be approved before execution
HIGH_RISK_PREFIXES = ("calendar.", "slack.", "gmail.", "drive.", "notion.", "jira.", "linear.")


def _needs_approval(tool_name: str) -> bool:
    return tool_name.startswith(HIGH_RISK_PREFIXES)


async def execute_plan(plan: Dict[str, Any], approved_step_ids: List[str]) -> Dict[str, Any]:
    client = MCPClient()
    results: Dict[str, Any] = {}

    steps = plan.get("steps", [])
    for step in steps:
        step_id = step.get("id")
        tool = step.get("tool")
        tool_input = step.get("input", {}) or {}

        if not tool:
            results[step_id] = {"status": "skipped", "reason": "No tool"}
            continue

        # approval gate
        if _needs_approval(tool) and step_id not in approved_step_ids:
            results[step_id] = {"status": "blocked", "reason": "Needs approval"}
            continue

        try:
            out = await client.call_tool(tool, tool_input)
            results[step_id] = {"status": "ok", "tool": tool, "output": out}
        except Exception as e:
            results[step_id] = {"status": "error", "tool": tool, "error": str(e)}

    return results
