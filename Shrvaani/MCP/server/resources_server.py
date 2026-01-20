from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resources-server")


# ✅ Resource 1: simple text resource
@mcp.resource("docs://mcp/intro")
def intro_doc():
    return """
MCP (Model Context Protocol) is a standard protocol that lets AI clients connect to AI servers.

Servers can expose:
1) Prompts (templates)
2) Resources (fetchable data)
3) Tools (executable functions)
"""


# ✅ Resource 2: policy resource example
@mcp.resource("policy://company/security")
def company_security_policy():
    return """
Company Security Policy (Demo):
- Do not share passwords.
- Do not upload confidential files to public services.
- Use MFA on all accounts.
"""


if __name__ == "__main__":
    mcp.run()
