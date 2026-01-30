from __future__ import annotations

from typing import Any, Dict, List

from app.services.mcp.mcp_client import MCPClient


client = MCPClient()


async def discover_tools() -> List[Dict[str, Any]]:
    """Discover available tools - both MCP and direct integrations"""
    
    # Hardcoded direct integration tools (Calendar + Slack)
    direct_tools = [
        {
            "name": "calendar.create_event",
            "description": "Create a Google Calendar event",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "timezone": {"type": "string"},
                    "attendees": {"type": "array"}
                }
            }
        },
        {
            "name": "calendar.list_events",
            "description": "List upcoming Google Calendar events",
            "input_schema": {"type": "object", "properties": {}}
        },
        {
            "name": "slack.post_message",
            "description": "Post a message to a Slack channel",
            "input_schema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "text": {"type": "string"}
                }
            }
        },
        {
            "name": "slack.read_messages",
            "description": "Read messages from a Slack channel",
            "input_schema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "limit": {"type": "integer"}
                }
            }
        },
        {
            "name": "slack.summarize_messages",
            "description": "Summarize Slack messages using AI",
            "input_schema": {"type": "object", "properties": {}}
        },
        {
            "name": "slack.list_channels",
            "description": "List Slack channels",
            "input_schema": {"type": "object", "properties": {}}
        }
    ]
    
    # Try to get MCP tools (may timeout, so we don't rely on them)
    try:
        data = await client.list_tools()
        mcp_tools = data.get("tools", [])
        
        # Normalize schema keys: convert inputSchema to input_schema
        for tool in mcp_tools:
            if "inputSchema" in tool and "input_schema" not in tool:
                tool["input_schema"] = tool.pop("inputSchema")
        
        return direct_tools + mcp_tools
    except:
        # If MCP fails, just return direct tools
        return direct_tools