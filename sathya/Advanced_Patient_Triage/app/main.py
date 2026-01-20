from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.agents.symptom_interpretation.schema import SymptomInput
from app.agents.symptom_interpretation.agent_main import run_symptom_agent, AgentRunError
from app.schemas.triage_schema import StartTriageRequest, ContinueTriageRequest
from app.services.session_service import create_session, get_session, update_session
from app.agents.symptom_interpretation.agent_main import run_symptom_agent


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
    
@app.post("/triage/start")
async def triage_start(payload: StartTriageRequest):
    # create a new Mongo session
    session_id = await create_session()

    # run agent first time
    result = await run_symptom_agent(payload.user_input, previous_notes={})

    # store encrypted notes (only clinical_notes)
    notes = result.clinical_notes.model_dump()

    await update_session(
        session_id=session_id,
        notes=notes,
        history_item={
            "type": "start",
            "user_input": payload.user_input,
            "agent_output": result.model_dump()
        }
    )

    return {
        "session_id": session_id,
        "agent_output": result.model_dump()
    }


@app.post("/triage/continue")
async def triage_continue(payload: ContinueTriageRequest):
    session = await get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid session_id")

    notes = session["notes"]

    # merge user answers into notes
    for k, v in payload.answers.items():
        notes[k] = v

    # run agent again with extra info + previous notes
    result = await run_symptom_agent(
        user_input=f"Additional patient answers: {payload.answers}",
        previous_notes=notes
    )

    # update notes with latest agent notes
    notes = result.clinical_notes.model_dump()

    await update_session(
        session_id=payload.session_id,
        notes=notes,
        history_item={
            "type": "continue",
            "answers": payload.answers,
            "agent_output": result.model_dump()
        }
    )

    return {
        "session_id": payload.session_id,
        "agent_output": result.model_dump()
    }
