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

#this tool lists files in a given folder, with optional filtering by file extensions
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

#this tool searches for files in a given folder matching a query in their names
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

# This tool reads text from a PDF file safely
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
    
# This tool reads text-like files (txt, md, json, csv) safely
@mcp.tool()
def read_text_file(path: str) -> str:
    """
    Read a text-like file safely (txt, md, json, csv).
    """
    file_path = Path(path).expanduser()

    if not file_path.exists():
        return f"❌ File not found: {file_path}"

    if not is_allowed_path(file_path):
        return f"❌ Access denied. File outside allowed roots: {file_path}"

    allowed_ext = {".txt", ".md", ".json", ".csv"}
    if file_path.suffix.lower() not in allowed_ext:
        return f"❌ Not a readable text file type: {file_path.suffix}"

    return file_path.read_text(encoding="utf-8", errors="ignore")

if __name__ == "__main__":
    mcp.run()
