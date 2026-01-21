from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tools-server")

#The tools decorator registers a function as a tool that can be called by clients. basically an api endpoint that triggers an action.
# ✅ Tool 1: calculator / this tool triggers the action of adding two numbers
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


# ✅ Tool 2: time tool / this tool triggers the action of getting the current time
@mcp.tool()
def get_current_time() -> str:
    """Returns the current time in ISO format."""
    return datetime.now().isoformat()


# ✅ Tool 3: simple compliance checker / this tool triggers the action of checking compliance
@mcp.tool()
def compliance_check(action: str) -> dict:
    """
    Demo governance tool:
    Checks if an action violates a simple policy.
    """
    blocked_words = ["password", "confidential", "leak"]

    lowered = action.lower()
    violations = [w for w in blocked_words if w in lowered]

    if violations:
        return {
            "allowed": False,
            "reason": f"Action contains risky keywords: {violations}",
            "suggestion": "Remove sensitive info and follow company policy."
        }

    return {
        "allowed": True,
        "reason": "No risky keywords detected.",
        "suggestion": "Proceed with standard precautions."
    }


if __name__ == "__main__":
    mcp.run()
