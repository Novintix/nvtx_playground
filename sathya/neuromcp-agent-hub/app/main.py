from fastapi import FastAPI
from app.config.env import load_dotenv  # noqa: F401


from app.routes.oauth_slack import router as slack_router
from app.routes.oauth_google import router as google_router
from app.routes.agent_api import router as agent_router
from app.routes.mcp_api import router as mcp_router

import os
from fastapi import FastAPI
from app.routes.mcp_api import router as mcp_router





print("MOCK_TOOLS =", os.getenv("MOCK_TOOLS"))
print("USE_MONGO_TOKENS =", os.getenv("USE_MONGO_TOKENS"))




app = FastAPI()

# OAuth Routers
app.include_router(slack_router)
app.include_router(google_router)

# Agent Execution Router
app.include_router(agent_router)
app.include_router(mcp_router, prefix="/mcp")


@app.get("/")
def root():
    return {"message": "NeuroMCP Backend Running ✅"}
