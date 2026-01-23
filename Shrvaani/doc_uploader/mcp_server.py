from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP
import fitz  # PyMuPDF

mcp = FastMCP("resume_uploader_server")


@mcp.tool()
def list_pdfs(root_path: str) -> List[str]:
    root = Path(root_path)
    if not root.exists():
        return []

    pdfs = []
    for p in root.rglob("*.pdf"):
        try:
            # skip hidden/system paths quickly
            if any(part.startswith(".") for part in p.parts):
                continue
            pdfs.append(str(p))
        except Exception:
            pass
    return pdfs


@mcp.tool()
def read_pdf_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return ""

    try:
        doc = fitz.open(str(path))
        chunks = []
        for page in doc:
            chunks.append(page.get_text("text"))
        doc.close()
        return "\n".join(chunks)
    except Exception:
        return ""


if __name__ == "__main__":
    mcp.run()
