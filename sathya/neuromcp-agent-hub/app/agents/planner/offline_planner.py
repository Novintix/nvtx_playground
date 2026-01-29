# app/agents/planner/offline_planner.py
from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re


def _parse_time_and_date(user_request: str, tz: str) -> tuple[str, str]:
    """
    Parse date and time from user request
    Returns (start_iso, end_iso)
    """
    z = ZoneInfo(tz)
    now = datetime.now(z)
    req = user_request.lower()
    
    # Determine date (today vs tomorrow)
    if "today" in req:
        target_date = now.date()
    elif "tomorrow" in req:
        target_date = (now + timedelta(days=1)).date()
    else:
        # Default to tomorrow if no date specified
        target_date = (now + timedelta(days=1)).date()
    
    # Parse time (2pm, 3pm, 14:00, etc.)
    hour = 16  # default 4 PM
    
    # Try to match patterns like "2 pm", "2pm", "14:00"
    time_patterns = [
        r"(\d{1,2})\s*pm",           # "2 pm" or "2pm"
        r"(\d{1,2})\s*am",           # "9 am" or "9am"
        r"(\d{1,2}):(\d{2})\s*pm",   # "2:30 pm"
        r"(\d{1,2}):(\d{2})\s*am",   # "9:30 am"
        r"at\s*(\d{1,2})",           # "at 2" or "at 14"
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, req)
        if match:
            hour_str = match.group(1)
            hour = int(hour_str)
            
            # Convert PM/AM
            if "pm" in pattern and hour < 12:
                hour += 12
            elif "am" in pattern and hour == 12:
                hour = 0
            break
    
    # Create datetime
    start = datetime(target_date.year, target_date.month, target_date.day, hour, 0, tzinfo=z)
    
    # If the time has already passed today, schedule for tomorrow
    if target_date == now.date() and start < now:
        target_date = (now + timedelta(days=1)).date()
        start = datetime(target_date.year, target_date.month, target_date.day, hour, 0, tzinfo=z)
    
    end = start + timedelta(hours=1)
    
    return start.isoformat(), end.isoformat()


def _extract_attendees(user_request: str) -> list[str]:
    """
    Extract email addresses from user request
    """
    # Pattern to match email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, user_request)
    return emails


def _extract_title(user_request: str) -> str:
    """
    Try to extract a meaningful meeting title from the request
    """
    req = user_request.lower()
    
    # Look for patterns like "meeting with X"
    patterns = [
        r"meeting with ([^,\.]+)",
        r"schedule ([^,\.]+?) at",
        r"create ([^,\.]+?) event",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, req)
        if match:
            title = match.group(1).strip().title()
            # Clean up common words
            title = re.sub(r'\bat\s+\d', '', title).strip()
            if title and len(title) > 2:
                return title
    
    # Default fallback
    return "Meeting"


def build_plan(user_request: str, tools: list[dict], tz: str = "Asia/Kolkata") -> dict:
    """
    Enhanced rule-based planner with smart date/time parsing
    """
    req = user_request.lower()
    
    # Parse date and time
    start_iso, end_iso = _parse_time_and_date(user_request, tz)
    
    # Extract attendees
    attendees = _extract_attendees(user_request)
    
    # Extract title
    title = _extract_title(user_request)
    
    # Extract Slack channel
    channel = "#general"
    channel_match = re.search(r"(#\w+)", user_request)
    if channel_match:
        channel = channel_match.group(1)
    
    plan = {
        "goal": user_request,
        "steps": []
    }
    
    # Slack message reading and summarization
    if ("read" in req or "fetch" in req or "get" in req) and ("message" in req or "slack" in req) and ("summarize" in req or "summarise" in req or "summary" in req):
        # Two-step: read messages then summarize
        plan["steps"].append({
            "id": "S1",
            "action": "Read Slack messages",
            "tool": "slack.read_messages",
            "input": {
                "channel": channel,
                "limit": 100
            },
            "depends_on": [],
            "expected_output": "List of messages"
        })
        
        plan["steps"].append({
            "id": "S2",
            "action": "Summarize messages with AI",
            "tool": "slack.summarize_messages",
            "input": {},
            "depends_on": ["S1"],
            "expected_output": "Summary text"
        })
    
    # Calendar event creation
    elif "meeting" in req or "schedule" in req or "event" in req:
        event_input = {
            "title": title,
            "start_time": start_iso,
            "end_time": end_iso,
            "timezone": tz
        }
        
        # Add attendees if found
        if attendees:
            event_input["attendees"] = attendees
        
        plan["steps"].append({
            "id": "S1",
            "action": "Create meeting event",
            "tool": "calendar.create_event",
            "input": event_input,
            "depends_on": [],
            "expected_output": "Event ID"
        })
    
    # Slack notification or standalone message
    if ("slack" in req or "post" in req or "notify" in req) and not any(s.get("tool") == "calendar.create_event" for s in plan["steps"]):
        # This is a standalone Slack message, extract the actual message
        message_text = user_request
        
        # Try to extract message content
        msg_patterns = [
            r"message\s+['\"](.+?)['\"]",      # "message 'hi team'"
            r"send\s+['\"](.+?)['\"]",         # "send 'hi team'"
            r"post\s+['\"](.+?)['\"]",         # "post 'hi team'"
            r"slack\s+['\"](.+?)['\"]",        # "slack 'hi team'"
            r"like\s+(.+?)\s+to",              # "like hi team to"
            r"say\s+(.+?)\s+to",               # "say hello to"
            r"message\s+like\s+(.+)",          # "message like hi team"
        ]
        
        for pattern in msg_patterns:
            match = re.search(pattern, req)
            if match:
                message_text = match.group(1).strip()
                break
        
        plan["steps"].append({
            "id": "S1" if not plan["steps"] else "S2",
            "action": "Post message in Slack",
            "tool": "slack.post_message",
            "input": {
                "channel": channel,
                "text": message_text
            },
            "depends_on": ["S1"] if any(s["id"] == "S1" for s in plan["steps"]) else [],
            "expected_output": "Message ID"
        })
    elif ("slack" in req or "post" in req or "notify" in req) and any(s.get("tool") == "calendar.create_event" for s in plan["steps"]):
        # This is a meeting notification (calendar + slack)
        time_match = re.search(r"(\d{1,2})\s*(pm|am)", req)
        time_str = time_match.group(0) if time_match else "soon"
        
        plan["steps"].append({
            "id": "S2",
            "action": "Post meeting notification in Slack",
            "tool": "slack.post_message",
            "input": {
                "channel": channel,
                "text": f"Meeting '{title}' scheduled for {time_str}"
            },
            "depends_on": ["S1"],
            "expected_output": "Message ID"
        })
    
    # Fallback if nothing matched
    if not plan["steps"]:
        # Extract the message content for Slack
        message_text = user_request
        
        # Try to extract message after keywords like "send", "post", "message"
        msg_patterns = [
            r"send.*?message.*?[\"'](.+?)[\"']",  # "send message 'hi team'"
            r"send.*?[\"'](.+?)[\"']",             # "send 'hi team'"  
            r"post.*?[\"'](.+?)[\"']",             # "post 'hi team'"
            r"slack.*?[\"'](.+?)[\"']",            # "slack 'hi team'"
            r"message.*?like\s+(.+)",              # "message like hi team"
            r"say\s+(.+)",                         # "say hi team"
        ]
        
        for pattern in msg_patterns:
            match = re.search(pattern, req)
            if match:
                message_text = match.group(1).strip()
                break
        
        plan["steps"].append({
            "id": "S1",
            "action": "Post message in Slack",
            "tool": "slack.post_message",
            "input": {"channel": channel, "text": message_text},
            "depends_on": [],
            "expected_output": "Message ID"
        })
    
    return plan


