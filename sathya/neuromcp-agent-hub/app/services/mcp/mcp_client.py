import os
import requests
from typing import List, Dict, Any


class MCPClient:
    def __init__(self, base_url: str | None = None, prefix: str | None = None):
        self.base_url = (base_url or os.getenv("MCP_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.prefix = (prefix or os.getenv("MCP_PREFIX", "/mcp/mcp")).rstrip("/")

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{self.prefix}{path}"

    async def list_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all available MCP tools"""
        # The endpoint doesn't support listing, so use hardcoded tools
        print(f"Using hardcoded tool list (MCP server doesn't provide tools/list)")
        return {"tools": get_default_tools()}

    async def call_tool(self, name: str, args: dict):
        """Call an MCP tool"""
        payload = {"name": name, "arguments": args}
        r = requests.post(self._url("/call"), json=payload, timeout=30)
        r.raise_for_status()
        return r.json()


def get_default_tools() -> List[Dict[str, Any]]:
    """Default tools available in the system"""
    return [
        {
            "name": "calendar.create_event",
            "description": "Create a calendar event. Attendees should be provided as an array of email address strings.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "ISO format datetime (e.g., 2026-01-30T16:00:00+05:30)"},
                    "end_time": {"type": "string", "description": "ISO format datetime"},
                    "description": {"type": "string", "description": "Event description (optional)"},
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses (e.g., ['user@example.com'])"
                    },
                    "timezone": {"type": "string", "description": "Timezone (default: Asia/Kolkata)"}
                },
                "required": ["title", "start_time", "end_time"]
            }
        },
        {
            "name": "slack.post_message",
            "description": "Post a message to Slack",
            "input_schema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "text": {"type": "string"}
                },
                "required": ["channel", "text"]
            }
        }
    ]