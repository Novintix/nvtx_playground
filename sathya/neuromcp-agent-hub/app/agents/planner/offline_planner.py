# app/agents/planner/offline_planner.py
from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re


def _parse_time_and_date(user_request: str, tz: str) -> tuple[str, str]:
    """
    Enhanced date and time parsing from user request
    Returns (start_iso, end_iso)
    """
    z = ZoneInfo(tz)
    now = datetime.now(z)
    req = user_request.lower()
    
    # Parse date - handle month names, specific dates
    target_date = None
    
    # Month name patterns (feb 1, february 1st, 1 feb, etc.)
    month_map = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }
    
    # Try patterns like "feb 1", "february 1st", "1 feb"
    for month_name, month_num in month_map.items():
        patterns = [
            rf"{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?",  # "feb 1" or "feb 1st"
            rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_name}",  # "1 feb" or "1st feb"
        ]
        for pattern in patterns:
            match = re.search(pattern, req)
            if match:
                day = int(match.group(1))
                year = now.year
                # If the date has passed this year, assume next year
                try:
                    target_date = datetime(year, month_num, day, tzinfo=z).date()
                    if target_date < now.date():
                        target_date = datetime(year + 1, month_num, day, tzinfo=z).date()
                except ValueError:
                    # Invalid date like Feb 30
                    continue
                break
        if target_date:
            break
    
    # If no month pattern, check for "today" or "tomorrow"
    if not target_date:
        if "today" in req:
            target_date = now.date()
        elif "tomorrow" in req:
            target_date = (now + timedelta(days=1)).date()
        else:
            # Default to tomorrow
            target_date = (now + timedelta(days=1)).date()
    
    # Parse time with better patterns
    hour = 16  # default 4 PM
    minute = 0
    
    time_patterns = [
        (r"(\d{1,2})\.(\d{2})\s*pm", True),      # "9.00 pm"
        (r"(\d{1,2}):(\d{2})\s*pm", True),       # "9:00 pm"
        (r"(\d{1,2})\s*pm", True),               # "9 pm"
        (r"(\d{1,2})\.(\d{2})\s*am", False),     # "9.00 am"
        (r"(\d{1,2}):(\d{2})\s*am", False),      # "9:00 am"  
        (r"(\d{1,2})\s*am", False),              # "9 am"
        (r"at\s+(\d{1,2})", None),               # "at 9" (ambiguous)
    ]
    
    for pattern, is_pm in time_patterns:
        match = re.search(pattern, req)
        if match:
            hour = int(match.group(1))
            if len(match.groups()) > 1:
                minute = int(match.group(2))
            
            # Convert PM/AM
            if is_pm is True and hour < 12:
                hour += 12
            elif is_pm is False and hour == 12:
                hour = 0
            break
    
    # Create datetime
    start = datetime(target_date.year, target_date.month, target_date.day, hour, minute, tzinfo=z)
    
    # If scheduling for today and time has passed, move to tomorrow
    if target_date == now.date() and start < now:
        target_date = (now + timedelta(days=1)).date()
        start = datetime(target_date.year, target_date.month, target_date.day, hour, minute, tzinfo=z)
    
    end = start + timedelta(hours=1)
    
    return start.isoformat(), end.isoformat()


def _extract_attendees(user_request: str) -> list[str]:
    """Extract email addresses from user request"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, user_request)
    return emails


def _extract_title(user_request: str) -> str:
    """
    Extract meaningful meeting title from the request
    """
    req = user_request.lower()
    
    # Remove common noise words
    cleaned = re.sub(r'\b(mark|book|schedule|create|set up|setup|in|the|calender|calendar|like|with|at|on)\b', '', req, flags=re.IGNORECASE)
    
    # Look for patterns before date/time keywords
    patterns = [
        r"^(.*?)\s+(?:at|on|for|@)\s+\d",           # "presentation meeting at 9pm"
        r"^(.*?)\s+(?:with|to)\s+[\w@.]+@",         # "project review with email@"
        r"^(.*?)\s+(?:feb|jan|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",  # "team sync feb 1"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Clean up and capitalize
            title = re.sub(r'\s+', ' ', title).strip()
            if len(title) > 3:
                return title.title()
    
    # Fallback: extract first few meaningful words
    words = [w for w in cleaned.split() if len(w) > 2 and not w.startswith('@')]
    if len(words) >= 2:
        return ' '.join(words[:3]).title()
    
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
    elif "meeting" in req or "schedule" in req or "event" in req or "mark" in req or "book" in req:
        event_input = {
            "title": title,
            "start_time": start_iso,
            "end_time": end_iso,
            "timezone": tz
        }
        
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
    if ("slack" in req or "post" in req or "notify" in req or "send" in req) and not any(s.get("tool") == "calendar.create_event" for s in plan["steps"]):
        # Standalone Slack message - extract actual message content
        message_text = user_request
        
        msg_patterns = [
            r"message\s+['\"](.+?)['\"]",                      # "message 'text'"
            r"send\s+['\"](.+?)['\"]",                         # "send 'text'"
            r"post\s+['\"](.+?)['\"]",                         # "post 'text'"
            r"slack\s+['\"](.+?)['\"]",                        # "slack 'text'"
            r"like\s+(.+?)\s+in\s+#",                          # "like X in #channel"
            r"like\s+(.+?)\s+to\s+#",                          # "like X to #channel"
            r"message\s+like\s+(.+?)\s+(?:in|to)\s+#",        # "message like X in/to #channel"
            r"like\s+(.+?)\s+(?:in|to)\s+(?:#\w+|\w+\s+group)", # "like X in #channel" or "like X in slack group"
            r"(?:send|post)\s+(?:message\s+)?like\s+(.+?)\s+(?:in|to)", # "send like X in/to"
        ]
        
        for pattern in msg_patterns:
            match = re.search(pattern, req, re.IGNORECASE)
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
        # Meeting notification
        plan["steps"].append({
            "id": "S2",
            "action": "Post meeting notification in Slack",
            "tool": "slack.post_message",
            "input": {
                "channel": channel,
                "text": f"📅 Meeting '{title}' scheduled"
            },
            "depends_on": ["S1"],
            "expected_output": "Message ID"
        })
    
    # Fallback
    if not plan["steps"]:
        message_text = user_request
        
        for pattern in [r"like\s+(.+)", r"say\s+(.+)"]:
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
