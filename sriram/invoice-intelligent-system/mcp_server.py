"""
Unified MCP Server: All Invoice Intelligence Agents
Single server with all agent tools for production deployment.
"""

from fastmcp import FastMCP
from pathlib import Path
import json
import time
from datetime import datetime

# Import document processing libraries
import PyPDF2
from PIL import Image
import openpyxl
from docx import Document as DocxDocument

mcp = FastMCP("Invoice Intelligence Agents")

# ============================================================
# INGESTION AGENT TOOLS
# ============================================================

@mcp.tool()
def process_pdf(file_path: str) -> str:
    """
    Extract text and metadata from PDF file.
    Returns JSON with pages, text, and metadata.
    """
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            pages_data = []
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                text_density = len(text.strip()) / max(len(text), 1)
                
                pages_data.append({
                    "page_number": page_num,
                    "text": text,
                    "text_density": text_density,
                    "needs_ocr": text_density < 0.3
                })
            
            result = {
                "file_type": "pdf",
                "total_pages": len(reader.pages),
                "pages": pages_data,
                "metadata": {
                    "file_name": Path(file_path).name,
                    "total_pages": len(reader.pages)
                }
            }
            
            return json.dumps(result)
            
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def process_image(file_path: str) -> str:
    """
    Process image file and return metadata.
    Returns JSON indicating OCR is needed.
    """
    try:
        img = Image.open(file_path)
        
        result = {
            "file_type": "image",
            "total_pages": 1,
            "pages": [{
                "page_number": 1,
                "text": "",
                "text_density": 0.0,
                "needs_ocr": True
            }],
            "metadata": {
                "file_name": Path(file_path).name,
                "image_size": img.size,
                "format": img.format
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def process_excel(file_path: str) -> str:
    """
    Extract data from Excel file.
    Returns JSON with sheet data.
    """
    try:
        wb = openpyxl.load_workbook(file_path)
        
        sheets_data = []
        for sheet_idx, sheet in enumerate(wb.worksheets, start=1):
            rows = []
            for row in sheet.iter_rows(values_only=True):
                rows.append([str(cell) if cell is not None else "" for cell in row])
            
            content = "\n".join(["\t".join(row) for row in rows])
            
            sheets_data.append({
                "page_number": sheet_idx,
                "text": content,
                "text_density": 1.0,
                "needs_ocr": False,
                "sheet_name": sheet.title
            })
        
        result = {
            "file_type": "excel",
            "total_pages": len(sheets_data),
            "pages": sheets_data,
            "metadata": {
                "file_name": Path(file_path).name,
                "total_sheets": len(sheets_data)
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def process_word(file_path: str) -> str:
    """
    Extract text from Word document.
    Returns JSON with document text.
    """
    try:
        doc = DocxDocument(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        content = "\n".join(paragraphs)
        
        result = {
            "file_type": "word",
            "total_pages": 1,
            "pages": [{
                "page_number": 1,
                "text": content,
                "text_density": 1.0,
                "needs_ocr": False
            }],
            "metadata": {
                "file_name": Path(file_path).name,
                "paragraph_count": len(paragraphs)
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# OCR AGENT TOOL
# ============================================================

@mcp.tool()
def perform_ocr(file_path: str) -> str:
    """
    Perform OCR on image/scanned PDF using Azure Computer Vision.
    Returns JSON with extracted text and confidence.
    """
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        AZURE_CV_ENDPOINT = os.getenv("AZURE_CV_ENDPOINT")
        AZURE_CV_KEY = os.getenv("AZURE_CV_KEY")
        
        if not AZURE_CV_KEY or not AZURE_CV_ENDPOINT:
            return json.dumps({
                "success": False,
                "text": "",
                "confidence": 0.0,
                "message": "Azure credentials not configured"
            })
        
        from azure.cognitiveservices.vision.computervision import ComputerVisionClient
        from msrest.authentication import CognitiveServicesCredentials
        
        credentials = CognitiveServicesCredentials(AZURE_CV_KEY)
        client = ComputerVisionClient(AZURE_CV_ENDPOINT, credentials)
        
        with open(file_path, "rb") as image_stream:
            ocr_result = client.read_in_stream(image_stream, raw=True)
        
        operation_location = ocr_result.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]
        
        # Wait for result
        while True:
            result = client.get_read_result(operation_id)
            if result.status.lower() not in ['notstarted', 'running']:
                break
            time.sleep(1)
        
        extracted_text = []
        confidence_scores = []
        
        if result.status.lower() == 'succeeded':
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    extracted_text.append(line.text)
                    if hasattr(line, 'confidence'):
                        confidence_scores.append(line.confidence)
        
        text_content = "\n".join(extracted_text)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return json.dumps({
            "success": True,
            "text": text_content,
            "confidence": avg_confidence,
            "char_count": len(text_content)
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "text": "",
            "confidence": 0.0,
            "error": str(e)
        })


# ============================================================
# STRUCTURING AGENT TOOL
# ============================================================

@mcp.tool()
def structure_invoice(content: str) -> str:
    """
    Extract structured invoice data from text using Gemini.
    Returns JSON with vendor, invoice_number, date, line_items, totals.
    """
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        GEMINI_MODEL = "gemini-flash-latest"
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )
        
        prompt = f"""Extract invoice data and return ONLY valid JSON.

Invoice Text:
{content}

Return this JSON structure:
{{
    "vendor": "vendor name",
    "invoice_number": "invoice number",
    "invoice_date": "2024-01-15",
    "line_items": [{{"description": "item", "quantity": 10, "unit_price": 50.0, "amount": 500.0}}],
    "subtotal": 1000.0,
    "tax": 80.0,
    "total": 1080.0,
    "currency": "USD"
}}

Return ONLY JSON, no explanation."""
        
        response = llm.invoke(prompt)
        response_text = response.content
        
        # Handle if response is a list
        if isinstance(response_text, list):
            response_text = response_text[0] if response_text else ""
        
        response_text = str(response_text).strip()
        
        # Remove markdown if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        if not response_text:
            raise ValueError("Empty response from LLM")
        
        structured_data = json.loads(response_text)
        
        return json.dumps({
            "success": True,
            "data": structured_data
        })
        
    except json.JSONDecodeError as e:
        # Fallback structure
        fallback = {
            "vendor": "Unknown",
            "invoice_number": None,
            "invoice_date": None,
            "line_items": [],
            "subtotal": None,
            "tax": None,
            "total": None,
            "currency": "USD"
        }
        return json.dumps({
            "success": True,
            "data": fallback,
            "warning": f"Using fallback: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "data": None,
            "error": str(e)
        })


# ============================================================
# VALIDATION AGENT TOOL (Neuro-Symbolic)
# ============================================================

@mcp.tool()
def validate_invoice(invoice_data_json: str) -> str:
    """
    Apply neuro-symbolic validation rules to structured invoice data.
    Returns JSON with validation status and rule results.
    """
    try:
        invoice_data = json.loads(invoice_data_json)
        
        validation_results = []
        
        # Rule 1: Total Calculation
        subtotal = invoice_data.get("subtotal")
        tax = invoice_data.get("tax")
        total = invoice_data.get("total")
        
        if subtotal is not None and tax is not None and total is not None:
            calculated_total = subtotal + tax
            tolerance = 0.02
            
            if abs(calculated_total - total) <= tolerance:
                validation_results.append({
                    "rule": "total_calculation",
                    "status": "PASS",
                    "message": f"Total calculation correct: {subtotal} + {tax} = {total}"
                })
            else:
                validation_results.append({
                    "rule": "total_calculation",
                    "status": "FAIL",
                    "message": f"Total mismatch: {subtotal} + {tax} = {calculated_total}, expected {total}"
                })
        else:
            validation_results.append({
                "rule": "total_calculation",
                "status": "NEEDS_REVIEW",
                "message": "Missing financial values"
            })
        
        # Rule 2: Positive Amounts
        if total is not None:
            if total > 0:
                validation_results.append({
                    "rule": "positive_amounts",
                    "status": "PASS",
                    "message": f"Total is positive: {total}"
                })
            else:
                validation_results.append({
                    "rule": "positive_amounts",
                    "status": "FAIL",
                    "message": f"Total must be positive, got: {total}"
                })
        else:
            validation_results.append({
                "rule": "positive_amounts",
                "status": "NEEDS_REVIEW",
                "message": "Total amount missing"
            })
        
        # Rule 3: Required Fields
        vendor = invoice_data.get("vendor")
        invoice_date = invoice_data.get("invoice_date")
        
        missing = []
        if not vendor:
            missing.append("vendor")
        if not invoice_date:
            missing.append("invoice_date")
        
        if not missing:
            validation_results.append({
                "rule": "required_fields",
                "status": "PASS",
                "message": "All required fields present"
            })
        else:
            validation_results.append({
                "rule": "required_fields",
                "status": "FAIL",
                "message": f"Missing required fields: {', '.join(missing)}"
            })
        
        # Rule 4: Date Validity
        if invoice_date:
            try:
                date_obj = datetime.strptime(invoice_date, "%Y-%m-%d")
                
                if date_obj > datetime.now():
                    validation_results.append({
                        "rule": "date_validity",
                        "status": "FAIL",
                        "message": f"Invoice date is in future: {invoice_date}"
                    })
                else:
                    validation_results.append({
                        "rule": "date_validity",
                        "status": "PASS",
                        "message": f"Valid invoice date: {invoice_date}"
                    })
            except ValueError:
                validation_results.append({
                    "rule": "date_validity",
                    "status": "FAIL",
                    "message": f"Invalid date format: {invoice_date}"
                })
        else:
            validation_results.append({
                "rule": "date_validity",
                "status": "NEEDS_REVIEW",
                "message": "Invoice date missing"
            })
        
        # Rule 5: Line Items Consistency
        line_items = invoice_data.get("line_items", [])
        
        if line_items and subtotal is not None:
            line_items_sum = sum(item.get("amount", 0) for item in line_items)
            tolerance = 0.02 * len(line_items)
            
            if abs(line_items_sum - subtotal) <= tolerance:
                validation_results.append({
                    "rule": "line_items_consistency",
                    "status": "PASS",
                    "message": f"Line items sum matches subtotal: {line_items_sum} ≈ {subtotal}"
                })
            else:
                validation_results.append({
                    "rule": "line_items_consistency",
                    "status": "FAIL",
                    "message": f"Line items sum mismatch: {line_items_sum} vs subtotal {subtotal}"
                })
        else:
            validation_results.append({
                "rule": "line_items_consistency",
                "status": "NEEDS_REVIEW",
                "message": "No line items or subtotal missing"
            })
        
        # Determine overall status
        statuses = [r['status'] for r in validation_results]
        if all(s == 'PASS' for s in statuses):
            overall_status = 'PASS'
        elif any(s == 'FAIL' for s in statuses):
            overall_status = 'FAIL'
        else:
            overall_status = 'NEEDS_REVIEW'
        
        return json.dumps({
            "overall_status": overall_status,
            "validation_results": validation_results,
            "rules_passed": sum(1 for r in validation_results if r['status'] == 'PASS'),
            "rules_failed": sum(1 for r in validation_results if r['status'] == 'FAIL'),
            "rules_review": sum(1 for r in validation_results if r['status'] == 'NEEDS_REVIEW')
        })
        
    except Exception as e:
        return json.dumps({
            "overall_status": "ERROR",
            "validation_results": [],
            "error": str(e)
        })


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    MCP_PORT = int(os.getenv("MCP_PORT", 8000))
    
    print("=" * 60)
    print("🧾 Invoice Intelligence - Unified MCP Server")
    print("=" * 60)
    print(f"\n✅ Starting server on port {MCP_PORT}")
    print(f"\n📝 Available tools:")
    print("   - process_pdf")
    print("   - process_image")
    print("   - process_excel")
    print("   - process_word")
    print("   - perform_ocr")
    print("   - structure_invoice")
    print("   - validate_invoice")
    print(f"\n🌐 Server URL: http://127.0.0.1:{MCP_PORT}")
    print("=" * 60)
    
    mcp.run(transport="http", host="127.0.0.1", port=MCP_PORT)
