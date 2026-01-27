from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.agents.symptom_interpretation.schema import SymptomInput
from app.agents.symptom_interpretation.agent_main import run_symptom_agent, AgentRunError

from app.schemas.triage_schema import StartTriageRequest, ContinueTriageRequest

# ✅ LangGraph
from app.langgraph.graphs_triage import build_triage_graph

app = FastAPI(title="Advanced Patient Triage")

# ✅ compile graph once
triage_graph = build_triage_graph()


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/symptom")
async def interpret_symptom(data: SymptomInput):
    try:
        result = await run_symptom_agent(
            user_input=data.user_input,
            previous_notes=data.previous_notes,
        )

        return JSONResponse(
            status_code=200,
            content={"status": "success", "data": result.model_dump()},
        )

    except AgentRunError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/triage/start")
async def triage_start(payload: StartTriageRequest):
    try:
        state = {"mode": "start", "user_input": payload.user_input}
        out = await triage_graph.ainvoke(state)

        # graph returns {"response": {...}}
        if isinstance(out, dict) and "response" in out:
            return out["response"]
        return out

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage start failed: {str(e)}")


@app.post("/triage/continue")
async def triage_continue(payload: ContinueTriageRequest):
    try:
        state = {
            "mode": "continue",
            "session_id": payload.session_id,
            "answers": payload.answers,
        }
        out = await triage_graph.ainvoke(state)

        if isinstance(out, dict) and "response" in out:
            return out["response"]
        return out

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage continue failed: {str(e)}")
