from typing import TypedDict, List, Any
from pathlib import Path

from langgraph.graph import StateGraph

from utils import (
    classify_resume,
    ensure_storage_folders,
    extract_primary_email,
    file_bytes_hash,
    is_in_allowed_parent_folder,
    is_probably_resume,
    load_registry,
    looks_like_non_resume_by_filename,
    registry_seen_emails,
    registry_seen_text_hashes,
    safe_move_to_folder,
    text_content_hash,
    update_registry,
)

from helpers import TECH_FOLDER, HR_FOLDER


class ResumeState(TypedDict, total=False):
    root_path: str
    pdf_files: List[str]
    results: list
    skipped: list
    mcp_session: Any


async def node_scan_files(state: ResumeState) -> ResumeState:
    root_path = state["root_path"]
    session = state["mcp_session"]

    resp = await session.call_tool("list_pdfs", {"root_path": root_path})

    files = []
    for c in getattr(resp, "content", []):
        if getattr(c, "text", None):
            files.append(c.text)

    filtered = []
    for fp in files:
        if is_in_allowed_parent_folder(Path(fp)):
            filtered.append(fp)

    return {
        **state,
        "pdf_files": filtered,
        "results": [],
        "skipped": [],
    }


async def node_process_files(state: ResumeState) -> ResumeState:
    ensure_storage_folders()
    session = state["mcp_session"]

    registry = load_registry()
    seen_file_hashes = set(registry.keys())
    seen_text_hashes = registry_seen_text_hashes(registry)
    seen_emails = registry_seen_emails(registry)

    run_file_hashes = set()
    run_text_hashes = set()
    run_emails = set()

    for fp in state.get("pdf_files", []):
        file_path = Path(fp)

        try:
            if looks_like_non_resume_by_filename(file_path):
                state["skipped"].append((fp, "Filename looks like non-resume"))
                continue

            fhash = file_bytes_hash(file_path)
            if fhash in seen_file_hashes or fhash in run_file_hashes:
                state["skipped"].append((fp, "Duplicate (file hash)"))
                continue

            resp = await session.call_tool(
                "read_pdf_text", {"file_path": str(file_path)}
            )

            text = "".join(
                c.text for c in getattr(resp, "content", []) if getattr(c, "text", None)
            ).strip()

            if not text:
                state["skipped"].append((fp, "Empty / scanned PDF"))
                continue

            ok, reason = is_probably_resume(text)
            if not ok:
                state["skipped"].append((fp, reason))
                continue

            thash = text_content_hash(text)
            if thash in seen_text_hashes or thash in run_text_hashes:
                state["skipped"].append((fp, "Duplicate (content hash)"))
                continue

            email = extract_primary_email(text)
            if email and (email in seen_emails or email in run_emails):
                state["skipped"].append((fp, f"Duplicate (email {email})"))
                continue

            category, confidence, reason_cls = classify_resume(text)
            target = HR_FOLDER if category == "HR" else TECH_FOLDER

            moved = safe_move_to_folder(file_path, target)

            state["results"].append({
                "file": fp,
                "moved_to": str(moved),
                "category": category,
                "confidence": confidence,
                "reason": reason_cls,
            })

            run_file_hashes.add(fhash)
            run_text_hashes.add(thash)
            if email:
                run_emails.add(email)

            update_registry({
                "file_hash": fhash,
                "text_hash": thash,
                "email": email or "",
                "file_path": str(moved),
                "category": category,
                "target_folder": str(target),
                "status": "ROUTED",
            })

        except Exception as e:
            state["skipped"].append((fp, str(e)))

    # ✅ IMPORTANT: return state explicitly
    return {
        **state,
        "results": state["results"],
        "skipped": state["skipped"],
    }


def build_graph():
    g = StateGraph(ResumeState)

    g.add_node("scan_files", node_scan_files)
    g.add_node("process_files", node_process_files)

    g.set_entry_point("scan_files")
    g.add_edge("scan_files", "process_files")

    return g.compile()
