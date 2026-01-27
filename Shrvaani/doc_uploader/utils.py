import csv
import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from helpers import (
    ALLOWED_PARENT_FOLDERS,
    CONTACT_SIGNALS,
    HR_FOLDER,
    HR_KEYWORDS,
    NON_RESUME_FILENAME_HINTS,
    REGISTRY_PATH,
    RESUME_SECTIONS,
    TECH_FOLDER,
    TECH_KEYWORDS,
)


# ----------------------------
# Storage
# ----------------------------
def ensure_storage_folders():
    TECH_FOLDER.mkdir(parents=True, exist_ok=True)
    HR_FOLDER.mkdir(parents=True, exist_ok=True)


# ----------------------------
# Hashing
# ----------------------------
def file_bytes_hash(file_path: Path) -> str:
    """
    Strong duplicate check for exact same file (bytes match).
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_text_for_hash(text: str) -> str:
    """
    Normalize resume text so formatting changes don't break dedupe.
    - lowercased
    - collapse spaces
    - remove punctuation-ish noise
    """
    t = (text or "").lower()
    t = re.sub(r"\s+", " ", t)
    t = t.replace("\u00a0", " ")  # non-breaking space
    t = t.strip()
    return t


def text_content_hash(text: str) -> str:
    """
    Strong duplicate check for same resume content (even if PDF layout differs).
    """
    norm = normalize_text_for_hash(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


# ----------------------------
# Email extraction (identity signal)
# ----------------------------
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

def extract_primary_email(text: str) -> Optional[str]:
    matches = EMAIL_REGEX.findall(text or "")
    if not matches:
        return None
    # first email is good enough as "primary"
    return matches[0].lower().strip()


# ----------------------------
# Registry (CSV)
# ----------------------------
REGISTRY_FIELDS = [
    "file_hash",
    "text_hash",
    "email",
    "file_path",
    "category",
    "target_folder",
    "status",
]

def load_registry() -> Dict[str, dict]:
    """
    Returns dict indexed by file_hash.
    Also contains text_hash/email in each row.
    """
    registry: Dict[str, dict] = {}

    if not REGISTRY_PATH.exists():
        return registry

    with open(REGISTRY_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fh = (row.get("file_hash") or "").strip()
            if fh:
                registry[fh] = row
    return registry


def registry_seen_text_hashes(registry: Dict[str, dict]) -> set[str]:
    s = set()
    for row in registry.values():
        th = (row.get("text_hash") or "").strip()
        if th:
            s.add(th)
    return s


def registry_seen_emails(registry: Dict[str, dict]) -> set[str]:
    s = set()
    for row in registry.values():
        em = (row.get("email") or "").strip().lower()
        if em:
            s.add(em)
    return s


def update_registry(row: dict):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    file_exists = REGISTRY_PATH.exists()

    with open(REGISTRY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ----------------------------
# Filtering / Scan rules
# ----------------------------
def looks_like_non_resume_by_filename(file_path: Path) -> bool:
    name = file_path.name.lower()
    return any(hint in name for hint in NON_RESUME_FILENAME_HINTS)


def is_in_allowed_parent_folder(file_path: Path) -> bool:
    parts = [p.lower() for p in file_path.parts]
    for folder in parts:
        for allowed in ALLOWED_PARENT_FOLDERS:
            if allowed in folder:
                return True
    return False


def list_candidate_pdfs(root_path: Path) -> List[Path]:
    """
    Fallback local scanner (NOT used once MCP list_pdfs is working),
    but kept as backup utility.
    """
    pdfs = []
    for dirpath, _, filenames in os.walk(root_path):
        for fn in filenames:
            if fn.lower().endswith(".pdf"):
                full_path = Path(dirpath) / fn
                if is_in_allowed_parent_folder(full_path):
                    pdfs.append(full_path)
    return pdfs


# ----------------------------
# Resume detection + classification
# ----------------------------
def is_probably_resume(text: str) -> Tuple[bool, str]:
    t = (text or "").lower()

    # must contain at least 2 sections
    section_hits = sum(1 for s in RESUME_SECTIONS if s in t)

    # must contain at least 1 contact signal
    contact_hits = sum(1 for c in CONTACT_SIGNALS if c in t)

    if section_hits < 2:
        return False, "Not a resume (missing key resume sections)."

    if contact_hits < 1:
        return False, "Not a resume (missing contact signals)."

    return True, "Resume structure detected."


def classify_resume(text: str):
    t = (text or "").lower()

    tech_hits = sum(1 for kw in TECH_KEYWORDS if kw in t)
    hr_hits = sum(1 for kw in HR_KEYWORDS if kw in t)

    if hr_hits > tech_hits:
        return "HR", 0.8, "Detected HR keywords."
    return "TECHNICAL", 0.85, "Detected technical keywords."


# ----------------------------
# Move / copy
# ----------------------------
def safe_move_to_folder(file_path: Path, target_folder: Path) -> Path:
    target_folder.mkdir(parents=True, exist_ok=True)

    dest = target_folder / file_path.name

    # handle duplicate filenames
    if dest.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        i = 1
        while True:
            candidate = target_folder / f"{stem}_{i}{suffix}"
            if not candidate.exists():
                dest = candidate
                break
            i += 1

    shutil.copy2(str(file_path), str(dest))
    return dest