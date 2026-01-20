import subprocess
from pathlib import Path
from typing import List
from pypdf import PdfReader


from mcp.server.fastmcp import FastMCP

mcp = FastMCP("local-agent-server")

# ✅ Allowed roots (server-side safety boundary)
ALLOWED_ROOTS = [
    Path.home() / "Music",
    Path.home() / "Documents",
]


def is_allowed_path(p: Path) -> bool:
    p = p.resolve()
    return any(str(p).startswith(str(root.resolve())) for root in ALLOWED_ROOTS)


@mcp.tool()
def list_files(folder: str, extensions: List[str] = None) -> List[str]:
    """
    List files in a folder (optionally filter by extension).
    """
    folder_path = Path(folder).expanduser()

    if not folder_path.exists():
        return [f"❌ Folder not found: {folder_path}"]

    if not is_allowed_path(folder_path):
        return [f"❌ Access denied. Folder outside allowed roots: {folder_path}"]

    results = []
    for item in folder_path.iterdir():
        if item.is_file():
            if extensions:
                if item.suffix.lower() in [e.lower() for e in extensions]:
                    results.append(str(item))
            else:
                results.append(str(item))

    return results


@mcp.tool()
def search_files(folder: str, query: str) -> List[str]:
    """
    Search for files containing query in name inside a folder.
    """
    folder_path = Path(folder).expanduser()

    if not folder_path.exists():
        return [f"❌ Folder not found: {folder_path}"]

    if not is_allowed_path(folder_path):
        return [f"❌ Access denied. Folder outside allowed roots: {folder_path}"]

    query_lower = query.lower()
    matches = []

    for item in folder_path.rglob("*"):
        if item.is_file() and query_lower in item.name.lower():
            matches.append(str(item))

    return matches[:50]


@mcp.tool()
def read_pdf_text(path: str) -> str:
    """
    Extract text from a PDF file safely.
    """
    file_path = Path(path).expanduser()

    if not file_path.exists():
        return f"❌ File not found: {file_path}"

    if not is_allowed_path(file_path):
        return f"❌ Access denied. File outside allowed roots: {file_path}"

    if file_path.suffix.lower() != ".pdf":
        return f"❌ Not a PDF file: {file_path.suffix}"

    try:
        reader = PdfReader(str(file_path))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"❌ Failed to read PDF: {e}"


# ⚠️ NOTE:
# We are intentionally NOT using play_audio via MCP stdio,
# because it can close the stdio session unexpectedly on macOS.
# We'll play on the CLIENT side instead.


if __name__ == "__main__":
    mcp.run()
