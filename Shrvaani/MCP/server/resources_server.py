from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resources-server")

# Resources are used for serving fetchable data to clients. It reads the data and returns it when requested.

# ✅ Resource 1: simple text resource / this resource provides an introductory document about MCP, while the user query is mentioned as "retrieve the intro doc", the details will be returned as the response.
@mcp.resource("docs://mcp/intro")
def intro_doc():
    return """
MCP (Model Context Protocol) is a standard protocol that lets AI clients connect to AI servers.

Servers can expose:
1) Prompts (templates)
2) Resources (fetchable data)
3) Tools (executable functions)
"""


# ✅ Resource 2: policy resource example / this resource provides a demo company security policy, while the user query is mentioned as "retrieve the company security policy", the details will be returned as the response.
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
