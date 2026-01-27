from pathlib import Path
import re
import hashlib
import fitz  # PyMuPDF


def extract_pdf_text(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def normalize_text(text: str) -> str:
    """
    Normalize text so formatting differences don't change hash.
    """
    t = (text or "").lower()
    t = re.sub(r"\s+", " ", t)        # collapse whitespace
    t = re.sub(r"[^a-z0-9@./ ]", "", t)  # keep useful chars
    return t.strip()


def text_hash_from_pdf(pdf_path: Path) -> str:
    raw_text = extract_pdf_text(pdf_path)
    clean_text = normalize_text(raw_text)
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()


files = [
    Path("/Users/alexander/Documents/resume.pdf"),
    Path("/Users/alexander/Documents/tinker/Resume_updated/Shrvaani S - AI_ML Python Developer - GEN AI - Product:Project Management - Data Science - Data Analysis.pdf"),
]

for f in files:
    print(f.name, text_hash_from_pdf(f))
