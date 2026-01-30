from __future__ import annotations
from typing import Any, Dict, List

from app.services.mcp.mcp_client import MCPClient
from app.services.tools.calendar_tool import create_calendar_event, list_calendar_events
from app.services.tools.slack_tool import post_slack_message, list_slack_channels, read_slack_messages
from app.services.ai.summarizer import summarize_slack_messages


async def run_executor(state: Dict[str, Any]) -> Dict[str, Any]:
    state.setdefault("logs", [])
    logs: List[Dict[str, Any]] = state["logs"]

    plan = state.get("plan")
    if not plan:
        raise RuntimeError("Missing plan in state")

    steps = plan.get("steps", [])
    if not steps:
        raise RuntimeError("Plan has no steps")

    logs.append({"agent": "executor", "msg": "Executor started..."})

    results: Dict[str, Any] = {}

    for step in steps:
        step_id = step["id"]
        tool = step.get("tool")
        tool_input = step.get("input", {}) or {}

        if not tool:
            results[step_id] = {"skipped": True, "reason": "No tool"}
            continue

        try:
            # Route to appropriate tool handler
            if tool == "calendar.create_event":
                # Use direct Google Calendar API
                logs.append({"agent": "executor", "msg": f"Creating calendar event: {tool_input.get('title', 'Meeting')}"})
                
                result = await create_calendar_event(
                    title=tool_input.get("title", "Meeting"),
                    start_time=tool_input.get("start_time"),
                    end_time=tool_input.get("end_time"),
                    description=tool_input.get("description", ""),
                    attendees=tool_input.get("attendees", []),
                    timezone=tool_input.get("timezone", "Asia/Kolkata")
                )
                results[step_id] = result
                logs.append({"agent": "executor", "msg": f"✅ Event created: {result.get('event_id')}"})
                
            elif tool == "calendar.list_events":
                # List calendar events
                result = await list_calendar_events(
                    max_results=tool_input.get("max_results", 10),
                    time_min=tool_input.get("time_min")
                )
                results[step_id] = result
                logs.append({"agent": "executor", "msg": f"✅ Retrieved {result.get('count', 0)} events"})
                
            elif tool == "slack.post_message":
                # Use direct Slack API
                logs.append({"agent": "executor", "msg": f"Posting to Slack: {tool_input.get('channel', '#general')}"})
                
                result = await post_slack_message(
                    channel=tool_input.get("channel", "#general"),
                    text=tool_input.get("text", ""),
                    thread_ts=tool_input.get("thread_ts")
                )
                results[step_id] = result
                logs.append({"agent": "executor", "msg": f"✅ Message posted to Slack"})
                
            elif tool == "slack.list_channels":
                # List Slack channels
                result = await list_slack_channels()
                results[step_id] = result
                logs.append({"agent": "executor", "msg": f"✅ Retrieved {result.get('count', 0)} channels"})
                
            elif tool == "slack.read_messages":
                # Read Slack messages
                channel = tool_input.get("channel", "#general")
                limit = tool_input.get("limit", 100)
                logs.append({"agent": "executor", "msg": f"Reading messages from {channel}..."})
                
                result = await read_slack_messages(channel=channel, limit=limit)
                results[step_id] = result
                logs.append({"agent": "executor", "msg": f"✅ Retrieved {result.get('count', 0)} messages"})
                
            elif tool == "slack.summarize_messages":
                # Summarize Slack messages (requires previous read_messages step)
                # Get messages from previous step
                messages = []
                for prev_step_id, prev_result in results.items():
                    if isinstance(prev_result, dict) and "messages" in prev_result:
                        messages = prev_result["messages"]
                        break
                
                if not messages:
                    raise RuntimeError(
                        "No messages found to summarize. "
                        "The channel may only contain system messages (joins, leaves). "
                        "Try asking to read more messages with a higher limit."
                    )
                
                logs.append({"agent": "executor", "msg": f"Summarizing {len(messages)} messages with AI..."})
                summary = summarize_slack_messages(messages)
                
                result = {
                    "success": True,
                    "summary": summary,
                    "message_count": len(messages)
                }
                results[step_id] = result
                logs.append({"agent": "executor", "msg": f"✅ Summary generated"})
                
            else:
                # Fall back to MCP client for other tools
                client = MCPClient()
                out = await client.call_tool(name=tool, args=tool_input)
                results[step_id] = out
                logs.append({"agent": "executor", "msg": f"✅ Tool {tool} executed via MCP"})
                
        except Exception as e:
            error_msg = str(e)
            logs.append({"agent": "executor", "msg": f"❌ Execution failed at {step_id}: {error_msg}"})
            state["status"] = "FAILED"
            state["execution_results"] = results
            state["error"] = error_msg
            return state


    state["status"] = "DONE"  # Changed from COMPLETED to match graph router
    state["execution_results"] = results
    logs.append({"agent": "executor", "msg": "🎉 Execution completed successfully!"})
    return state


