"""
Query Service API: Unified query interface for MongoDB and RAG.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from query_router import get_router
from logger import setup_logger

logger = setup_logger("QUERY_SERVICE")

app = FastAPI(
    title="Company Personal Assistant",
    description="Intelligent AI assistant for querying HR data, invoices, policies, and more",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="query_ui"), name="static")

# Global router instance
query_router = None


class QueryRequest(BaseModel):
    """Query request model."""
    query: str


@app.on_event("startup")
async def startup_event():
    """Initialize query router on startup."""
    global query_router
    
    logger.info("action=service_startup status=starting")
    query_router = get_router()
    logger.info("action=service_startup status=complete")


@app.get("/")
async def root():
    """Serve the company personal assistant UI."""
    return FileResponse("query_ui/index.html")


@app.post("/query")
async def query_data(request: QueryRequest):
    """
    Company Personal Assistant endpoint.
    Intelligently routes queries to appropriate data sources:
    - HR data (MongoDB)
    - Financial documents (RAG)
    - Policies (coming soon)
    
    The AI agent automatically determines which source to query based on your question.
    """
    logger.info(f"action=query_received query='{request.query}'")
    
    try:
        result = query_router.route_query(request.query)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"action=query_failed error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "router_ready": query_router is not None,
        "services": {
            "mongodb": "AI-HR database",
            "rag": "Invoice vector store"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
