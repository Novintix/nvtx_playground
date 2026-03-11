import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import tempfile
import os
import fitz  # PyMuPDF
from fpdf import FPDF
import io


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes."""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages = [page.get_text() for page in doc]
    return "\n\n".join(pages)


def extract_text_from_docx(docx_bytes: bytes) -> list[dict]:
    """
    Extract structured text from DOCX bytes.
    Returns a list of segments with type and text.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name

    try:
        doc = docx.Document(tmp_path)
        segments = []
        segment_id = 1
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # Determine segment type based on formatting
            style_name = para.style.name.lower() if para.style else ""
            
            if style_name.startswith('heading 1'):
                seg_type = "h1"
            elif style_name.startswith('heading 2'):
                seg_type = "h2"
            elif style_name.startswith('heading 3'):
                seg_type = "h3"
            elif para.runs and any(r.bold for r in para.runs if r.text.strip()):
                seg_type = "li"
            else:
                seg_type = "p"
            
            segments.append({
                "id": segment_id,
                "type": seg_type,
                "text": text
            })
            segment_id += 1
        
        return segments
    finally:
        os.unlink(tmp_path)


def extract_text_plain_from_docx(docx_bytes: bytes) -> str:
    """Extract plain text from Word document bytes."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name

    try:
        doc = docx.Document(tmp_path)
        paragraphs = [para.text for para in doc.paragraphs]
        return "\n\n".join(paragraphs)
    finally:
        os.unlink(tmp_path)


def create_translated_docx(translated_text: str, source_filename: str = "translated") -> bytes:
    """Generate a Word document from translated text. Returns DOCX as bytes."""
    doc = docx.Document()
    
    # Set normal style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Add paragraphs for each line of text
    for line in translated_text.split('\n'):
        doc.add_paragraph(line)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        doc.save(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            docx_bytes = f.read()
    finally:
        os.unlink(tmp_path)
    
    return docx_bytes


def create_frozen_template_pdf(
    original_file: bytes,
    segments: list[dict],
    target_lang: str,
    doc_title: str = "Translated Document",
    doc_ref: str = "DOC-001"
) -> bytes:
    """
    Create a PDF using the original DOCX as a frozen template,
    overlaying translated text on top of original positions.
    
    Args:
        original_file: Original DOCX file bytes
        segments: List of segments with original and translated text
        target_lang: Target language name
        doc_title: Document title
        doc_ref: Document reference number
    
    Returns:
        PDF file as bytes
    """
    # For now, create a simple PDF with translated text
    # In production, you'd use the original DOCX as a template
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=doc_title, ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Reference: {doc_ref} | Language: {target_lang}", ln=True, align="C")
    pdf.ln(10)
    
    # Add translated content
    pdf.set_font("Arial", size=11)
    for seg in segments:
        text = seg.get("translated_text", seg.get("text", ""))
        if not text:
            continue
        
        seg_type = seg.get("type", "p")
        
        # Apply formatting based on segment type
        if seg_type == "h1":
            pdf.set_font("Arial", "B", 16)
            pdf.ln(5)
        elif seg_type == "h2":
            pdf.set_font("Arial", "B", 14)
            pdf.ln(5)
        elif seg_type == "h3":
            pdf.set_font("Arial", "B", 12)
            pdf.ln(3)
        elif seg_type == "li":
            pdf.set_font("Arial", size=11)
            pdf.cell(10, 6, txt="• ", ln=False)
        else:
            pdf.set_font("Arial", size=11)
        
        # Multi-cell for wrapped text
        pdf.multi_cell(0, 6, text)
        pdf.ln(2)
    
    return pdf.output(dest="S").encode("latin-1")


# Backward compatibility aliases
extract_text_from_pdf = extract_text_from_pdf
create_translated_pdf = create_translated_docx
