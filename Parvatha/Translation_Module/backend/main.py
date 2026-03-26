# Translation Backend - FastAPI Application

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from docx import Document
import io
import os

app = FastAPI(title="Translation API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory storage for glossary (in production, use a database)
glossary_store: Dict[str, List[Dict[str, str]]] = {}


def parse_docx(file: UploadFile) -> List[Dict[str, Any]]:
    """Parse a .docx file and extract segments"""
    doc = Document(file.file)
    segments = []
    segment_id = 1
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        # Determine segment type based on style
        style_name = para.style.name.lower() if para.style else ""
        
        if style_name.startswith('heading 1') or style_name == 'title':
            segment_type = "h1"
        elif style_name.startswith('heading 2'):
            segment_type = "h2"
        elif style_name.startswith('heading 3'):
            segment_type = "h3"
        elif style_name.startswith('list'):
            segment_type = "li"
        else:
            segment_type = "p"
        
        segments.append({
            "id": segment_id,
            "type": segment_type,
            "text": text
        })
        segment_id += 1
    
    return segments


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Translation API is running"}


@app.post("/extract-docx")
async def extract_docx(file: UploadFile = File(...)):
    """Extract segments from a .docx file"""
    try:
        if not file.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="File must be a .docx file")
        
        segments = parse_docx(file)
        return {"segments": segments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate-segments")
async def translate_segments(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    run_validation: str = Form("false")
):
    """Translate segments using NLLB model with optional validation"""
    try:
        # Parse the document to get segments
        segments = parse_docx(file)
        
        # Simple mock translation - in production, use NLLB-200 model
        translated_segments = []
        for seg in segments:
            translated_text = f"[{target_lang}] {seg['text']}"
            translated_segments.append({
                "id": seg["id"],
                "type": seg["type"],
                "text": seg["text"],
                "translated_text": translated_text
            })
        
        # Calculate mock validation summary
        total = len(translated_segments)
        validation_summary = {
            "total": total,
            "passed": total,
            "failed": 0,
            "errors": 0
        }
        
        # Return as NDJSON streaming response
        # First send progress updates, then final result
        result = {
            "type": "done",
            "segments": translated_segments,
            "validation_summary": validation_summary
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export-frozen-pdf")
async def export_frozen_pdf(
    file: UploadFile = File(...),
    segments: str = Form(...),
    target_lang: str = Form(...),
    doc_title: str = Form("Untitled"),
    doc_ref: str = Form("")
):
    """Generate a PDF from translated segments"""
    try:
        from fpdf import FPDF
        
        segments_data = json.loads(segments)
        
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, doc_title, 0, 1, 'C')
                self.ln(5)
            
            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 10)
        
        for seg in segments_data:
            text = seg.get('translated_text', seg.get('text', ''))
            
            # Format based on segment type
            seg_type = seg.get('type', 'p')
            if seg_type == 'h1':
                pdf.set_font('Arial', 'B', 16)
                pdf.ln(5)
            elif seg_type == 'h2':
                pdf.set_font('Arial', 'B', 14)
                pdf.ln(3)
            elif seg_type == 'h3':
                pdf.set_font('Arial', 'B', 12)
                pdf.ln(2)
            else:
                pdf.set_font('Arial', '', 10)
            
            pdf.multi_cell(0, 5, text)
            pdf.ln(2)
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/glossary/add")
async def add_to_glossary(
    corrections: List[Dict[str, str]],
    target_lang: str
):
    """Add term corrections to the glossary"""
    try:
        if target_lang not in glossary_store:
            glossary_store[target_lang] = []
        
        added_count = 0
        for corr in corrections:
            glossary_store[target_lang].append({
                "original": corr.get("original", ""),
                "correct": corr.get("correct", ""),
                "context": corr.get("context", ""),
                "added_at": datetime.now().isoformat()
            })
            added_count += 1
        
        return {"added": added_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export-multilingual-pdf")
async def export_multilingual_pdf(
    file: UploadFile = File(...),
    translations_map: str = Form(...),
    doc_title: str = Form("Untitled"),
    doc_ref: str = Form("")
):
    """Generate a multilingual PDF with multiple translations"""
    try:
        from fpdf import FPDF
        
        translations = json.loads(translations_map)
        
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, doc_title, 0, 1, 'C')
                self.ln(5)
            
            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
        pdf = PDF()
        
        # Add a page for each language
        for lang_code, segments in translations.items():
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f"Language: {lang_code}", 0, 1)
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            
            for seg in segments:
                text = seg.get('translated_text', seg.get('text', ''))
                seg_type = seg.get('type', 'p')
                
                if seg_type == 'h1':
                    pdf.set_font('Arial', 'B', 16)
                elif seg_type == 'h2':
                    pdf.set_font('Arial', 'B', 14)
                elif seg_type == 'h3':
                    pdf.set_font('Arial', 'B', 12)
                else:
                    pdf.set_font('Arial', '', 10)
                
                pdf.multi_cell(0, 5, text)
                pdf.ln(2)
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
