from __future__ import annotations
from typing import Any, Dict
from datetime import datetime


def format_slack_messages(messages: list) -> str:
    """Format Slack messages in a user-friendly way"""
    if not messages:
        return "No messages found."
    
    formatted_lines = []
    formatted_lines.append(f"📬 {len(messages)} Messages:\n")
    
    for msg in messages:
        text = msg.get("text", "")
        user = msg.get("user", "unknown")
        timestamp = msg.get("timestamp", "")
        
        # Convert timestamp to readable format if possible
        try:
            if timestamp:
                ts_float = float(timestamp)
                dt = datetime.fromtimestamp(ts_float)
                time_str = dt.strftime("%b %d, %I:%M %p")
            else:
                time_str = "Unknown time"
        except:
            time_str = "Unknown time"
        
        formatted_lines.append(f"💬 {time_str}")
        formatted_lines.append(f"   {text}\n")
    
    return "\n".join(formatted_lines)


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
    
    # Check if results contain Slack messages - format them nicely
    has_slack_messages = False
    for step_id, result in results.items():
        if isinstance(result, dict) and "messages" in result:
            messages = result.get("messages", [])
            if messages:
                has_slack_messages = True
                formatted_text = format_slack_messages(messages)
                lines.append(formatted_text)
                
                # IMPORTANT: Match the format the UI expects (like summarizer output)
                # Put formatted text in 'summary' field
                results[step_id] = {
                    "success": True,
                    "summary": formatted_text,
                    "message_count": len(messages)
                }
                # Removed 'break' to allow processing of multiple Slack message results
    
    # DON'T overwrite other results like calendar events - they have their own display format

    # If no special formatting was needed, show standard report
    if not has_slack_messages:
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
    state["execution_results"] = results  # Update with formatted results (Slack only)
    logs.append({"agent": "report", "msg": "Final report generated."})
    state["logs"] = logs
    return state
