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
    """
    Uses MCP tool: list_pdfs(root_path)
    Then filters them by allowed parent folders (resume/cv/etc)
    """
    root_path = state["root_path"]
    session = state["mcp_session"]

    # ✅ MCP call (MUST await)
    resp = await session.call_tool("list_pdfs", {"root_path": root_path})

    files = []
    for c in getattr(resp, "content", []):
        fp = getattr(c, "text", None)
        if fp:
            files.append(fp)

    filtered = []
    for fp in files:
        p = Path(fp)
        if is_in_allowed_parent_folder(p):
            filtered.append(str(p))

    return {
        **state,
        "pdf_files": filtered,
        "results": [],
        "skipped": [],
    }


async def node_process_files(state: ResumeState) -> ResumeState:
    """
    Uses MCP tool: read_pdf_text(file_path)
    Dedupe using:
      - file bytes hash
      - extracted text hash
      - email identity
    """
    ensure_storage_folders()
    session = state["mcp_session"]

    registry = load_registry()

    seen_file_hashes = set(registry.keys())
    seen_text_hashes = registry_seen_text_hashes(registry)
    seen_emails = registry_seen_emails(registry)

    # also avoid duplicates inside same run
    run_file_hashes = set()
    run_text_hashes = set()
    run_emails = set()

    for fp in state.get("pdf_files", []):
        file_path = Path(fp)

        try:
            # reject by filename
            if looks_like_non_resume_by_filename(file_path):
                state["skipped"].append((str(file_path), "Filename looks like non-resume document."))
                continue

            # file hash
            fhash = file_bytes_hash(file_path)
            if fhash in seen_file_hashes or fhash in run_file_hashes:
                state["skipped"].append((str(file_path), "Duplicate (same file bytes)."))
                continue

            # ✅ MCP read (MUST await)
            resp = await session.call_tool("read_pdf_text", {"file_path": str(file_path)})

            extracted_text = ""
            for c in getattr(resp, "content", []):
                t = getattr(c, "text", None)
                if t:
                    extracted_text += t + "\n"

            extracted_text = extracted_text.strip()

            if not extracted_text:
                state["skipped"].append((str(file_path), "Empty PDF text (scanned image PDF / no text)."))
                continue

            # resume heuristic
            ok, reason_resume = is_probably_resume(extracted_text)
            if not ok:
                state["skipped"].append((str(file_path), reason_resume))
                continue

            # text hash dedupe
            thash = text_content_hash(extracted_text)
            if thash in seen_text_hashes or thash in run_text_hashes:
                state["skipped"].append((str(file_path), "Duplicate (same content)."))
                continue

            # email dedupe
            email = extract_primary_email(extracted_text)
            if email:
                if email in seen_emails or email in run_emails:
                    state["skipped"].append((str(file_path), f"Duplicate (same email: {email})."))
                    continue

            # classify
            category, confidence, reason_class = classify_resume(extracted_text)

            target_folder = HR_FOLDER if category == "HR" else TECH_FOLDER
            moved_path = safe_move_to_folder(file_path, target_folder)

            result = {
                "file": str(file_path),
                "moved_to": str(moved_path),
                "category": category,
                "confidence": confidence,
                "reason": reason_class,
                "target_folder": str(target_folder),
                "file_hash": fhash,
                "text_hash": thash,
                "email": email or "",
            }

            state["results"].append(result)

            # update run dedupe memory
            run_file_hashes.add(fhash)
            run_text_hashes.add(thash)
            if email:
                run_emails.add(email)

            update_registry(
                {
                    "file_hash": fhash,
                    "text_hash": thash,
                    "email": email or "",
                    "file_path": str(moved_path),
                    "category": category,
                    "target_folder": str(target_folder),
                    "status": "ROUTED",
                }
            )

        except Exception as e:
            state["skipped"].append((str(file_path), f"Error processing file: {e}"))

    return state


def build_graph():
    g = StateGraph(ResumeState)

    g.add_node("scan_files", node_scan_files)
    g.add_node("process_files", node_process_files)

    g.set_entry_point("scan_files")
    g.add_edge("scan_files", "process_files")

    return g.compile()