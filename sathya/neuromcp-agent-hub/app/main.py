"""
FastAPI Main Application
Production-ready backend for NeuroMCP Agent Hub
"""
from fastapi import FastAPI
from app.config.env import load_dotenv  # Load environment variables

# Import routers
from app.routes.oauth_slack import router as slack_router
from app.routes.oauth_google import router as google_router
from app.routes.agent_api import router as agent_router

# Create FastAPI app
app = FastAPI(
    title="NeuroMCP Agent Hub",
    description="Enterprise AI Agent Platform with Multi-Tool Integration",
    version="1.0.0"
)

# Register routers
app.include_router(slack_router, tags=["OAuth - Slack"])
app.include_router(google_router, tags=["OAuth - Google"])
app.include_router(agent_router, tags=["Agent Execution"])

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "NeuroMCP Backend Running ✅",
        "version": "1.0.0"
    }
