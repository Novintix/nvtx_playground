from fastapi import FastAPI
from app.agents.symptom_interpretation.schema import SymptomInput
from app.agents.symptom_interpretation.agent_main import run_symptom_agent

app = FastAPI(title="Advanced Patient Triage")

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/symptom")
async def interpret_symptom(data: SymptomInput):
    result = await run_symptom_agent(data.user_input, data.previous_notes)
    return result
