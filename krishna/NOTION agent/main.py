"""
Notion MCP Server - FastMCP Implementation
A Model Context Protocol server that provides access to Notion API endpoints.
"""

from typing import Optional, Dict, Any, List
from fastmcp import FastMCP
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Notion API")

# Notion API Configuration
NOTION_BASE_URL = os.getenv("NOTION_BASE_URL", "https://api.notion.com")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2025-09-03")

class NotionClient:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        if not self.token:
            # We don't raise here to allow server start, but tools will fail
            self.headers = {}
            return

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }

    def request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.headers:
             return {"error": "NOTION_TOKEN environment variable is required"}

        url = f"{NOTION_BASE_URL}{endpoint}"

        # FastMCP tools are synchronous by default
        with httpx.Client(timeout=30.0) as client:
            try:
                if method.upper() == "GET":
                    response = client.get(url, headers=self.headers, params=params)
                elif method.upper() == "POST":
                    response = client.post(url, headers=self.headers, json=data, params=params)
                elif method.upper() == "PATCH":
                    response = client.patch(url, headers=self.headers, json=data, params=params)
                elif method.upper() == "DELETE":
                    response = client.delete(url, headers=self.headers, params=params)
                else:
                    return {"error": f"Method {method} not allowed"}

                if response.status_code >= 400:
                    try:
                        return {"error": response.json(), "status": response.status_code}
                    except:
                         return {"error": response.text, "status": response.status_code}

                return response.json()

            except httpx.RequestError as e:
                return {"error": f"Request failed: {str(e)}"}

def get_client() -> NotionClient:
    return NotionClient()

# Users API

@mcp.tool()
def get_user(user_id: str) -> Dict[str, Any]:
    """Retrieve partial information about a user. Returns a User, Bot, or Person object."""
    client = get_client()
    return client.request("GET", f"/v1/users/{user_id}")

@mcp.tool()
def get_users() -> Dict[str, Any]:
    """List all users in the workspace. Returns a list of User, Bot, or Person objects."""
    client = get_client()
    return client.request("GET", "/v1/users")

@mcp.tool()
def get_current_user() -> Dict[str, Any]:
    """Retrieve the bot user associated with the API token."""
    client = get_client()
    return client.request("GET", "/v1/users/me")

# Search API

@mcp.tool()
def search(
    query: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    sort: Optional[Dict[str, Any]] = None,
    start_cursor: Optional[str] = None,
    page_size: int = 100
) -> Dict[str, Any]:
    """
    Search Notion for pages or databases. 
    Use this tool to find the `page_id` or `database_id` (data_source_id) needed for other tools.
    """
    client = get_client()
    data = {k: v for k, v in locals().items() if v is not None and k != 'client'}
    return client.request("POST", "/v1/search", data)

# Blocks API

@mcp.tool()
def get_block_children(
    block_id: str,
    start_cursor: Optional[str] = None,
    page_size: int = 100
) -> Dict[str, Any]:
    """Retrieve the children blocks of a parent block. Use this to read page content."""
    client = get_client()
    params = {}
    if start_cursor:
        params["start_cursor"] = start_cursor
    if page_size:
        params["page_size"] = page_size
    
    return client.request("GET", f"/v1/blocks/{block_id}/children", params=params)

@mcp.tool()
def append_block_children(
    block_id: str,
    children: List[Dict[str, Any]],
    after: Optional[str] = None
) -> Dict[str, Any]:
    """Add new blocks (content) to the end of a parent block or page."""
    client = get_client()
    data = {"children": children}
    if after:
        data["after"] = after
    return client.request("PATCH", f"/v1/blocks/{block_id}/children", data)

@mcp.tool()
def get_block(block_id: str) -> Dict[str, Any]:
    """Retrieve a specific block object."""
    client = get_client()
    return client.request("GET", f"/v1/blocks/{block_id}")

@mcp.tool()
def update_block(block_id: str, block: Dict[str, Any]) -> Dict[str, Any]:
    """Update a block's content or state (e.g. text, archived status)."""
    client = get_client()
    return client.request("PATCH", f"/v1/blocks/{block_id}", block)

@mcp.tool()
def delete_block(block_id: str) -> Dict[str, Any]:
    """Delete (archive) a block."""
    client = get_client()
    return client.request("DELETE", f"/v1/blocks/{block_id}")

# Pages API

@mcp.tool()
def get_page(page_id: str) -> Dict[str, Any]:
    """Retrieve a page's metadata and properties (but not its main content/blocks)."""
    client = get_client()
    return client.request("GET", f"/v1/pages/{page_id}")

@mcp.tool()
def create_page(
    parent: Dict[str, Any],
    properties: Dict[str, Any],
    children: Optional[List[Dict[str, Any]]] = None,
    icon: Optional[Dict[str, Any]] = None,
    cover: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new page in a database or as a child of another page."""
    client = get_client()
    data = {k: v for k, v in locals().items() if v is not None and k != 'client'}
    return client.request("POST", "/v1/pages", data)

@mcp.tool()
def update_page(
    page_id: str,
    properties: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
    in_trash: Optional[bool] = None,
    icon: Optional[Dict[str, Any]] = None,
    cover: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update a page's properties, icon, cover, or archive status."""
    client = get_client()
    data = {k: v for k, v in locals().items() if v is not None and k not in ['client', 'page_id']}
    return client.request("PATCH", f"/v1/pages/{page_id}", data)

@mcp.tool()
def get_page_property(
    page_id: str,
    property_id: str,
    start_cursor: Optional[str] = None,
    page_size: int = 100
) -> Dict[str, Any]:
    """Retrieve a specific property item from a page."""
    client = get_client()
    params = {}
    if start_cursor:
        params["start_cursor"] = start_cursor
    if page_size:
        params["page_size"] = page_size
    
    return client.request("GET", f"/v1/pages/{page_id}/properties/{property_id}", params=params)

@mcp.tool()
def move_page(page_id: str, parent: Dict[str, Any]) -> Dict[str, Any]:
    """Move a page to a new parent page or database."""
    client = get_client()
    return client.request("POST", f"/v1/pages/{page_id}/move", {"parent": parent})

# Comments API

@mcp.tool()
def get_comments(
    block_id: str,
    start_cursor: Optional[str] = None,
    page_size: int = 100
) -> Dict[str, Any]:
    """Retrieve comments from a page or block."""
    client = get_client()
    params = {"block_id": block_id}
    if start_cursor:
        params["start_cursor"] = start_cursor
    if page_size:
        params["page_size"] = page_size
    return client.request("GET", "/v1/comments", params=params)

@mcp.tool()
def create_comment(
    parent: Dict[str, Any],
    rich_text: List[Dict[str, Any]],
    discussion_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a comment to a page or existing discussion."""
    client = get_client()
    data = {k: v for k, v in locals().items() if v is not None and k != 'client'}
    return client.request("POST", "/v1/comments", data)

# Data Sources API (Databases)

@mcp.tool()
def create_data_source(
    parent: Dict[str, Any],
    properties: Dict[str, Any],
    title: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create a new data source (database) with properties."""
    client = get_client()
    data = {k: v for k, v in locals().items() if v is not None and k != 'client'}
    return client.request("POST", "/v1/data_sources", data)

@mcp.tool()
def query_data_source(
    data_source_id: str,
    filter: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    start_cursor: Optional[str] = None,
    page_size: int = 100
) -> Dict[str, Any]:
    """
    Query a data source (database) to find specific pages within it.
    Returns a list of pages with their properties and IDs.
    """
    client = get_client()
    data = {k: v for k, v in locals().items() if v is not None and k not in ['client', 'data_source_id']}
    return client.request("POST", f"/v1/data_sources/{data_source_id}/query", data)

@mcp.tool()
def get_data_source(data_source_id: str) -> Dict[str, Any]:
    """Retrieve data source (database) metadata and properties."""
    client = get_client()
    return client.request("GET", f"/v1/data_sources/{data_source_id}")

@mcp.tool()
def update_data_source(
    data_source_id: str,
    properties: Optional[Dict[str, Any]] = None,
    title: Optional[List[Dict[str, Any]]] = None,
    description: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update a data source (database) name, description, or properties."""
    client = get_client()
    data = {k: v for k, v in locals().items() if v is not None and k not in ['client', 'data_source_id']}
    return client.request("PATCH", f"/v1/data_sources/{data_source_id}", data)

@mcp.tool()
def get_data_source_templates(data_source_id: str) -> Dict[str, Any]:
    """Retrieve templates available for a database."""
    client = get_client()
    return client.request("GET", f"/v1/data_sources/{data_source_id}/templates")

if __name__ == "__main__":
    mcp.run(transport="http", port=8001)
