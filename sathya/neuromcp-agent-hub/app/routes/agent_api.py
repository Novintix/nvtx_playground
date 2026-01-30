from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.langgraph.graph import build_graph

graph = build_graph()

router = APIRouter(prefix="/agent", tags=["Agent Execution"])

# UPDATED: 2026-01-30 15:08 - Added pre-validation


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
    # Pre-validation: Check for obvious errors before wasting LLM tokens
    from app.agents.validator.pre_validation import validate_user_request
    
    is_valid, error_msg = validate_user_request(req.user_request)
    if not is_valid:
        # Return validation error immediately
        return {
            "status": "ERROR",
            "plan": None,
            "pending_approvals": [],
            "execution_results": {},
            "final_report": None,
            "logs": [
                {"agent": "pre_validator", "msg": "Running pre-validation checks..."},
                {"agent": "pre_validator", "msg": f"❌ Validation failed: {error_msg}"}
            ],
            "error": error_msg
        }
    
    # Validation passed, proceed with planning
    state = {
        "user_request": req.user_request,
        "logs": [{"agent": "pre_validator", "msg": "✅ Pre-validation passed"}]
    }

    result = await graph.ainvoke(state)

    return {
        "status": result.get("status"),
        "plan": result.get("plan"),
        "pending_approvals": result.get("pending_approvals"),
        "execution_results": result.get("execution_results"),
        "final_report": result.get("final_report"),  # Add formatted report
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
