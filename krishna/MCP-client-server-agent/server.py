from fastmcp import FastMCP

mcp = FastMCP("Utility Server")

@mcp.tool()
def uppercase_text(text: str) -> str:
    """Convert text to uppercase."""
    return text.upper()

@mcp.tool()
def slugify_text(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    return "-".join(text.lower().split())

@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse a string."""
    return text[::-1]

@mcp.tool()
def word_count(text: str) -> int:
    """Count words in a string."""
    return len(text.split())

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
