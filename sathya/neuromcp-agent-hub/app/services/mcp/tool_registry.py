from __future__ import annotations
from typing import Any, Dict, List, Callable, Awaitable

from app.services.tools.slack_tool import slack_post_message
from app.services.tools.calendar_tool import calendar_create_event

TOOL_REGISTRY: List[Dict[str, Any]] = [
    {
        "name": "slack.post_message",
        "description": "Post a message to Slack",
        "requires_approval": True,
        "handler": slack_post_message,
        "schema": {
            "channel": "str",
            "text": "str"
        },
    },
    {
        "name": "calendar.create_event",
        "description": "Create a Google Calendar event",
        "requires_approval": True,
        "handler": calendar_create_event,
        "schema": {
            "title": "str",
            "start_time": "ISO datetime str",
            "end_time": "ISO datetime str",
            "timezone": "str"
        },
    },
]
