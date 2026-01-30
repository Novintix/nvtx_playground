# app/agents/planner/agent_main.py
import os
from app.agents.planner.agent import create_plan_with_groq
from app.agents.planner.offline_planner import build_plan

def run_planner(state: dict) -> dict:
    user_request = state["user_request"]
    tools = state["available_tools"]
    tz = state.get("timezone", "Asia/Kolkata")

    logs = state.get("logs", [])
    try:
        if os.getenv("OFFLINE_PLANNER", "false").lower() == "true":
            logs.append({"agent": "planner", "msg": "OFFLINE_PLANNER enabled → using rule-based planner."})
            plan_obj = build_plan(user_request, tools, tz=tz)
        else:
            plan_obj = create_plan_with_groq(user_request, tools, retries=2)
            # Convert Pydantic model to dict for validator
            if hasattr(plan_obj, 'model_dump'):
                plan_obj = plan_obj.model_dump()

        state["plan"] = plan_obj
        
        # Debug: Log the plan for troubleshooting
        import json
        if hasattr(plan_obj, 'model_dump'):
            plan_dict = plan_obj.model_dump()
        else:
            plan_dict = plan_obj
        logs.append({"agent": "planner", "msg": f"Generated plan: {json.dumps(plan_dict, indent=2)}"})
        
        logs.append({"agent": "planner", "msg": "Plan created successfully."})
        state["logs"] = logs
        return state

    except Exception as e:
        # Provide helpful error message
        error_msg = str(e)
        if "GROQ_API_KEY" in error_msg:
            logs.append({
                "agent": "planner", 
                "msg": f"❌ GROQ_API_KEY missing or invalid. Falling back to offline pattern-based planner."
            })
        else:
            logs.append({
                "agent": "planner", 
                "msg": f"Groq LLM failed: {error_msg}. Falling back to offline planner."
            })
        
        # Fallback to pattern-based planner
        plan_obj = build_plan(user_request, tools, tz=tz)
        state["plan"] = plan_obj
        state["logs"] = logs
        return state

