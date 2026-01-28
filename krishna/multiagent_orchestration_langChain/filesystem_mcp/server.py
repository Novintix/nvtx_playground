from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

mcp = FastMCP("filesystem")


def _get_root() -> Path:
    root = os.getenv("FILES_ROOT", os.getcwd())
    return Path(root).resolve()


def _resolve_path(path: str) -> Path:
    root = _get_root()
    target = (root / path).resolve()
    if root not in target.parents and target != root:
        raise ValueError("Path escapes root directory")
    return target


def _file_info(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "name": path.name,
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
        "size": stat.st_size,
        "modified": stat.st_mtime,
    }


@mcp.tool()
def fs_root() -> dict[str, str]:
    """Return the configured root directory path."""
    return {"root": str(_get_root())}


@mcp.tool()
def fs_exists(path: str) -> dict[str, bool]:
    """Check if a path exists within the root directory."""
    return {"exists": _resolve_path(path).exists()}


@mcp.tool()
def fs_list(path: str = ".") -> dict[str, Any]:
    """List files and directories in the specified path."""
    target = _resolve_path(path)
    if not target.exists():
        raise FileNotFoundError("Path not found")
    if not target.is_dir():
        raise NotADirectoryError("Path is not a directory")
    items = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    return {
        "path": str(target),
        "items": [_file_info(p) for p in items],
    }


@mcp.tool()
def fs_read_text(path: str, encoding: str = "utf-8") -> dict[str, Any]:
    """Read the contents of a text file."""
    target = _resolve_path(path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("File not found")
    return {"path": str(target), "content": target.read_text(encoding=encoding)}


@mcp.tool()
def fs_write_text(path: str, content: str, encoding: str = "utf-8", overwrite: bool = True) -> dict[str, Any]:
    """Write text content to a file."""
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        raise FileExistsError("File already exists")
    target.write_text(content, encoding=encoding)
    return {"path": str(target), "bytes": target.stat().st_size}


@mcp.tool()
def fs_append_text(path: str, content: str, encoding: str = "utf-8") -> dict[str, Any]:
    """Append text content to an existing file."""
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding=encoding) as handle:
        handle.write(content)
    return {"path": str(target), "bytes": target.stat().st_size}


@mcp.tool()
def fs_delete(path: str, recursive: bool = False) -> dict[str, Any]:
    """Delete a file or directory."""
    target = _resolve_path(path)
    if not target.exists():
        raise FileNotFoundError("Path not found")
    if target.is_dir():
        if recursive:
            for item in sorted(target.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                if item.is_dir():
                    item.rmdir()
                else:
                    item.unlink()
            target.rmdir()
        else:
            target.rmdir()
    else:
        target.unlink()
    return {"deleted": True, "path": str(target)}


@mcp.tool()
def fs_mkdir(path: str, parents: bool = True, exist_ok: bool = True) -> dict[str, Any]:
    """Create a new directory."""
    target = _resolve_path(path)
    target.mkdir(parents=parents, exist_ok=exist_ok)
    return {"path": str(target)}


@mcp.tool()
def fs_stat(path: str) -> dict[str, Any]:
    """Get metadata information about a file or directory."""
    target = _resolve_path(path)
    if not target.exists():
        raise FileNotFoundError("Path not found")
    return _file_info(target)


@mcp.tool()
def fs_pwd() -> dict[str, str]:
    """Get the current working directory path."""
    root = _get_root()
    return {
        "current_location": str(root),
        "description": "This is your filesystem root. All operations are relative to this location."
    }


@mcp.tool()
def fs_move(source: str, destination: str) -> dict[str, Any]:
    """Move or rename a file or directory to a new location."""
    src = _resolve_path(source)
    dst = _resolve_path(destination)
    
    if not src.exists():
        raise FileNotFoundError(f"Source path not found: {source}")
    
    if dst.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    
    return {
        "moved": True,
        "from": str(src),
        "to": str(dst)
    }


@mcp.tool()
def fs_copy(source: str, destination: str, overwrite: bool = False) -> dict[str, Any]:
    """Copy a file to a new location."""
    import shutil
    
    src = _resolve_path(source)
    dst = _resolve_path(destination)
    
    if not src.exists():
        raise FileNotFoundError(f"Source path not found: {source}")
    
    if not src.is_file():
        raise IsADirectoryError("Can only copy files, not directories")
    
    if dst.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists: {destination}")
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    
    return {
        "copied": True,
        "from": str(src),
        "to": str(dst),
        "size": dst.stat().st_size
    }


@mcp.tool()
def fs_search(pattern: str, path: str = ".", case_sensitive: bool = False) -> dict[str, Any]:
    """Search for files and directories matching a pattern using wildcards."""
    target = _resolve_path(path)
    
    if not target.exists():
        raise FileNotFoundError("Path not found")
    
    if not target.is_dir():
        raise NotADirectoryError("Path is not a directory")
    
    if case_sensitive:
        matches = list(target.rglob(pattern))
    else:
        # Case-insensitive search
        matches = []
        for item in target.rglob("*"):
            if item.match(pattern) or item.name.lower() == pattern.lower():
                matches.append(item)
    
    return {
        "pattern": pattern,
        "search_path": str(target),
        "matches": [_file_info(p) for p in matches[:100]],  # Limit to 100 results
        "total_matches": len(matches)
    }


@mcp.tool()
def fs_find_by_extension(extension: str, path: str = ".") -> dict[str, Any]:
    """Find all files with a specific file extension."""
    target = _resolve_path(path)
    
    if not target.exists():
        raise FileNotFoundError("Path not found")
    
    if not target.is_dir():
        raise NotADirectoryError("Path is not a directory")
    
    # Ensure extension starts with a dot
    if not extension.startswith("."):
        extension = f".{extension}"
    
    matches = [p for p in target.rglob(f"*{extension}") if p.is_file()]
    
    return {
        "extension": extension,
        "search_path": str(target),
        "files": [_file_info(p) for p in matches[:100]],  # Limit to 100 results
        "total_files": len(matches)
    }


@mcp.tool()
def fs_tree(path: str = ".", max_depth: int = 3) -> dict[str, Any]:
    """Display a directory tree structure with nested files and folders."""
    target = _resolve_path(path)
    
    if not target.exists():
        raise FileNotFoundError("Path not found")
    
    if not target.is_dir():
        raise NotADirectoryError("Path is not a directory")
    
    def build_tree(current_path: Path, current_depth: int = 0) -> list[dict]:
        if current_depth >= max_depth:
            return []
        
        items = []
        try:
            for item in sorted(current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                info = {
                    "name": item.name,
                    "path": str(item.relative_to(target)),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                }
                
                if item.is_dir():
                    info["children"] = build_tree(item, current_depth + 1)
                
                items.append(info)
        except PermissionError:
            pass
        
        return items
    
    tree = build_tree(target)
    
    return {
        "root": str(target),
        "max_depth": max_depth,
        "tree": tree
    }


@mcp.tool()
def fs_get_directory_size(path: str = ".") -> dict[str, Any]:
    """Calculate the total size and contents of a directory."""
    target = _resolve_path(path)
    
    if not target.exists():
        raise FileNotFoundError("Path not found")
    
    if target.is_file():
        return {
            "path": str(target),
            "is_file": True,
            "size_bytes": target.stat().st_size,
            "size_mb": round(target.stat().st_size / (1024 * 1024), 2)
        }
    
    total_size = 0
    file_count = 0
    dir_count = 0
    
    for item in target.rglob("*"):
        if item.is_file():
            total_size += item.stat().st_size
            file_count += 1
        elif item.is_dir():
            dir_count += 1
    
    return {
        "path": str(target),
        "is_dir": True,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_size_gb": round(total_size / (1024 * 1024 * 1024), 3),
        "file_count": file_count,
        "directory_count": dir_count
    }


@mcp.tool()
def fs_read_binary(path: str) -> dict[str, Any]:
    """Read a binary file and return its content as base64 encoded data."""
    import base64
    
    target = _resolve_path(path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("File not found")
    
    content = target.read_bytes()
    encoded = base64.b64encode(content).decode('utf-8')
    
    return {
        "path": str(target),
        "size_bytes": len(content),
        "content_base64": encoded
    }


@mcp.tool()
def fs_write_binary(path: str, content_base64: str, overwrite: bool = True) -> dict[str, Any]:
    """Write binary data from base64 encoded content to a file."""
    import base64
    
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    
    if target.exists() and not overwrite:
        raise FileExistsError("File already exists")
    
    content = base64.b64decode(content_base64)
    target.write_bytes(content)
    
    return {
        "path": str(target),
        "bytes": target.stat().st_size
    }


if __name__ == "__main__":
    mcp.run(transport="http", port=8002)