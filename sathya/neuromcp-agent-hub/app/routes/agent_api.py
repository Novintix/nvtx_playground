from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.langgraph.graph import build_graph

graph = build_graph()

router = APIRouter(prefix="/agent", tags=["Agent Execution"])


# -----------------------------
# Request Schemas
# -----------------------------

class RunRequest(BaseModel):
    user_request: str


class ApproveRequest(BaseModel):
    state: Dict[str, Any]
    approved_step_ids: List[str]


# -----------------------------
# RUN Endpoint (Planner → Validator)
# -----------------------------

@router.post("/run")
async def run_agent(req: RunRequest):
    state = {
        "user_request": req.user_request,
        "logs": []
    }

    result = await graph.ainvoke(state)

    return {
        "status": result.get("status"),
        "plan": result.get("plan"),
        "pending_approvals": result.get("pending_approvals"),
        "execution_results": result.get("execution_results"),
        "logs": result.get("logs")
    }


# -----------------------------
# APPROVE Endpoint (Executor Runs Tools)
# -----------------------------

@router.post("/approve")
async def approve_agent(req: ApproveRequest):

    updated_state = req.state
    updated_state["approved_step_ids"] = req.approved_step_ids

    result = await graph.ainvoke(updated_state)

    return {
        "status": result.get("status"),
        "execution_results": result.get("execution_results"),
        "logs": result.get("logs")
    }
