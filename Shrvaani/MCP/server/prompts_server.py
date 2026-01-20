from mcp.server.fastmcp import FastMCP

mcp = FastMCP("prompts-server")


@mcp.prompt()
def summarize(text: str):
    return f"""
You are a sharp, structured assistant.

Summarize the following text in bullet points.
Extract key action items.

TEXT:
{text}
"""


@mcp.prompt()
def professional_email(draft: str):
    return f"""
Rewrite this email professionally.
Keep it short, polite, and corporate-ready.

DRAFT:
{draft}
"""


if __name__ == "__main__":
    # ✅ Force STDIO mode (prevents instant exit issues)
    mcp.run(transport="stdio")
