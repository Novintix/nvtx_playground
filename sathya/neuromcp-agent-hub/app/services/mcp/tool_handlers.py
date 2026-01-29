from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict

# Import handlers ONLY when calling /mcp/call, not when listing tools
from app.services.tools.slack_tool import slack_post_message
from app.services.tools.calendar_tool import calendar_create_event

TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Awaitable[Any]]] = {
    "slack.post_message": slack_post_message,
    "calendar.create_event": calendar_create_event,
}
