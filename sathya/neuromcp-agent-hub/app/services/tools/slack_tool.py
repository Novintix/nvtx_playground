"""
Direct Slack integration
Bypasses MCP client to avoid circular dependency
"""
import httpx
from typing import Dict, Any
from app.services.oauth.token_store import get_token


async def post_slack_message(
    channel: str,
    text: str,
    thread_ts: str = None
) -> Dict[str, Any]:
    """
    Post a message to Slack using OAuth token
    
    Args:
        channel: Channel name (with # or without) or channel ID
        text: Message text
        thread_ts: Optional thread timestamp to reply to
    
    Returns:
        Message details including timestamp
    """
    # Get Slack OAuth token
    token_data = await get_token("slack")
    if not token_data:
        raise RuntimeError("Slack not connected. Please authenticate first.")
    
    # Token might be stored as string or dict
    if isinstance(token_data, str):
        access_token = token_data
    else:
        access_token = token_data.get("access_token") or token_data
    
    if not access_token:
        raise RuntimeError("No access token found for Slack")
    
    # Ensure channel starts with # for channel names, but allow channel IDs
    if not channel.startswith("#") and not channel.startswith("C"):
        channel = f"#{channel}"
    
    # Build message payload
    payload = {
        "channel": channel,
        "text": text
    }
    
    if thread_ts:
        payload["thread_ts"] = thread_ts
    
    # Make API call to post message
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Slack API HTTP error: {response.status_code}")
        
        result = response.json()
        
        if not result.get("ok"):
            error = result.get("error", "unknown_error")
            
            # Provide helpful error messages
            if error == "channel_not_found":
                raise RuntimeError(
                    f"❌ Channel '{channel}' not found. Please specify a valid channel in your Slack workspace. "
                    f"Example: 'send slack message like hi team to #random' (check your Slack sidebar for channel names)"
                )
            elif error == "not_in_channel":
                raise RuntimeError(
                    f"❌ Bot is not a member of '{channel}'. "
                    f"Please invite the bot to the channel first, or use a different channel you're both in."
                )
            elif error == "invalid_auth":
                raise RuntimeError("❌ Slack authentication expired. Please reconnect Slack OAuth.")
            else:
                raise RuntimeError(f"❌ Slack error: {error}")
        
        return {
            "success": True,
            "channel": result.get("channel"),
            "ts": result.get("ts"),
            "message": {
                "text": text,
                "timestamp": result.get("ts")
            }
        }


async def list_slack_channels() -> Dict[str, Any]:
    """
    List Slack channels
    
    Returns:
        List of channels
    """
    token_data = await get_token("slack")
    if not token_data:
        raise RuntimeError("Slack not connected")
    
    if isinstance(token_data, str):
        access_token = token_data
    else:
        access_token = token_data.get("access_token") or token_data
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/conversations.list",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Failed to list channels: {response.status_code}")
        
        result = response.json()
        
        if not result.get("ok"):
            raise RuntimeError(f"Slack error: {result.get('error')}")
        
        channels = result.get("channels", [])
        
        return {
            "success": True,
            "count": len(channels),
            "channels": [
                {
                    "id": ch.get("id"),
                    "name": ch.get("name"),
                    "is_private": ch.get("is_private"),
                    "is_member": ch.get("is_member")
                }
                for ch in channels
            ]
        }


async def read_slack_messages(
    channel: str,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Read messages from a Slack channel
    
    Args:
        channel: Channel name (with # or without) or channel ID
        limit: Maximum number of messages to fetch (default 100)
    
    Returns:
        List of messages from the channel
    """
    token_data = await get_token("slack")
    if not token_data:
        raise RuntimeError("Slack not connected")
    
    if isinstance(token_data, str):
        access_token = token_data
    else:
        access_token = token_data.get("access_token") or token_data
    
    # If channel name starts with #, we need to get the channel ID first
    channel_id = channel
    if channel.startswith("#"):
        # Get channel ID from name
        channels_result = await list_slack_channels()
        matching_channels = [
            ch for ch in channels_result.get("channels", [])
            if f"#{ch['name']}" == channel
        ]
        if not matching_channels:
            raise RuntimeError(f"Channel '{channel}' not found")
        channel_id = matching_channels[0]["id"]
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/conversations.history",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "channel": channel_id,
                "limit": limit
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Failed to read messages: {response.status_code}")
        
        result = response.json()
        
        if not result.get("ok"):
            error = result.get("error", "unknown_error")
            if error == "channel_not_found":
                raise RuntimeError(f"Channel '{channel}' not found")
            elif error == "not_in_channel":
                raise RuntimeError(f"Bot is not a member of '{channel}'")
            else:
                raise RuntimeError(f"Slack error: {error}")
        
        messages = result.get("messages", [])
        
        # Filter out only system messages (joins, leaves, etc.)
        # Keep bot messages as they are legitimate content
        filtered_messages = [
            {
                "text": msg.get("text", ""),
                "user": msg.get("user", "unknown"),
                "timestamp": msg.get("ts", ""),
                "type": msg.get("type", "message")
            }
            for msg in messages
            if (
                msg.get("type") == "message" and 
                msg.get("text") and
                not msg.get("subtype")  # Only exclude system messages (joins, leaves, etc.)
            )
        ]
        
        return {
            "success": True,
            "channel": channel,
            "count": len(filtered_messages),  # Use filtered count, not raw count
            "messages": filtered_messages
        }
