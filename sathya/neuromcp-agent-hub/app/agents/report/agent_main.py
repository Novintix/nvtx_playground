from __future__ import annotations
from typing import Any, Dict


def run_report(state: Dict[str, Any]) -> Dict[str, Any]:
    logs = state.get("logs", [])
    logs.append({"agent": "report", "msg": "Generating final report..."})

    plan = state.get("plan", {})
    results = state.get("execution_results", {}) or {}

    lines = []
    lines.append("✅ NeuroMCP Final Report")
    lines.append("")
    lines.append(f"Goal: {plan.get('goal', '-')}")
    lines.append("")
    lines.append("Steps executed:")

    for step in plan.get("steps", []):
        sid = step.get("id")
        action = step.get("action")
        tool = step.get("tool")

        r = results.get(sid, {})
        status = r.get("status", "unknown")

        lines.append(f"- {sid}: {action} ({tool}) -> {status}")

        if status == "ok":
            out = r.get("output")
            if isinstance(out, dict) and out.get("error"):
                lines.append(f"    ⚠️ Tool error: {out.get('error')}")
        if status == "error":
            lines.append(f"    ❌ {r.get('error')}")

    state["final_report"] = "\n".join(lines)
    logs.append({"agent": "report", "msg": "Final report generated."})
    state["logs"] = logs
    return state
