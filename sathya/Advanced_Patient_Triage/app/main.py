from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.agents.symptom_interpretation.schema import SymptomInput
from app.agents.symptom_interpretation.agent_main import run_symptom_agent, AgentRunError

from app.schemas.triage_schema import StartTriageRequest, ContinueTriageRequest
from app.services.session_service import create_session, get_session, update_session

from app.agents.risk_hypothesis.agent_main import run_risk_agent
from app.services.question_policy import enforce_followup_policy
from app.services.notes_postprocess import patch_triage_summary  
from app.agents.risk_scoring_safety.agent_main import run_risk_scoring_agent

app = FastAPI(title="Advanced Patient Triage")

# Hard limits to prevent loops
MAX_QUESTIONS_PER_TURN = 5
MAX_CLARIFICATION_ROUNDS = 3


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

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": result.model_dump()
            }
        )

    except AgentRunError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/triage/start")
async def triage_start(payload: StartTriageRequest):
    """
    Starts a new triage session:
    - Creates Mongo session
    - Runs Agent 1
    - Applies follow-up policy: max questions + dedupe
    - Stores notes + history
    """
    session_id = await create_session()

    try:
        # Run agent first time
        result = await run_symptom_agent(payload.user_input, previous_notes={})

        # Notes start from agent clinical notes
        notes = result.clinical_notes.model_dump()

        # ✅ Patch summary for consistency
        notes = patch_triage_summary(notes)

        # Initialize policy tracking fields
        notes["_round_count"] = 1
        notes["_asked_keys"] = []

        # Enforce policy on follow-up questions
        raw_followups = [q.model_dump() for q in result.follow_up_questions]
        filtered_followups, notes = enforce_followup_policy(
            followups=raw_followups,
            notes=notes,
            max_questions=MAX_QUESTIONS_PER_TURN
        )

        # Build output payload (override followups)
        agent1_output = result.model_dump()
        agent1_output["follow_up_questions"] = filtered_followups
        agent1_output["ready_for_next_agent"] = (len(filtered_followups) == 0)

        # ✅ Also patch the outgoing summary (same as stored)
        agent1_output["clinical_notes"] = patch_triage_summary(agent1_output["clinical_notes"])

        # Save session state
        await update_session(
            session_id=session_id,
            notes=notes,
            history_item={
                "type": "start",
                "user_input": payload.user_input,
                "agent_output": agent1_output
            }
        )

        return {
            "session_id": session_id,
            "passed_to_agent2": False,
            "agent_output": agent1_output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage start failed: {str(e)}")


@app.post("/triage/continue")
async def triage_continue(payload: ContinueTriageRequest):
    """
    Continues an existing triage session:
    - Loads session from Mongo
    - Merges user answers into notes
    - Runs Agent 1 again
    - Enforces follow-up policy (max 5, dedupe, no repeats)
    - Forces pass to Agent 2 after MAX_CLARIFICATION_ROUNDS
    - If ready -> runs Agent 2 and returns both
    """
    session = await get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid session_id")

    # Load decrypted notes (includes previous answers + tracking)
    notes = session["notes"]

    # ✅ Merge new user answers into notes, normalize whitespace
    for k, v in payload.answers.items():
        if isinstance(v, str):
            notes[k] = " ".join(v.split())
        else:
            notes[k] = v

    try:
        # Run Agent 1 again using previous_notes (contains answers)
        result = await run_symptom_agent(
            user_input=f"Additional patient answers: {payload.answers}",
            previous_notes=notes
        )

        # ✅ IMPORTANT: keep previous answers, then overlay agent clinical_notes
        clinical_notes = dict(notes)  # keeps duration, severity, etc.
        agent_notes = result.clinical_notes.model_dump()
        clinical_notes.update(agent_notes)

        # ✅ Patch summary so it never contradicts structured fields
        clinical_notes = patch_triage_summary(clinical_notes)

        # Preserve internal tracking fields from session notes
        prev_round_count = int(notes.get("_round_count", 0))
        prev_asked_keys = notes.get("_asked_keys", [])

        # Increment round count
        round_count = prev_round_count + 1

        # Update tracking fields
        clinical_notes["_round_count"] = round_count
        clinical_notes["_asked_keys"] = prev_asked_keys

        # Enforce follow-up policy (dedupe + max questions + avoid already asked keys)
        raw_followups = [q.model_dump() for q in result.follow_up_questions]
        filtered_followups, clinical_notes = enforce_followup_policy(
            followups=raw_followups,
            notes=clinical_notes,
            max_questions=MAX_QUESTIONS_PER_TURN
        )

        # Build output payload (override followups)
        agent1_output = result.model_dump()
        agent1_output["follow_up_questions"] = filtered_followups

        # ✅ Patch outgoing clinical summary too
        agent1_output["clinical_notes"] = patch_triage_summary(agent1_output["clinical_notes"])

        # Decide if we should proceed
        force_proceed = round_count >= MAX_CLARIFICATION_ROUNDS
        if force_proceed:
            agent1_output["ready_for_next_agent"] = True
            agent1_output["follow_up_questions"] = []
            agent1_output["clinical_notes"]["triage_summary"] += (
                f" | Note: Max clarification rounds reached ({MAX_CLARIFICATION_ROUNDS}). "
                "Proceeding with available info."
            )
        else:
            agent1_output["ready_for_next_agent"] = (len(filtered_followups) == 0)

        # Store updated notes + agent1 history
        await update_session(
            session_id=payload.session_id,
            notes=clinical_notes,
            history_item={
                "type": "continue",
                "answers": payload.answers,
                "agent_output": agent1_output
            }
        )

        # If intake complete (or forced), call Agent 2
        if agent1_output["ready_for_next_agent"] is True:
            # ✅ Pass full merged notes (includes answers like duration="2 years")
            full_notes_for_agent2 = dict(clinical_notes)

            # Remove internal tracking fields
            full_notes_for_agent2.pop("_round_count", None)
            full_notes_for_agent2.pop("_asked_keys", None)

            risk = await run_risk_agent(
                identified_symptoms=agent1_output["identified_symptoms"],
                clinical_notes=full_notes_for_agent2
            )

            # ✅ Agent 3: Risk Scoring & Safety (config-driven)
            risk_data = risk.model_dump()
            risk_scoring = await run_risk_scoring_agent(
                risk_output=risk_data,
                clinical_notes=full_notes_for_agent2
            )

            # Store risk + agent3 output
            await update_session(
                session_id=payload.session_id,
                notes=clinical_notes,
                history_item={
                    "type": "risk_agent",
                    "risk_output": risk_data,
                    "risk_scoring_output": risk_scoring.model_dump()
                }
            )

            return {
                "session_id": payload.session_id,
                "passed_to_agent2": True,
                "symptom_agent": agent1_output,
                "risk_agent": risk_data,
                "risk_scoring_agent": risk_scoring.model_dump(),
                "next_step": "human_escalation" if risk_scoring.risk_level == "HIGH" else "specialist_routing"
            }

        # Otherwise keep looping Agent 1
        return {
            "session_id": payload.session_id,
            "passed_to_agent2": False,
            "agent_output": agent1_output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage continue failed: {str(e)}")
