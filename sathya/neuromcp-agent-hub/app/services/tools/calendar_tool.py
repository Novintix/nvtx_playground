"""
Direct Google Calendar integration
Bypasses MCP client to avoid circular dependency
"""
import httpx
from typing import Dict, Any
from datetime import datetime
from app.services.oauth.token_store import get_token


GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"


async def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    attendees: list = None,
    timezone: str = "Asia/Kolkata"
) -> Dict[str, Any]:
    """
    Create a Google Calendar event using OAuth tokens
    
    Args:
        title: Event title
        start_time: ISO format datetime (e.g., "2026-01-30T16:00:00+05:30")
        end_time: ISO format datetime
        description: Event description
        attendees: List of email addresses
        timezone: Timezone for the event
    
    Returns:
        Event details including event ID
    """
    # Get Google OAuth token
    token_data = await get_token("google")
    if not token_data:
        raise RuntimeError("Google Calendar not connected. Please authenticate first.")
    
    access_token = token_data.get("access_token")
    if not access_token:
        raise RuntimeError("No access token found for Google Calendar")
    
    # Build event payload
    event = {
        "summary": title,
        "description": description or f"Event: {title}",
        "start": {
            "dateTime": start_time,
            "timeZone": timezone
        },
        "end": {
            "dateTime": end_time,
            "timeZone": timezone
        }
    }
    
    # Add attendees if provided
    if attendees:
        event["attendees"] = [{"email": email} for email in attendees]
    
    # Make API call to create event
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=event,
            timeout=30.0
        )
        
        if response.status_code == 401:
            raise RuntimeError("Access token expired. Please re-authenticate with Google.")
        
        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            raise RuntimeError(f"Calendar API error: {response.status_code} - {error_data}")
        
        result = response.json()
        
        return {
            "success": True,
            "event_id": result.get("id"),
            "html_link": result.get("htmlLink"),
            "summary": result.get("summary"),
            "start": result.get("start", {}).get("dateTime"),
            "end": result.get("end", {}).get("dateTime"),
            "created": result.get("created")
        }


async def list_calendar_events(
    max_results: int = 10,
    time_min: str = None
) -> Dict[str, Any]:
    """
    List upcoming calendar events
    
    Args:
        max_results: Maximum number of events to return
        time_min: Minimum time for events (ISO format)
    
    Returns:
        List of events
    """
    token_data = await get_token("google")
    if not token_data:
        raise RuntimeError("Google Calendar not connected")
    
    access_token = token_data.get("access_token")
    
    params = {
        "maxResults": max_results,
        "orderBy": "startTime",
        "singleEvents": True
    }
    
    if time_min:
        params["timeMin"] = time_min
    else:
        params["timeMin"] = datetime.utcnow().isoformat() + "Z"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Failed to list events: {response.status_code}")
        
        result = response.json()
        events = result.get("items", [])
        
        return {
            "success": True,
            "count": len(events),
            "events": [
                {
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "start": event.get("start", {}).get("dateTime"),
                    "end": event.get("end", {}).get("dateTime"),
                    "html_link": event.get("htmlLink")
                }
                for event in events
            ]
        }