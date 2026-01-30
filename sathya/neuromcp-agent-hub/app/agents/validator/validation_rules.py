"""
Data Validation Rules for NeuroMCP Agent
Provides universal validation functions for tool inputs
"""

import re
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from urllib.parse import urlparse


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address format.
    
    Returns:
        (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email cannot be empty"
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, f"Invalid email format: '{email}'"
    
    # Additional checks
    if '..' in email:
        return False, f"Invalid email (consecutive dots): '{email}'"
    
    if email.startswith('.') or email.startswith('@'):
        return False, f"Invalid email format: '{email}'"
    
    # Dot cannot be immediately before or after @
    if '.@' in email or '@.' in email:
        return False, f"Invalid email format (dot before/after @): '{email}'"
    
    # Local part cannot end with dot
    local_part = email.split('@')[0]
    if local_part.endswith('.'):
        return False, f"Invalid email format: '{email}'"
    
    return True, None


def validate_datetime(dt_str: str, allow_past: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate datetime string and ensure it's not in the past.
    
    Args:
        dt_str: ISO format datetime string
        allow_past: If True, past dates are allowed
        
    Returns:
        (is_valid, error_message)
    """
    if not dt_str or not isinstance(dt_str, str):
        return False, "Datetime cannot be empty"
    
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False, f"Invalid datetime format: '{dt_str}' (expected ISO format like '2026-02-05T18:00:00+05:30')"
    
    # Check if date is in the past
    if not allow_past:
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        # Allow 5 minute buffer for processing time
        min_time = now - timedelta(minutes=5)
        
        if dt < min_time:
            return False, f"Datetime cannot be in the past: '{dt_str}'"
    
    # Check if date is too far in future (beyond 2 years)
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    max_future = now + timedelta(days=730)  # 2 years
    
    if dt > max_future:
        return False, f"Datetime too far in future (max 2 years): '{dt_str}'"
    
    return True, None


def validate_event_times(start_time: str, end_time: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that start time is before end time and duration is reasonable.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False, "Invalid datetime format for event times"
    
    # Start must be before end
    if start_dt >= end_dt:
        return False, "Event start time must be before end time"
    
    # Check duration
    duration = end_dt - start_dt
    
    # Minimum duration: 15 minutes
    if duration < timedelta(minutes=15):
        return False, "Event duration too short (minimum 15 minutes)"
    
    # Maximum duration: 24 hours
    if duration > timedelta(hours=24):
        return False, "Event duration too long (maximum 24 hours)"
    
    return True, None


def validate_attendees(attendees: List[str], max_count: int = 100) -> Tuple[bool, Optional[str]]:
    """
    Validate list of attendee email addresses.
    
    Args:
        attendees: List of email addresses
        max_count: Maximum number of attendees allowed
        
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(attendees, list):
        return False, "Attendees must be a list"
    
    if len(attendees) == 0:
        return True, None  # Empty list is okay
    
    # Check count
    if len(attendees) > max_count:
        return False, f"Too many attendees: {len(attendees)} (maximum {max_count})"
    
    # Validate each email
    seen = set()
    for email in attendees:
        # Check for duplicates
        email_lower = email.lower() if isinstance(email, str) else ""
        if email_lower in seen:
            return False, f"Duplicate attendee email: '{email}'"
        seen.add(email_lower)
        
        # Validate email format
        is_valid, error = validate_email(email)
        if not is_valid:
            return False, error
    
    return True, None


def validate_slack_channel(channel: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Slack channel name format.
    
    Returns:
        (is_valid, error_message)
    """
    if not channel or not isinstance(channel, str):
        return False, "Channel name cannot be empty"
    
    # Must start with #
    if not channel.startswith('#'):
        return False, f"Channel name must start with '#': '{channel}'"
    
    # Channel name without #
    channel_name = channel[1:]
    
    # Must not be empty after #
    if not channel_name:
        return False, "Channel name cannot be just '#'"
    
    # Slack channel name rules: lowercase, numbers, hyphens, underscores
    # Length: 1-80 characters
    if len(channel_name) > 80:
        return False, f"Channel name too long (max 80 characters): '{channel}'"
    
    # Valid characters: a-z, 0-9, -, _
    if not re.match(r'^[a-z0-9_-]+$', channel_name):
        return False, f"Invalid channel name format (use lowercase, numbers, hyphens, underscores only): '{channel}'"
    
    return True, None


def validate_message_content(text: str, max_length: int = 4000) -> Tuple[bool, Optional[str]]:
    """
    Validate message content.
    
    Args:
        text: Message text
        max_length: Maximum message length (Slack limit is 40000, but 4000 is reasonable)
        
    Returns:
        (is_valid, error_message)
    """
    if not text or not isinstance(text, str):
        return False, "Message text cannot be empty"
    
    # Check length
    if len(text) > max_length:
        return False, f"Message too long: {len(text)} characters (maximum {max_length})"
    
    # Check for suspicious patterns (API keys, tokens)
    suspicious_patterns = [
        r'(api[_-]?key|apikey)[\s:=]+[a-zA-Z0-9_-]{20,}',
        r'(secret|token|password)[\s:=]+[a-zA-Z0-9_-]{20,}',
        r'sk-[a-zA-Z0-9]{20,}',  # Common API key format
        r'[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}',  # Credit card pattern
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Message may contain sensitive data (API key, password, or credit card). Please remove sensitive information."
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL format.
    
    Returns:
        (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty"
    
    try:
        result = urlparse(url)
        
        # Must have scheme and netloc
        if not result.scheme or not result.netloc:
            return False, f"Invalid URL format: '{url}'"
        
        # Scheme should be http or https
        if result.scheme not in ['http', 'https']:
            return False, f"URL must use http or https: '{url}'"
        
        return True, None
        
    except Exception:
        return False, f"Invalid URL: '{url}'"


def validate_calendar_event_input(event_input: dict) -> List[str]:
    """
    Validate calendar event input data.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Validate required fields exist
    if 'start_time' not in event_input:
        errors.append("Missing required field: start_time")
        return errors
    
    if 'end_time' not in event_input:
        errors.append("Missing required field: end_time")
        return errors
    
    # Validate start time
    is_valid, error = validate_datetime(event_input['start_time'], allow_past=False)
    if not is_valid:
        errors.append(f"start_time: {error}")
    
    # Validate end time
    is_valid, error = validate_datetime(event_input['end_time'], allow_past=False)
    if not is_valid:
        errors.append(f"end_time: {error}")
    
    # Validate start < end
    if 'start_time' in event_input and 'end_time' in event_input:
        is_valid, error = validate_event_times(event_input['start_time'], event_input['end_time'])
        if not is_valid:
            errors.append(error)
    
    # Validate attendees if present
    if 'attendees' in event_input:
        is_valid, error = validate_attendees(event_input['attendees'])
        if not is_valid:
            errors.append(f"attendees: {error}")
    
    return errors


def validate_slack_message_input(message_input: dict) -> List[str]:
    """
    Validate Slack message input data.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Validate channel
    if 'channel' not in message_input:
        errors.append("Missing required field: channel")
    else:
        is_valid, error = validate_slack_channel(message_input['channel'])
        if not is_valid:
            errors.append(f"channel: {error}")
    
    # Validate message text
    if 'text' not in message_input:
        errors.append("Missing required field: text")
    else:
        is_valid, error = validate_message_content(message_input['text'])
        if not is_valid:
            errors.append(f"text: {error}")
    
    return errors
