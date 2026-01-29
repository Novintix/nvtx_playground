from __future__ import annotations
from typing import Any, Dict, List

TOOL_REGISTRY: List[Dict[str, Any]] = [
    {
        "name": "slack.post_message",
        "description": "Post a message to a Slack channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["channel", "text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "calendar.create_event",
        "description": "Create an event in Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"},
                "timezone": {"type": "string"},
            },
            "required": ["title", "start_time", "end_time", "timezone"],
            "additionalProperties": False,
        },
    },
]
