from __future__ import annotations
from typing import Dict, Any, List
from app.services.mcp.mcp_client import MCPClient


async def execute_plan(plan: Dict[str, Any], approved_step_ids: List[str]) -> Dict[str, Any]:
    """
    Executes approved steps only.
    Calls real MCP tools (Slack + Google Calendar)
    """

    client = MCPClient()
    steps = plan.get("steps", [])

    results = {}

    for step in steps:
        step_id = step["id"]
        tool = step["tool"]
        tool_input = step["input"]

        # ✅ Approval required
        if step_id not in approved_step_ids:
            results[step_id] = {"status": "BLOCKED", "reason": "Not approved"}
            continue

        # ✅ Execute tool
        output = await client.call_tool(tool, tool_input)

        results[step_id] = {
            "status": "SUCCESS",
            "tool": tool,
            "output": output
        }

    return results
