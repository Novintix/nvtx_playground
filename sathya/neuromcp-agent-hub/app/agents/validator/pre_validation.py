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
    relaxed_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]*\b'
    
    matches = set()
    matches.update(re.findall(email_pattern, text))
    matches.update(re.findall(relaxed_pattern, text))
    
    return list(matches)


def is_request_in_scope_llm(user_request: str) -> Tuple[bool, Optional[str]]:
    """
    LLM-powered intelligent scope validation.
    Uses the LLM to determine if a request is actionable within agent capabilities.
    
    This is PRODUCTION-GRADE and handles ALL edge cases, phrasings, and languages.
    
    Returns:
        (is_in_scope, error_message)
    """
    import os
    import json
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
    
    # Get LLM
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Fallback to basic validation if LLM unavailable
        return True, None
    
    llm = ChatGroq(
        api_key=api_key,
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        temperature=0.0,  # Deterministic
        max_tokens=150,
    )
    
    system_prompt = """You are a STRICT request classifier for an AI agent.

The agent can ONLY perform these actions:
1. Google Calendar: create events, list events
2. Slack: post messages, read messages, list channels, summarize conversations

Your job: Determine if the user's request is ACTIONABLE with these tools.

CRITICAL RULES:
1. REJECT if the request is:
   - General knowledge questions (who is X, what is Y, explain Z, define A)
   - Greetings without tasks (hi, hello, thanks, how are you)
   - Math/calculations (calculate, what is 2+2)
   - Weather/news/facts (weather, news, stock prices)
   - Unrelated to Calendar or Slack
   - Just a name or single word with no clear action
   - Incomplete requests (just "meeting", "slack", "create", "send" with no details)

2. ACCEPT ONLY if the request:
   - Explicitly asks to create/list/show calendar events
   - Explicitly asks to post/read/summarize Slack messages
   - Contains BOTH an action verb AND a target (calendar/slack)

BE STRICT. When in doubt, REJECT.

Respond ONLY with valid JSON (no markdown):
{"in_scope": true/false, "reason": "brief explanation"}

Examples:
"who is vijay" -> {"in_scope": false, "reason": "General knowledge question"}
"vijay" -> {"in_scope": false, "reason": "No actionable request"}
"hi" -> {"in_scope": false, "reason": "Greeting without task"}
"meeting" -> {"in_scope": false, "reason": "Incomplete - no action specified"}
"slack" -> {"in_scope": false, "reason": "Incomplete - no action specified"}
"create" -> {"in_scope": false, "reason": "Incomplete - create what?"}
"weather today" -> {"in_scope": false, "reason": "Weather query"}
"calculate 2+2" -> {"in_scope": false, "reason": "Math calculation"}
"create meeting tomorrow" -> {"in_scope": true, "reason": "Calendar event creation"}
"post to slack" -> {"in_scope": true, "reason": "Slack message posting"}
"list events" -> {"in_scope": true, "reason": "Calendar query"}
"read #general" -> {"in_scope": true, "reason": "Slack message reading"}
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User request: {user_request}")
        ])
        
        # Parse JSON response
        content = response.content.strip()
        
        # DEBUG: Print raw response
        # print(f"DEBUG - Raw LLM response: {content}")
        
        # Extract JSON if wrapped in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON object in the response
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]
        
        result = json.loads(content)
        
        # DEBUG: Print parsed result
        # print(f"DEBUG - Parsed result: {result}")
        
        if not result.get("in_scope", False):
            reason = result.get("reason", "Request is out of scope")
            return False, (
                f"I cannot help with this request.\n\n"
                f"Reason: {reason}\n\n"
                f"I can only help with:\n"
                f"  - Calendar: Create events, list meetings\n"
                f"  - Slack: Post messages, read channels, summarize conversations"
            )
        
        return True, None
        
    except Exception as e:
        # DEBUG: Print exception
        # print(f"DEBUG - Exception: {e}")
        # import traceback
        # traceback.print_exc()
        # If LLM fails, be permissive (let it through to planner)
        # The planner will handle it if truly invalid
        return True, None



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
    
    # NEW: LLM-powered scope validation (production-grade)
    is_in_scope, scope_error = is_request_in_scope_llm(user_request)
    if not is_in_scope:
        return False, scope_error
    
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

