from fastmcp import FastMCP

mcp = FastMCP("Utility Server")

@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for a city"""
    return f"Weather in {city} is sunny ☀️"

@mcp.tool()
def planner_prompt(task: str) -> str:
    """Create a step-by-step plan for a task"""
    return f"PLAN:\n1. Analyze\n2. Investigate\n3. Fix\nTask: {task}"

@mcp.tool()
def summary_prompt(text: str) -> str:
    """Summarize given text"""
    return f"SUMMARY: {text[:50]}..."

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
