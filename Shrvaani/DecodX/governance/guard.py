import datetime
from typing import Optional

print("🛡️  MCP Guard Module Loaded Successfully")

# Tool-level Access Control Matrix
TOOL_PERMISSIONS = {
    "Guest": ["policy_only"],
    "Analyst": ["policy_only", "analyze_performance", "compare_history", "validate_policy"],
    "Admin": ["*"]  # All tools
}

# Credential Validation
def validate_credentials(user_id: str, user_role: str) -> bool:
    """Mock validation. Replace with IAM/OAuth in production."""
    valid_roles = ["Guest", "Analyst", "Admin"]
    return user_role in valid_roles

# Query-Level Authorization (Entry Point)
def authorize(query: str, user_role: str = "Guest", tool_name: str = None) -> bool:
    """
    MCP Entry Point: Validate if the user can perform this query.
    Returns True if authorized, False otherwise.
    """
    # 1. Validate Credentials
    if not validate_credentials("mock_user", user_role):
        return False
    
    # 2. Check Query-Level Restrictions
    blocked_keywords = ["approve", "execute", "delete", "modify"]
    
    # Guest Restrictions
    if user_role == "Guest":
        if any(word in query.lower() for word in blocked_keywords):
            return False
        
        if "override" in query.lower() or "exception" in query.lower():
            return False
    
    # 3. Tool-Level Authorization (if tool_name provided)
    if tool_name:
        return authorize_tool(tool_name, user_role)
    
    return True

# Tool-Level Authorization
def authorize_tool(tool_name: str, user_role: str) -> bool:
    """
    Check if the user role has permission to use the specified tool.
    """
    allowed_tools = TOOL_PERMISSIONS.get(user_role, [])
    
    # Admin has access to all tools
    if "*" in allowed_tools:
        return True
    
    return tool_name in allowed_tools

# Audit Logging Functions
def audit_log(query: str, user: str = "unknown", role: str = "Guest", outcome: str = "Allowed"):
    """Entry Point Audit: Log all incoming requests."""
    timestamp = datetime.datetime.now().isoformat()
    with open("mcp_audit.log", "a") as log:
        log.write(f"[ENTRY] {timestamp} | USER:{user} | ROLE:{role} | QUERY:{query[:100]} | OUTCOME:{outcome}\n")

def log_request_approval(query: str, user: str, role: str, approved: bool, reason: str = ""):
    """Approval Decision Audit: Log whether request was approved."""
    timestamp = datetime.datetime.now().isoformat()
    decision = "Approved" if approved else "Rejected"
    with open("mcp_audit.log", "a") as log:
        log.write(f"[APPROVAL] {timestamp} | USER:{user} | ROLE:{role} | DECISION:{decision} | REASON:{reason}\n")

def audit_exit(query: str, user: str, role: str, status: str, response_summary: str = ""):
    """
    Exit Point Audit: Log the final outcome and response.
    
    Args:
        status: "Success", "Blocked", "Error"
        response_summary: Brief summary or length of response
    """
    timestamp = datetime.datetime.now().isoformat()
    with open("mcp_audit.log", "a") as log:
        log.write(f"[EXIT] {timestamp} | USER:{user} | ROLE:{role} | STATUS:{status} | RESPONSE:{response_summary}\n")
        log.write("-" * 100 + "\n")  # Separator for readability
