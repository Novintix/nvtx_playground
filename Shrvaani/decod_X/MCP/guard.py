from datetime import datetime

def validate_credentials(user_id: str, role: str) -> bool:
    # Mock credential validation
    # In a real system, this would check against an IAM system
    valid_roles = ["Admin", "Analyst", "Guest"]
    if role not in valid_roles:
        return False
    return True

def authorize(query: str, user_role: str = "Guest", tool_name: str = None) -> bool:
    """
    Validates if the user has permission to perform the action.
    """
    if not validate_credentials("mock_user", user_role):
        return False

    # 1. Tool Access Control
    if tool_name:
        # Example: Guests cannot use 'modify' tools (if we had them)
        pass 

    # 2. Query Content Restrictions
    blocked_keywords = ["approve", "execute", "delete", "modify"]
    
    # Guest Restrictions
    if user_role == "Guest":
        # Guests cannot ask for approvals or modifications
        if any(word in query.lower() for word in blocked_keywords):
            return False
        
        # Guests additionally cannot see sensitive "Policy" validation text directly (hypothetical restriction)
        # For this demo, let's say Guest cannot ask about "override" or "exception"
        if "override" in query.lower() or "exception" in query.lower():
            return False

    # Admin/Analyst Access
    # (Allow everything for now)

    return True

def audit_log(query: str, user: str = "Unknown", role: str = "Unknown", outcome: str = "Allowed"):
    entry = f"{datetime.utcnow()} | USER:{user} ({role}) | OUTCOME:{outcome} | QUERY:{query}\n"
    with open("mcp_audit.log", "a") as f:
        f.write(entry)
