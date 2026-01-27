"""
FastAPI application for RAG system.
Provides REST API endpoints for document ingestion and querying.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
import shutil
from pathlib import Path

from rag_pipeline import RAGPipeline
from config import UPLOAD_DIR
from logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="Advanced RAG System API",
    description="Production-grade RAG system with semantic chunking and re-ranking",
    version="1.0.0"
)

# Global pipeline instance
pipeline = None


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str
    metadata_filter: Optional[Dict] = None


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup."""
    global pipeline
    logger.info("Starting RAG API server")
    pipeline = RAGPipeline(index_name="main")
    
    # Try to load existing index
    try:
        pipeline.load_existing_index()
        logger.info("Loaded existing index")
    except Exception as e:
        logger.info(f"No existing index found: {e}")


@app.post("/ingest", summary="Ingest a PDF document")
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a PDF document into the RAG system.
    
    Args:
        file: PDF file to ingest
    
    Returns:
        Ingestion statistics
    """
    try:
        logger.info(f"Received document upload: {file.filename}")
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to: {file_path}")
        
        # Process document
        stats = pipeline.ingest_document(str(file_path), save_index=True)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Document ingested successfully",
                "statistics": stats
            }
        )
        
    except Exception as e:
        logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", summary="Query the RAG system")
async def query_documents(request: QueryRequest):
    """
    Query the RAG system with a question.
    
    Args:
        request: Query request with question and optional filters
    
    Returns:
        Answer with sources
    """
    try:
        logger.info(f"Received query: {request.query}")
        
        if pipeline.vector_store.index is None:
            raise HTTPException(
                status_code=400,
                detail="No documents ingested. Please upload a document first."
            )
        
        # Process query
        result = pipeline.query(request.query, request.metadata_filter)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "result": result
            }
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", summary="Health check")
async def health_check():
    """
    Check API health status.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "index_loaded": pipeline.vector_store.index is not None,
        "total_vectors": pipeline.vector_store.index.ntotal if pipeline.vector_store.index else 0
    }


@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Advanced RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "POST /ingest": "Upload and ingest PDF documents",
            "POST /query": "Query the document collection",
            "GET /health": "Check system health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
