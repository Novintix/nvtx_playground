from pydantic import BaseModel
from typing import Dict, List, Optional, Literal


class SymptomInput(BaseModel):
    user_input: str
    previous_notes: Optional[Dict[str, str]] = None


class FollowUpQuestion(BaseModel):
    answer_key: str          # ✅ stable key for frontend/CLI
    question: str
    reason: str


class ClinicalNotes(BaseModel):
    triage_summary: str
    red_flags: str
    confidence: Literal["low", "medium", "high"]


class SymptomAgentResponse(BaseModel):
    identified_symptoms: List[str]
    follow_up_questions: List[FollowUpQuestion]
    clinical_notes: ClinicalNotes
    ready_for_next_agent: bool
