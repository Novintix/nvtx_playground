from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from pathlib import Path
import json

import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

load_dotenv(Path(__file__).parent / ".env")

from languages import LANGUAGES
from translator import translate_text, translate_chunks
from corrector import correct_translation
from glossary import add_corrections
from docx import Document

app = FastAPI(title="IFU Translator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_MODELS = {"600m"}
_executor = ThreadPoolExecutor()


def get_lang(target_lang: str) -> dict:
    lang = LANGUAGES.get(target_lang)
    if not lang:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {target_lang}")
    return lang


# ── Languages ────────────────────────────────────────────────────────────────

@app.get("/languages")
async def list_languages():
    return [{"code": code, "name": info["name"]} for code, info in LANGUAGES.items()]


# ── File extraction (DOCX, Excel, PDF) ────────────────────────────────────────

@app.post("/extract-file")
async def extract_file(file: UploadFile = File(...)):
    raise HTTPException(status_code=400, detail="Legacy endpoint deprecated.")


# ── DOCX Segment Extraction (for frontend) ───────────────────────────────────

@app.post("/extract-docx")
async def extract_docx(file: UploadFile = File(...)):
    """
    Extract structured segments from DOCX file.
    Returns segments with HTML for formatting preservation.
    """
    file_bytes = await file.read()
    try:
        from placeholder_parser import extract_and_replace_elements
        
        doc = Document(io.BytesIO(file_bytes))
        doc_flow, asset_store = extract_and_replace_elements(doc)
        
        segments = []
        for i, text_block in enumerate(doc_flow):
            stripped = text_block.strip()
            # Mark placeholders as tables/images in UI
            if stripped.startswith("[TBL_") or stripped.startswith("[IMG_"):
                seg_type = "table"
            else:
                seg_type = "p"
                
            segments.append({
                "id": i,
                "type": seg_type,
                "text": text_block,
                "html": f"<p>{text_block}</p>",
                "style": "Normal",
                "level": 0
            })
            
        return {
            "filename": file.filename,
            "segments": segments,
            "html": "",
            "has_header": False,
            "has_footer": False,
            "page_count": 1
        }
    except Exception as e:
        import traceback
        print(f"[EXTRACT-DOCX] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to parse DOCX: {str(e)}")


# ── Translate Segments ───────────────────────────────────────────────────────

@app.post("/translate-segments")
async def translate_segments(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    model: str = Form("600m"),
    run_validation: bool = Form(True),
):
    """
    Translate DOCX utilizing the XML Placeholder extraction pipeline.
    """
    if model not in VALID_MODELS:
        raise HTTPException(status_code=400, detail=f"Invalid model: {model}")
    
    lang_info = get_lang(target_lang)
    file_bytes = await file.read()
    
    try:
        from docx import Document
        from placeholder_parser import extract_and_replace_elements
        import io
        
        doc = Document(io.BytesIO(file_bytes))
        doc_flow, asset_store = extract_and_replace_elements(doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid DOCX or Extraction Failed: {str(e)}")
    
    translated_flow = []
    validation_results = []
    segments_payload = []  # To maintain frontend compatibility for now
    
    async def generate():
        total = len(doc_flow)
        from validator import validate_translation_batch
        
        try:
            BATCH_SIZE = 15
            i = 0
            while i < total:
                # 1. Collect a batch of up to BATCH_SIZE items
                batch_indices = []
                batch_sources = []
                batch_placeholders = []
                
                # Scan ahead to fill batch
                scan_idx = i
                while scan_idx < total and len(batch_sources) < BATCH_SIZE:
                    text_block = doc_flow[scan_idx]
                    stripped = text_block.strip()
                    
                    if not stripped or stripped.startswith("[TBL_") or stripped.startswith("[IMG_"):
                        # Keep placeholders aligned, but don't translate them
                        batch_placeholders.append((scan_idx, text_block))
                    else:
                        batch_indices.append(scan_idx)
                        batch_sources.append(text_block)
                    scan_idx += 1
                
                # 2. Batch Translate
                translated_sources = batch_sources.copy() # fallback
                if batch_sources:
                    try:
                        # Combine all sources into one massive string block
                        # (The translator engine now splits it via spacy and chunks it automatically)
                        # However, to map results back precisely to our UI chunks, we loop here
                        # by calling translate_text which handles the heavy lifting under the hood
                        translated_sources = []
                        for src_text in batch_sources:
                            res = translate_text(src_text, model, target_lang)
                            translated_sources.append(res)
                    except Exception as e:
                        print(f"[TRANSLATE BATCH] Error: {e}")
                        translated_sources = batch_sources.copy()
                
                # 3. Batch Validate
                validation_results_map = {}
                if run_validation and batch_sources:
                    try:
                        print(f"[VALIDATE] Validating batch of {len(batch_sources)} segments...")
                        batch_val_res = validate_translation_batch(
                            sources=batch_sources,
                            translations=translated_sources,
                            target_lang_name=lang_info["name"],
                            target_lang=target_lang
                        )
                        results_array = batch_val_res.get("results", [])
                        for j, v_res in enumerate(results_array):
                            if j < len(batch_indices):
                                validation_results_map[batch_indices[j]] = v_res
                    except Exception as ve:
                        print(f"[VALIDATE BATCH] Error: {ve}")
                
                # 4. Yield processed segments
                # We need to yield them exactly in the order they appeared in the doc (scan_idx range)
                for cur_idx in range(i, scan_idx):
                    is_placeholder = any(p_idx == cur_idx for p_idx, _ in batch_placeholders)
                    original_text = doc_flow[cur_idx]
                    
                    if is_placeholder:
                        translated_text = original_text
                        v_res = None
                    else:
                        list_idx = batch_indices.index(cur_idx)
                        translated_text = translated_sources[list_idx]
                        v_res = validation_results_map.get(cur_idx)
                        
                        if v_res:
                            validation_results.append({
                                "segment_id": cur_idx,
                                "segment_type": "p",
                                "source": original_text[:500],
                                "translation": translated_text[:500],
                                "result": v_res,
                            })
                            
                    translated_flow.append(translated_text)
                    
                    segments_payload.append({
                        "id": cur_idx,
                        "type": "p" if not (original_text.strip().startswith("[TBL") or original_text.strip().startswith("[IMG")) else "table",
                        "text": original_text,
                        "translated_text": translated_text,
                        "html": f"<p>{translated_text}</p>",
                        "validation": v_res,
                    })
                    
                    progress = round((cur_idx + 1) / total * 100)
                    yield json.dumps({
                        "type": "progress",
                        "value": progress,
                        "completed": cur_idx + 1,
                        "total": total
                    }) + "\n"
                
                i = scan_idx
            
            passed = sum(1 for v in validation_results if v["result"].get("result") == "PASS")
            failed = sum(1 for v in validation_results if v["result"].get("result") == "FAIL")
            errors = sum(1 for v in validation_results if v["result"].get("result") == "ERROR")
            
            yield json.dumps({
                "type": "done",
                "segments": segments_payload,
                "translated_flow": translated_flow, # Return the perfectly ordered strings
                "validation_summary": {
                    "total": len(validation_results),
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                }
            }) + "\n"
                
        except Exception as e:
            import traceback
            print(f"[TRANSLATE-SEGMENTS] Stream Error: {e}")
            traceback.print_exc()
            yield json.dumps({"type": "error", "detail": str(e)}) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


# ── Export Validation Report (Excel) ─────────────────────────────────────────

@app.post("/export-validation-report")
async def export_validation_report(
    segments: str = Form(...),
    target_lang: str = Form(...),
    document_name: str = Form("translation_report"),
):
    """
    Export validation report as Excel file.
    Contains source text, translation, validation results, and corrections.
    """
    try:
        translated_segments = json.loads(segments)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid segments JSON")
    
    lang_info = get_lang(target_lang)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Validation Report"
    
    # Styles
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill("solid", fgColor="1E3A5F")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    row_fill_even = PatternFill("solid", fgColor="EFF6FF")
    row_fill_odd = PatternFill("solid", fgColor="FFFFFF")
    pass_fill = PatternFill("solid", fgColor="DCFCE7")
    fail_fill = PatternFill("solid", fgColor="FEE2E2")
    error_fill = PatternFill("solid", fgColor="FEF3C7")
    cell_align = Alignment(vertical="top", wrap_text=True)
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    
    # Headers
    headers = ["#", "Type", "Source (English)", f"Translation ({lang_info['name']})", 
               "Validation", "Accuracy Note", "Terminology Note", "Issues"]
    col_widths = [5, 8, 35, 35, 12, 25, 25, 40]
    
    for col, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font, cell.fill, cell.alignment, cell.border = header_font, header_fill, header_align, border
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[1].height = 28
    
    # Data rows
    passed = failed = errors = 0
    
    for i, seg in enumerate(translated_segments, start=1):
        row = i + 1
        validation = seg.get("validation")
        
        if validation:
            result = validation.get("result", "N/A")
            if result == "PASS":
                passed += 1
                result_fill = pass_fill
            elif result == "FAIL":
                failed += 1
                result_fill = fail_fill
            else:
                errors += 1
                result_fill = error_fill
        else:
            result = "N/A"
            result_fill = row_fill_even if i % 2 == 0 else row_fill_odd
        
        fill = result_fill if validation else (row_fill_even if i % 2 == 0 else row_fill_odd)
        
        # Build issues list from corrections
        issues = ""
        if validation and validation.get("corrections"):
            corr_list = validation["corrections"]
            issues = "\n".join([
                f"• {c.get('original', '')} → {c.get('correct', '')} ({c.get('context', '')})"
                for c in corr_list[:5]  # Limit to 5 issues per segment
            ])
        
        values = [
            i,
            seg.get("type", "p"),
            seg.get("text", "")[:300],
            seg.get("translated_text", "")[:300],
            result,
            validation.get("accuracy_note", "") if validation else "",
            validation.get("terminology_note", "") if validation else "",
            issues,
        ]
        
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.fill, cell.alignment, cell.border = fill, cell_align, border
            if col == 1:
                cell.alignment = Alignment(horizontal="center", vertical="top")
                cell.font = Font(name="Calibri", bold=True, color="64748B")
            elif col == 5 and validation:
                cell.font = Font(name="Calibri", bold=True)
        
        ws.row_dimensions[row].height = 60
    
    # Summary
    summary_row = len(translated_segments) + 3
    ws.cell(row=summary_row, column=1, value="SUMMARY")
    ws.cell(row=summary_row, column=1).font = Font(bold=True, size=12, color="1E3A5F")
    
    summary_data = [
        f"Total Segments: {len(translated_segments)}",
        f"Validated: {passed + failed + errors}",
        f"PASS: {passed}",
        f"FAIL: {failed}",
        f"Errors: {errors}",
        f"Target Language: {lang_info['name']}",
    ]
    
    for i, summary in enumerate(summary_data, start=1):
        ws.cell(row=summary_row + i, column=1, value=summary)
        ws.cell(row=summary_row + i, column=1).font = Font(color="1E3A5F")
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"{document_name}_validation_{target_lang}.xlsx"
    return Response(
        content=buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Export Frozen PDF ───────────────────────────────────────────────────────────

@app.post("/export-frozen-pdf")
async def export_frozen_pdf(
    file: UploadFile = File(...),
    segments: str = Form(...),
    target_lang: str = Form(...),
    doc_title: str = Form("IFU Document"),
    doc_ref: str = Form("IFU-001"),
):
    """
    Generate translated DOCX with perfect XML formatting preservation.
    Re-injects XML blobs from placeholders back into the document.
    """
    print(f"[EXPORT] Received request: target_lang={target_lang}, doc_title={doc_title}")
    
    try:
        translated_segments = json.loads(segments)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid segments JSON: {str(e)}")
    
    file_bytes = await file.read()
    
    try:
        from docx import Document
        from placeholder_parser import extract_and_replace_elements, recompose_elements
        import io
        
        # 1. Parse the original again to get the asset store
        src_doc = Document(io.BytesIO(file_bytes))
        doc_flow, asset_store = extract_and_replace_elements(src_doc)
        
        # 2. Extract the translated flow from the payload
        # Note: Depending on frontend state, segments might contain the translated text in order
        translated_flow = [s['translated_text'] for s in translated_segments]
        
        # 3. Create a fresh document for output (or deep copy source document formatting)
        out_doc = Document(io.BytesIO(file_bytes))
        recompose_elements(out_doc, translated_flow, asset_store)
        
        # Add page numbers to footer
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement, ns
        
        for section in out_doc.sections:
            footer = section.footer
            p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            
            fldChar1 = OxmlElement('w:fldChar')
            fldChar1.set(ns.qn('w:fldCharType'), 'begin')
            instrText = OxmlElement('w:instrText')
            instrText.set(ns.qn('xml:space'), 'preserve')
            instrText.text = "PAGE"
            fldChar2 = OxmlElement('w:fldChar')
            fldChar2.set(ns.qn('w:fldCharType'), 'separate')
            fldChar3 = OxmlElement('w:fldChar')
            fldChar3.set(ns.qn('w:fldCharType'), 'end')
            
            run._r.append(fldChar1)
            run._r.append(instrText)
            run._r.append(fldChar2)
            run._r.append(fldChar3)
        
        # Save reconstructed DOCX to temporary file
        import tempfile, os
        from docx2pdf import convert
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
            out_doc.save(tmp_docx.name)
            docx_path = tmp_docx.name
            
        pdf_path = docx_path.replace(".docx", ".pdf")
        
        # Convert DOCX to PDF maintaining all formatting
        convert(docx_path, pdf_path)
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        try:
            os.unlink(docx_path)
            os.unlink(pdf_path)
        except Exception as e:
            print(f"[CLEANUP] Error removing temp files: {e}")
            
        filename = f"{doc_title}_{target_lang}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate translated document: {str(e)}")


# ── Translation ───────────────────────────────────────────────────────────────

@app.post("/translate")
async def translate(
    text: str = Form(...),
    model: str = Form("600m"),
    target_lang: str = Form("fr"),
):
    if model not in VALID_MODELS:
        raise HTTPException(status_code=400, detail="Invalid model.")
    get_lang(target_lang)

    async def generate():
        try:
            print(f"[TRANSLATE] Starting translation: model={model}, target_lang={target_lang}, text_length={len(text)}")
            translated_chunks = []
            for chunk_text, step, total in translate_chunks(text, model, target_lang):
                print(f"[TRANSLATE] Chunk {step}/{total}: {chunk_text[:50]}...")
                translated_chunks.append(chunk_text)
                progress = round(step / total * 100)
                yield json.dumps({"type": "progress", "value": progress, "step": step, "total": total}) + "\n"
            final_translation = " ".join(translated_chunks)
            print(f"[TRANSLATE] Done: {final_translation[:100]}...")
            yield json.dumps({"type": "done", "translation": final_translation}) + "\n"
        except Exception as e:
            print(f"[TRANSLATE] Error: {e}")
            import traceback
            traceback.print_exc()
            yield json.dumps({"type": "error", "detail": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


# ── LLM correction ────────────────────────────────────────────────────────────

class CorrectRequest(BaseModel):
    source: str
    translations: dict
    target_lang: str


@app.post("/correct")
async def correct(req: CorrectRequest):
    lang = get_lang(req.target_lang)
    loop = asyncio.get_event_loop()

    async def correct_one(model_key: str, translation: str):
        result = await loop.run_in_executor(
            _executor,
            correct_translation,
            req.source,
            translation,
            req.target_lang,
            lang["name"],
        )
        return model_key, result

    tasks = [
        correct_one(k, v)
        for k, v in req.translations.items()
        if v and v.strip()
    ]
    results = await asyncio.gather(*tasks)
    return {k: v for k, v in results}


# ── Validation ────────────────────────────────────────────────────────────────

class ValidateRequest(BaseModel):
    source: str
    translation: str
    target_lang: str
    reference: Optional[str] = None


@app.post("/validate")
async def validate(req: ValidateRequest):
    lang = get_lang(req.target_lang)
    try:
        from validator import validate_translation_batch
        res = validate_translation_batch(
            sources=[req.source],
            translations=[req.translation],
            target_lang_name=lang["name"],
            target_lang=req.target_lang
        )
        return res["results"][0] if res.get("results") else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Glossary ──────────────────────────────────────────────────────────────────

class GlossaryUpdateRequest(BaseModel):
    corrections: List[dict]
    target_lang: str


@app.post("/glossary/add")
async def glossary_add(req: GlossaryUpdateRequest):
    lang_pair = f"en-{req.target_lang}"
    count = add_corrections(req.corrections, lang_pair)
    return {"added": count}


# ── PDF export ────────────────────────────────────────────────────────────────

@app.post("/export-pdf")
async def export_pdf(
    text: str = Form(...),
    filename: str = Form("translated"),
    target_lang: str = Form("fr"),
):
    raise HTTPException(status_code=400, detail="Endpoint deprecated. Use /export-frozen-pdf instead.")


# ── Excel export (legacy) ───────────────────────────────────────────────────

class Correction(BaseModel):
    original: str
    mistranslated: str
    correct: str
    context: str


class ExcelExportRequest(BaseModel):
    corrections: List[Correction]
    document_name: Optional[str] = "translation"


@app.post("/export-excel")
async def export_excel(req: ExcelExportRequest):
    wb = Workbook()
    ws = wb.active
    ws.title = "Translation Corrections"

    header_font  = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill  = PatternFill("solid", fgColor="1E3A5F")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    row_fill_even = PatternFill("solid", fgColor="EFF6FF")
    row_fill_odd  = PatternFill("solid", fgColor="FFFFFF")
    critical_fill = PatternFill("solid", fgColor="FEF2F2")
    cell_align    = Alignment(vertical="top", wrap_text=True)
    thin   = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    headers    = ["#", "Original (English)", "Mistranslated As", "Correct Translation", "Context / Notes"]
    col_widths = [5, 35, 35, 35, 45]

    for col, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font, cell.fill, cell.alignment, cell.border = header_font, header_fill, header_align, border
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[1].height = 28

    critical_keywords = ["critical", "sterile", "implant", "contraindic", "warning", "caution", "dose", "dosage"]

    for i, c in enumerate(req.corrections, start=1):
        row = i + 1
        is_critical = any(kw in c.context.lower() or kw in c.original.lower() for kw in critical_keywords)
        fill = critical_fill if is_critical else (row_fill_even if i % 2 == 0 else row_fill_odd)
        values = [i, c.original, c.mistranslated, c.correct, c.context]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.fill, cell.alignment, cell.border = fill, cell_align, border
            if col == 1:
                cell.alignment = Alignment(horizontal="center", vertical="top")
                cell.font = Font(name="Calibri", bold=True, color="64748B")
            elif col == 3:
                cell.font = Font(name="Calibri", color="DC2626")
            elif col == 4:
                cell.font = Font(name="Calibri", color="15803D", bold=True)
        ws.row_dimensions[row].height = 42

    if req.corrections:
        summary_row = len(req.corrections) + 3
        ws.cell(row=summary_row, column=1, value=f"Total issues: {len(req.corrections)}")
        ws.cell(row=summary_row, column=1).font = Font(bold=True, color="1E3A5F")

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"{req.document_name}_corrections.xlsx"
    return Response(
        content=buffer.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
