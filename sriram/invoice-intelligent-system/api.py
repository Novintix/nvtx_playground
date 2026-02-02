"""
REST API for Invoice Intelligence System.
Integrates LangGraph orchestration, MCP agents, and RAG.
"""

import uuid
import shutil
import asyncio
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from orchestrator import process_document
from rag_system import AdvancedRAGSystem
from config import UPLOAD_DIR, API_HOST, API_PORT
from logger import setup_logger

logger = setup_logger("API")

app = FastAPI(
    title="Invoice Intelligence System",
    description="AI-Powered Invoice Processing with LangChain, LangGraph, MCP, Neuro-Symbolic AI, and RAG",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global instances
rag_system = None
document_status = {}


class QueryRequest(BaseModel):
    """Query request model."""
    query: str
    metadata_filter: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    global rag_system
    
    logger.info("action=api_startup status=starting")
    
    # Initialize RAG system
    rag_system = AdvancedRAGSystem()
    
    logger.info("action=api_startup status=complete")


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload invoice document.
    Returns document_id for tracking.
    """
    logger.info(f"action=upload_received filename={file.filename}")
    
    try:
        # Generate document ID
        doc_id = f"INV_{uuid.uuid4().hex[:8].upper()}"
        
        # Detect file type
        file_ext = Path(file.filename).suffix.lower()
        file_type_map = {
            ".pdf": "pdf",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image",
            ".xlsx": "excel",
            ".docx": "word"
        }
        
        file_type = file_type_map.get(file_ext)
        if not file_type:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
        
        # Save file
        file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"doc={doc_id} action=file_saved path={file_path}")
        
        # Update status
        document_status[doc_id] = {
            "status": "uploaded",
            "filename": file.filename,
            "file_type": file_type,
            "file_path": str(file_path)
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "document_id": doc_id,
                "filename": file.filename,
                "file_type": file_type,
                "message": "Document uploaded successfully. Use /documents/process/{document_id} to process."
            }
        )
        
    except Exception as e:
        logger.error(f"action=upload_failed error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/process/{document_id}")
async def process_document_endpoint(document_id: str):
    """
    Process uploaded document through LangGraph workflow.
    Uses MCP servers for agent communication.
    """
    logger.info(f"doc={document_id} action=process_request")
    
    if document_id not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        doc_info = document_status[document_id]
        file_path = doc_info["file_path"]
        
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Update status
        document_status[document_id]["status"] = "processing"
        
        # Process through LangGraph workflow
        final_state = await process_document(
            document_id,
            file_path,
            doc_info["file_type"]
        )
        
        # Index in RAG system if we have structured data (even if validation failed)
        if final_state.get("structured_data"):
            try:
                rag_system.index_invoice(document_id, final_state["structured_data"])
                logger.info(f"doc={document_id} action=indexed_successfully")
            except Exception as e:
                logger.error(f"doc={document_id} action=indexing_failed error={str(e)}")
        
        # Update status
        document_status[document_id].update({
            "status": "complete" if not final_state.get("error") else "failed",
            "structured_data": final_state.get("structured_data"),
            "validation_result": final_state.get("validation_result"),
            "current_stage": final_state.get("current_stage"),
            "error": final_state.get("error")
        })
        
        return JSONResponse(
            status_code=200,
            content={
                "document_id": document_id,
                "status": document_status[document_id]["status"],
                "structured_data": final_state.get("structured_data"),
                "validation_result": final_state.get("validation_result"),
                "current_stage": final_state.get("current_stage"),
                "message": "Document processed and indexed. Use Query Service (Port 8002) to query all documents."
            }
        )
        
    except Exception as e:
        logger.error(f"doc={document_id} action=process_failed error={str(e)}")
        document_status[document_id]["status"] = "failed"
        document_status[document_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}/status")
async def get_document_status(document_id: str):
    """Get processing status of a document."""
    if document_id not in document_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return JSONResponse(
        status_code=200,
        content=document_status[document_id]
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "rag_system_ready": rag_system is not None,
        "mcp_server": f"http://127.0.0.1:8000"
    }


@app.get("/")
async def root():
    """Serve the UI."""
    return FileResponse("static/index.html")


@app.get("/api")
async def api_info():
    """Root endpoint with API information."""
    return {
        "name": "Invoice Intelligence System - Document Ingestion Service",
        "version": "2.0.0",
        "port": API_PORT,
        "purpose": "Upload and process documents only. For querying, use Query Service on Port 8002.",
        "technologies": {
            "orchestration": "LangGraph",
            "agents": "FastMCP",
            "rag": "LangChain + FAISS (indexing only)",
            "validation": "Neuro-Symbolic AI",
            "llm": "Gemini"
        },
        "endpoints": {
            "POST /documents/upload": "Upload invoice document",
            "POST /documents/process/{document_id}": "Process uploaded document",
            "GET /documents/{document_id}/status": "Get processing status",
            "GET /health": "Health check"
        },
        "query_service": {
            "url": "http://localhost:8002",
            "description": "Use Query Service for all querying operations"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
