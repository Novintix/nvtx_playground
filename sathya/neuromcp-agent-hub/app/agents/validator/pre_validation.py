"""
Pre-validation: Quick checks on user input BEFORE planning
Catches obvious errors immediately without wasting LLM tokens
"""

import re
from typing import List, Tuple, Optional


def extract_emails_from_text(text: str) -> List[str]:
    """
    Extract potential email addresses from user's request text.
    Uses a simple regex pattern to find email-like strings.
    """
    # Simple email pattern - matches anything that looks like an email
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    
    # Also catch malformed emails with extra dots or weird patterns
    relaxed_pattern = r'\b[a-zA-Z0-9._%+-]+[@.]+[a-zA-Z0-9.-]*\b'
    
    matches = set()
    matches.update(re.findall(email_pattern, text))
    matches.update(re.findall(relaxed_pattern, text))
    
    return list(matches)


def validate_user_request(user_request: str) -> Tuple[bool, Optional[str]]:
    """
    Quick validation of user's raw input before sending to planner.
    
    Returns:
        (is_valid, error_message)
    """
    from app.agents.validator.validation_rules import validate_email
    from app.agents.validator.rate_limiter import check_rate_limit
    
    if not user_request or not user_request.strip():
        return False, "Request cannot be empty"
    
    # Check overall rate limit (before specific tool checks)
    is_allowed, rate_error = check_rate_limit("overall", user_request)
    if not is_allowed:
        return False, rate_error
    
    # Extract and validate any emails in the request
    emails = extract_emails_from_text(user_request)
    
    for email in emails:
        is_valid, error = validate_email(email)
        if not is_valid:
            return False, f"Invalid email in your request: {error}"
    
    return True, None
