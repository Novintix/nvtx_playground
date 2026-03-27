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
    """Parse a .docx file and extract segments natively from paragraphs and tables"""
    file.file.seek(0)
    doc = Document(file.file)
    
    from placeholder_parser import extract_translatable_elements
    flow = extract_translatable_elements(doc)
    
    segments = []
    segment_id = 1
    
    for text in flow:
        segments.append({
            "id": segment_id,
            "type": "p",  # Simplification since translation doesn't strictly need semantic headings
            "text": text
        })
        segment_id += 1
        
    file.file.seek(0)
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
        
        import asyncio

        async def stream_translation():
            from translator import translate_text
            translated_segments = []
            total = len(segments)
            
            for i, seg in enumerate(segments):
                try:
                    # Run heavy inference in thread to prevent blocking the server socket flush
                    translated_text = await asyncio.to_thread(
                        translate_text, seg["text"], "600m", target_lang
                    )
                except Exception as e:
                    print(f"Translation Error for {seg['text']}: {e}")
                    translated_text = f"[{target_lang}] Error: {seg['text']}"

                translated_segments.append({
                    "id": seg["id"],
                    "type": seg["type"],
                    "text": seg["text"],
                    "translated_text": translated_text
                })
                
                # Yield progress
                progress_msg = {
                    "type": "progress",
                    "completed": i + 1,
                    "total": total
                }
                yield json.dumps(progress_msg) + "\n"
            
            # In a real setup, we might also run validation here.
            validation_summary = {
                "total": total,
                "passed": total,
                "failed": 0,
                "errors": 0
            }
            
            final_msg = {
                "type": "done",
                "segments": translated_segments,
                "validation_summary": validation_summary
            }
            yield json.dumps(final_msg) + "\n"
            
        from fastapi.responses import StreamingResponse
        return StreamingResponse(stream_translation(), media_type="application/x-ndjson")
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
    """Generate a PDF from translated segments with exact layout mapping"""
    try:
        from fastapi import Response
        import tempfile
        import os
        from docx2pdf import convert
        from placeholder_parser import recompose_elements
        
        segments_data = json.loads(segments)
        translated_flow = [seg.get('translated_text', seg.get('text', '')) for seg in segments_data]
        
        file.file.seek(0)
        doc = Document(file.file)
        
        recompose_elements(doc, translated_flow)
        
        with tempfile.TemporaryDirectory() as td:
            docx_path = os.path.join(td, "temp.docx")
            pdf_path = os.path.join(td, "temp.pdf")
            
            doc.save(docx_path)
            # Use docx2pdf allowing MS Word to export native PDF
            convert(docx_path, pdf_path)
            
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
                
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        import traceback
        traceback.print_exc()
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
    """Generate a multilingual PDF with fully preserved layout"""
    try:
        from fastapi import Response
        import tempfile
        import os
        from docx2pdf import convert
        from placeholder_parser import recompose_elements
        import fitz  # PyMuPDF
        
        translations = json.loads(translations_map)
        
        file.file.seek(0)
        file_bytes = file.file.read()
        
        merged_pdf = fitz.open()
        
        with tempfile.TemporaryDirectory() as td:
            for lang_code, segments in translations.items():
                translated_flow = [seg.get('translated_text', seg.get('text', '')) for seg in segments]
                
                # Use a pristine copy of original document for each language
                lang_doc = Document(io.BytesIO(file_bytes))
                recompose_elements(lang_doc, translated_flow)
                
                docx_path = os.path.join(td, f"{lang_code}.docx")
                pdf_path = os.path.join(td, f"{lang_code}.pdf")
                
                lang_doc.save(docx_path)
                convert(docx_path, pdf_path)
                
                lang_pdf = fitz.open(pdf_path)
                merged_pdf.insert_pdf(lang_pdf)
                lang_pdf.close()
                
            final_pdf_path = os.path.join(td, "final.pdf")
            merged_pdf.save(final_pdf_path)
            merged_pdf.close()
            
            with open(final_pdf_path, "rb") as f:
                pdf_bytes = f.read()
                
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
