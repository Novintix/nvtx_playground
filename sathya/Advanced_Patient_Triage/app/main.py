from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.agents.symptom_interpretation.schema import SymptomInput
from app.agents.symptom_interpretation.agent_main import run_symptom_agent, AgentRunError

app = FastAPI(title="Advanced Patient Triage")


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/symptom")
async def interpret_symptom(data: SymptomInput):
    """
    Symptom Interpretation endpoint:
    - Takes patient free-text input
    - Calls Symptom Interpretation Agent (Groq)
    - Returns structured JSON response
    """
    try:
        result = await run_symptom_agent(
            user_input=data.user_input,
            previous_notes=data.previous_notes
        )

        # Postman-friendly response structure
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": result.model_dump()  # Pydantic v2
            }
        )

    except AgentRunError as e:
        # Known agent failure (LLM output invalid, missing key, etc.)
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        # Unknown failure (network, groq downtime, coding bug, etc.)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
