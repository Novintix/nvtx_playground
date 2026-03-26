import docx
from docx.shared import Pt
import tempfile
import os
import fitz  # PyMuPDF
import io
import re


# Multilingual PDF generation function
def create_multilingual_pdf(
    original_segments: list[dict],
    translations: list[dict],
    doc_title: str = "IFU Document",
    doc_ref: str = "IFU-001"
) -> bytes:
    """
    Generate a multilingual PDF with English content and all target language translations.
    Creates a contents page after the deputy synthesis page listing all languages and their starting page numbers.
    """
    import fitz
    
    page_width = 595
    page_height = 842
    margin_left = 50
    margin_right = 50
    margin_top = 60
    content_width = page_width - margin_left - margin_right
    
    doc = fitz.open()
    
    color_black = (0, 0, 0)
    color_dark_blue = (0.1, 0.2, 0.4)
    color_gray = (0.5, 0.5, 0.5)
    
    def wrap_text(text, max_width, fontsize):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            estimated_width = len(test_line) * fontsize * 0.4
            if estimated_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines if lines else [""]
    
    def add_new_page():
        return doc.new_page(width=page_width, height=page_height)
    
    def check_new_page(y_pos, required_height):
        if y_pos + required_height > page_height - 50:
            return add_new_page(), margin_top
        return None, y_pos
    
    def insert_text_func(page, x, y, text, fontsize, color, max_width=None):
        if max_width:
            lines = wrap_text(text, max_width, fontsize)
            for line in lines:
                page.insert_text(fitz.Point(x, y), line, fontsize=fontsize, color=color)
                y += fontsize * 1.4
            return y
        else:
            page.insert_text(fitz.Point(x, y), text, fontsize=fontsize, color=color)
            return y + fontsize * 1.4
    
    # Cover Page
    page = add_new_page()
    y = margin_top + 30
    title_text = doc_title.replace("_", " ").title()
    text_width = len(title_text) * 20 * 0.4
    x = (page_width - text_width) / 2
    page.insert_text(fitz.Point(x, y), title_text, fontsize=20, color=color_dark_blue)
    y += 40
    page.draw_line(fitz.Point(margin_left, y), fitz.Point(page_width - margin_right, y), color=(0.7, 0.7, 0.7), width=1)
    y += 30
    page.insert_text(fitz.Point(margin_left, y), f"Document Reference: {doc_ref}", fontsize=12, color=color_black)
    y += 20
    page.insert_text(fitz.Point(margin_left, y), f"Languages: English + {len(translations)} target language(s)", fontsize=12, color=color_black)
    y += 40
    page.insert_text(fitz.Point(margin_left, y), "Target Languages:", fontsize=14, color=color_dark_blue)
    y += 25
    for i, trans in enumerate(translations):
        lang = trans.get('language', 'Unknown')
        page.insert_text(fitz.Point(margin_left + 20, y), f"{i+1}. {lang}", fontsize=11, color=color_black)
        y += 18
    y += 20
    page.insert_text(fitz.Point(margin_left, y), "This document contains confidential medical device information.", fontsize=10, color=color_gray)
    
    # Deputy Synthesis Page
    page = add_new_page()
    y = margin_top
    text_width = len("Deputy Synthesis") * 18 * 0.4
    x = (page_width - text_width) / 2
    page.insert_text(fitz.Point(x, y), "Deputy Synthesis", fontsize=18, color=color_dark_blue)
    y += 30
    page.draw_line(fitz.Point(margin_left, y), fitz.Point(page_width - margin_right, y), color=color_dark_blue, width=0.5)
    y += 25
    synthesis_text = f"This multilingual IFU document contains the original English version along with {len(translations)} target language(s) as required by EU MDR 2017/745 and FDA regulations."
    y = insert_text_func(page, margin_left, y, synthesis_text, 11, color_black, content_width)
    
    # Contents Page
    page = add_new_page()
    y = margin_top
    text_width = len("Contents") * 18 * 0.4
    x = (page_width - text_width) / 2
    page.insert_text(fitz.Point(x, y), "Contents", fontsize=18, color=color_dark_blue)
    y += 30
    page.draw_line(fitz.Point(margin_left, y), fitz.Point(page_width - margin_right, y), color=color_dark_blue, width=0.5)
    y += 25
    page.insert_text(fitz.Point(margin_left, y), "Language", fontsize=14, color=color_dark_blue)
    page.insert_text(fitz.Point(page_width - margin_right - 80, y), "Page No.", fontsize=14, color=color_dark_blue)
    y += 5
    page.draw_line(fitz.Point(margin_left, y), fitz.Point(page_width - margin_right, y), color=color_gray, width=0.3)
    y += 20
    page.insert_text(fitz.Point(margin_left, y), "English", fontsize=12, color=color_black)
    page.insert_text(fitz.Point(page_width - margin_right - 80, y), "4", fontsize=12, color=color_black)
    y += 20
    
    current_page = 4
    for trans in translations:
        lang = trans.get('language', 'Unknown')
        page_count = len(trans.get('segments', []))
        lang_pages = max(1, (page_count // 30) + 1)
        current_page += lang_pages
        page.insert_text(fitz.Point(margin_left, y), lang, fontsize=12, color=color_black)
        page.insert_text(fitz.Point(page_width - margin_right - 80, y), str(current_page), fontsize=12, color=color_black)
        y += 20
    
    # English Content
    page = add_new_page()
    y = margin_top
    text_width = len("English Version") * 16 * 0.4
    x = (page_width - text_width) / 2
    page.insert_text(fitz.Point(x, y), "English Version", fontsize=16, color=color_dark_blue)
    y += 25
    page.draw_line(fitz.Point(margin_left, y), fitz.Point(page_width - margin_right, y), color=color_dark_blue, width=0.5)
    y += 20
    for seg in original_segments:
        text = seg.get('text', '')
        seg_type = seg.get('type', 'p')
        if not text:
            continue
        new_page_needed, y = check_new_page(y, 50)
        if new_page_needed:
            page = new_page_needed
        if seg_type in ['h1']:
            y = insert_text_func(page, margin_left, y, text, 16, color_dark_blue, content_width)
            y += 10
        elif seg_type in ['h2']:
            y = insert_text_func(page, margin_left, y, text, 14, color_dark_blue, content_width)
            y += 8
        else:
            y = insert_text_func(page, margin_left, y, text, 11, color_black, content_width)
            y += 8
    
    # Each Target Language
    for trans in translations:
        lang = trans.get('language', 'Unknown')
        segments = trans.get('segments', [])
        page = add_new_page()
        y = margin_top
        header_text = f"{lang} Version"
        text_width = len(header_text) * 16 * 0.4
        x = (page_width - text_width) / 2
        page.insert_text(fitz.Point(x, y), header_text, fontsize=16, color=color_dark_blue)
        y += 25
        page.draw_line(fitz.Point(margin_left, y), fitz.Point(page_width - margin_right, y), color=color_dark_blue, width=0.5)
        y += 20
        for seg in segments:
            text = seg.get('translated_text', '')
            seg_type = seg.get('type', 'p')
            if not text:
                continue
            new_page_needed, y = check_new_page(y, 50)
            if new_page_needed:
                page = new_page_needed
            if seg_type in ['h1']:
                y = insert_text_func(page, margin_left, y, text, 16, color_dark_blue, content_width)
                y += 10
            elif seg_type in ['h2']:
                y = insert_text_func(page, margin_left, y, text, 14, color_dark_blue, content_width)
                y += 8
            else:
                y = insert_text_func(page, margin_left, y, text, 11, color_black, content_width)
                y += 8
    
    return doc.tobytes()


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
        list_counters = {}
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            style_name = para.style.name.lower() if para.style else ""
            
            if style_name.startswith('heading 1'):
                seg_type = "h1"
            elif style_name.startswith('heading 2'):
                seg_type = "h2"
            elif style_name.startswith('heading 3'):
                seg_type = "h3"
            elif 'list' in style_name or 'bullet' in style_name:
                seg_type = "li"
            elif 'number' in style_name or 'ordered' in style_name:
                num_id = para._element.pPr.numPr.numId.val if para._element.pPr is not None and para._element.pPr.numPr is not None else None
                if num_id is not None:
                    if num_id not in list_counters:
                        list_counters[num_id] = 1
                    else:
                        list_counters[num_id] += 1
                    seg_type = "ol"
                else:
                    seg_type = "li"
            elif para.runs and any(r.bold for r in para.runs if r.text.strip()):
                all_bold = all(r.bold for r in para.runs if r.text.strip())
                if all_bold and len(text) < 100:
                    seg_type = "h3"
                else:
                    seg_type = "li"
            elif para.paragraph_format.left_indent is not None and para.paragraph_format.left_indent > 0:
                seg_type = "li"
            else:
                seg_type = "p"
            
            extra_data = {}
            if seg_type == "ol" and num_id is not None:
                extra_data["number"] = list_counters[num_id]
            
            segments.append({
                "id": segment_id,
                "type": seg_type,
                "text": text,
                **extra_data
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
    
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
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
    Create a PDF with proper HTML-like formatting using PyMuPDF.
    Preserves document structure with styled headings, sections, and bullet points.
    """
    # Page dimensions (A4)
    page_width = 595
    page_height = 842
    margin_left = 50
    margin_right = 50
    margin_top = 60
    margin_bottom = 50
    content_width = page_width - margin_left - margin_right
    
    # Create PDF document
    doc = fitz.open()
    page = doc.new_page(width=page_width, height=page_height)
    
    # Colors
    color_black = (0, 0, 0)
    color_dark_blue = (0.1, 0.2, 0.4)
    color_gray = (0.5, 0.5, 0.5)
    
    y_position = margin_top
    
    # Helper function to wrap text
    def wrap_text(text, max_width, fontsize):
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            estimated_width = len(test_line) * fontsize * 0.4
            
            if estimated_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [""]
    
    # Helper function to check if new page needed
    def check_new_page(required_height):
        nonlocal y_position, page
        if y_position + required_height > page_height - margin_bottom:
            page = doc.new_page(width=page_width, height=page_height)
            y_position = margin_top
            return True
        return False
    
    # Helper function to insert centered text
    def insert_centered_text(page, y, text, fontsize, color):
        text_width = len(text) * fontsize * 0.4
        x = (page_width - text_width) / 2
        page.insert_text(fitz.Point(x, y), text, fontsize=fontsize, color=color)
    
    # ====== HEADER SECTION ======
    # Title
    check_new_page(30)
    insert_centered_text(page, y_position, doc_title, 20, color_dark_blue)
    y_position += 25
    
    # Subtitle
    subtitle = f"Reference: {doc_ref} | Language: {target_lang}"
    insert_centered_text(page, y_position, subtitle, 10, color_gray)
    y_position += 20
    
    # Horizontal line
    page.draw_line(fitz.Point(margin_left, y_position), fitz.Point(page_width - margin_right, y_position), color=(0.7, 0.7, 0.7), width=0.5)
    y_position += 15
    
    # ====== CONTENT SECTION ======
    for seg in segments:
        text = seg.get("translated_text", seg.get("text", ""))
        if not text:
            continue
        
        seg_type = seg.get("type", "p")
        
        # Apply formatting based on segment type
        if seg_type == "h1":
            # Heading 1: Large, bold, dark blue
            check_new_page(25)
            page.insert_text(fitz.Point(margin_left, y_position), text, fontsize=18, color=color_dark_blue)
            y_position += 30
            
        elif seg_type == "h2":
            # Heading 2: Medium-large, bold
            check_new_page(22)
            page.insert_text(fitz.Point(margin_left, y_position), text, fontsize=15, color=color_black)
            y_position += 24
            
        elif seg_type == "h3":
            # Heading 3: Medium, bold
            check_new_page(20)
            page.insert_text(fitz.Point(margin_left, y_position), text, fontsize=13, color=color_black)
            y_position += 20
            
        elif seg_type == "li":
            # List item: bullet with indentation
            indent = 20
            wrapped = wrap_text(text, content_width - indent, 11)
            
            for i, line_text in enumerate(wrapped):
                check_new_page(16)
                bullet_x = margin_left + 5
                text_x = margin_left + indent
                
                if i == 0:
                    page.insert_text(fitz.Point(bullet_x, y_position), "•", fontsize=12, color=color_black)
                
                page.insert_text(fitz.Point(text_x, y_position), line_text, fontsize=11, color=color_black)
                y_position += 14
            y_position += 4
            
        elif seg_type == "ol":
            # Ordered list: number with indentation
            indent = 25
            number = seg.get("number", 1)
            wrapped = wrap_text(text, content_width - indent, 11)
            
            for i, line_text in enumerate(wrapped):
                check_new_page(16)
                num_x = margin_left + 10
                text_x = margin_left + indent
                
                if i == 0:
                    page.insert_text(fitz.Point(num_x, y_position), f"{number}.", fontsize=11, color=color_black)
                
                page.insert_text(fitz.Point(text_x, y_position), line_text, fontsize=11, color=color_black)
                y_position += 14
            y_position += 4
            
        else:
            # Regular paragraph
            wrapped = wrap_text(text, content_width, 11)
            
            for line_text in wrapped:
                check_new_page(16)
                page.insert_text(fitz.Point(margin_left, y_position), line_text, fontsize=11, color=color_black)
                y_position += 14
            y_position += 8
    
    # Add page numbers
    for p in doc:
        footer_text = f"Page {p.number}"
        text_width = len(footer_text) * 9 * 0.4
        x = (page_width - text_width) / 2
        page_rect = p.rect
        footer_y = page_rect.height - 30
        p.insert_text(fitz.Point(x, footer_y), footer_text, fontsize=9, color=color_gray)
    
    return doc.tobytes()


def create_translated_pdf(translated_text: str, source_filename: str = "translated") -> bytes:
    """
    Generate a PDF from translated text with proper formatting using PyMuPDF.
    Automatically detects headings, subheadings, and list items.
    """
    # Page dimensions (A4)
    page_width = 595
    page_height = 842
    margin_left = 50
    margin_right = 50
    margin_top = 60
    margin_bottom = 50
    content_width = page_width - margin_left - margin_right
    
    # Create PDF document
    doc = fitz.open()
    page = doc.new_page(width=page_width, height=page_height)
    
    # Colors
    color_black = (0, 0, 0)
    color_dark_blue = (0.1, 0.2, 0.4)
    color_gray = (0.5, 0.5, 0.5)
    
    y_position = margin_top
    
    # Helper function to wrap text
    def wrap_text(text, max_width, fontsize):
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            estimated_width = len(test_line) * fontsize * 0.4
            
            if estimated_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [""]
    
    # Helper function to check if new page needed
    def check_new_page(required_height):
        nonlocal y_position, page
        if y_position + required_height > page_height - margin_bottom:
            page = doc.new_page(width=page_width, height=page_height)
            y_position = margin_top
            return True
        return False
    
    # Helper function to insert centered text
    def insert_centered_text(page, y, text, fontsize, color):
        text_width = len(text) * fontsize * 0.4
        x = (page_width - text_width) / 2
        page.insert_text(fitz.Point(x, y), text, fontsize=fontsize, color=color)
    
    # Add header
    check_new_page(30)
    title = source_filename.replace(".pdf", "").replace("_", " ").title()
    insert_centered_text(page, y_position, title, 20, color_dark_blue)
    y_position += 25
    
    # Horizontal line
    page.draw_line(fitz.Point(margin_left, y_position), fitz.Point(page_width - margin_right, y_position), color=(0.7, 0.7, 0.7), width=0.5)
    y_position += 15
    
    # Parse and format the text
    lines = translated_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            y_position += 8
            continue
        
        # Detect formatting based on line content
        is_heading = False
        heading_level = 0
        
        # Check for markdown-style headings
        if line.startswith('# '):
            heading_level = 1
            line = line[2:].strip()
            is_heading = True
        elif line.startswith('## '):
            heading_level = 2
            line = line[3:].strip()
            is_heading = True
        elif line.startswith('### '):
            heading_level = 3
            line = line[4:].strip()
            is_heading = True
        # Check for ALL CAPS lines (often headings)
        elif line.isupper() and len(line) < 80 and not any(c.isdigit() for c in line):
            heading_level = 2
            is_heading = True
        # Check for lines ending with colon (subheadings)
        elif line.endswith(':') and len(line) < 60:
            heading_level = 3
            is_heading = True
        
        # Check for bullet points
        is_bullet = line.startswith('• ') or line.startswith('- ') or line.startswith('* ')
        if is_bullet:
            line = line[2:].strip()
        
        # Check for numbered lists
        is_numbered = bool(re.match(r'^\d+[\.)]\s', line))
        if is_numbered:
            line = re.sub(r'^\d+[\.)]\s', '', line).strip()
        
        # Format based on type
        if is_heading:
            check_new_page(25)
            if heading_level == 1:
                page.insert_text(fitz.Point(margin_left, y_position), line, fontsize=18, color=color_dark_blue)
                y_position += 30
            elif heading_level == 2:
                page.insert_text(fitz.Point(margin_left, y_position), line, fontsize=15, color=color_black)
                y_position += 24
            else:
                page.insert_text(fitz.Point(margin_left, y_position), line, fontsize=13, color=color_black)
                y_position += 20
                
        elif is_bullet:
            indent = 20
            wrapped = wrap_text(line, content_width - indent, 11)
            
            for i, line_text in enumerate(wrapped):
                check_new_page(16)
                bullet_x = margin_left + 5
                text_x = margin_left + indent
                
                if i == 0:
                    page.insert_text(fitz.Point(bullet_x, y_position), "•", fontsize=12, color=color_black)
                
                page.insert_text(fitz.Point(text_x, y_position), line_text, fontsize=11, color=color_black)
                y_position += 14
            y_position += 4
            
        elif is_numbered:
            indent = 25
            wrapped = wrap_text(line, content_width - indent, 11)
            
            for i, line_text in enumerate(wrapped):
                check_new_page(16)
                num_x = margin_left + 10
                text_x = margin_left + indent
                
                if i == 0:
                    page.insert_text(fitz.Point(num_x, y_position), "1.", fontsize=11, color=color_black)
                
                page.insert_text(fitz.Point(text_x, y_position), line_text, fontsize=11, color=color_black)
                y_position += 14
            y_position += 4
            
        else:
            # Regular paragraph
            wrapped = wrap_text(line, content_width, 11)
            
            for line_text in wrapped:
                check_new_page(16)
                page.insert_text(fitz.Point(margin_left, y_position), line_text, fontsize=11, color=color_black)
                y_position += 14
            y_position += 8
    
    # Add page numbers
    for p in doc:
        footer_text = f"Page {p.number}"
        text_width = len(footer_text) * 9 * 0.4
        x = (page_width - text_width) / 2
        page_rect = p.rect
        footer_y = page_rect.height - 30
        p.insert_text(fitz.Point(x, footer_y), footer_text, fontsize=9, color=color_gray)
    
    return doc.tobytes()
