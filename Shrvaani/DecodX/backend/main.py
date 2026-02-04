import sys
from pathlib import Path

# Corporate Pathing
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp.server.fastmcp import FastMCP
import backend.services.governance_service as gov_service
from backend.controllers.agent_controller import run_agent_reasoning

# Initialize FastMCP Server
mcp = FastMCP("Corporate Governance Server")

# --- Tools Mapping (Controllers/Services) ---

# TOOL: Validates user permissions for specific queries.
@mcp.tool()
def authorize_request(query: str, user_role: str):
    """Checks if a user has permission to execute a specific query."""
    return gov_service.authorize_request(query, user_role)

# TOOL: Retrieves facts from policies and financial records.
@mcp.tool()
def get_grounded_context(query: str, user_role: str):
    """Retrieves relevant financial and policy facts from the secure store."""
    return gov_service.get_grounded_context(query, user_role)

# TOOL: Fetches regional sales data for analysis.
@mcp.tool()
def get_financial_data(user_role: str):
    """Fetches full regional financial records if authorized."""
    return gov_service.get_financial_data(user_role)

# TOOL: Accesses the full text of corporate policies.
@mcp.tool()
def read_policy(policy_name: str):
    """Reads the full content of a corporate policy."""
    return gov_service.read_policy(policy_name)

# TOOL: Updates policy files (Admin only).
@mcp.tool()
def update_policy_document(policy_name: str, new_content: str, user_role: str):
    """Writes an updated version of a policy after Admin approval."""
    return gov_service.update_policy_document(policy_name, new_content, user_role)

# TOOL: Triggers the agentic reasoning graph.
@mcp.tool()
def execute_agent_reasoning(state_data: dict):
    """Executes the internal reasoning graph to synthesize a verified answer."""
    return run_agent_reasoning(state_data)

# TOOL: Logs interaction events for corporate auditing.
@mcp.tool()
def audit_event(event_type: str, user_id: str, user_role: str, query: str, details: str):
    """Logs a governance event for corporate auditing."""
    return gov_service.audit_event(event_type, user_id, user_role, query, details)

# TOOL: Performs external regulatory research.
@mcp.tool()
def research_compliance_standards(query: str):
    """Simulates a research agent checking external compliance regulations."""
    return gov_service.research_compliance_standards(query)

# TOOL: Detects contradictions in proposed changes.
@mcp.tool()
def identify_policy_hurdles(new_content: str):
    """Detects potential policy contradictions using cross-document intelligence."""
    return gov_service.identify_policy_hurdles(new_content)

if __name__ == "__main__":
    import os
    # Default to SSE for visibility and performance in the unified architecture
    transport = os.getenv("MCP_TRANSPORT", "sse")
    
    if transport == "sse":
        print("\n" + "="*50)
        print("🛡️  DecodX Governance Server is LIVE")
        print("🔗 Transport: SSE")
        print("📍 URL: http://localhost:8000/sse")
        print("="*50 + "\n")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
