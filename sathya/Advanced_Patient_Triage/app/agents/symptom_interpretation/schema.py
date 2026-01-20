from pydantic import BaseModel
from typing import Dict, List, Optional


# -------- Request Model (Postman sends this) --------
class SymptomInput(BaseModel):
    user_input: str
    previous_notes: Optional[Dict[str, str]] = None


# -------- Response Models (Agent returns this) --------
class FollowUpQuestion(BaseModel):
    question: str
    reason: str


class ClinicalNotes(BaseModel):
    triage_summary: str
    red_flags: str
    confidence: str  # "low" | "medium" | "high"


class SymptomAgentResponse(BaseModel):
    identified_symptoms: List[str]
    follow_up_questions: List[FollowUpQuestion]
    clinical_notes: ClinicalNotes
    ready_for_next_agent: bool
