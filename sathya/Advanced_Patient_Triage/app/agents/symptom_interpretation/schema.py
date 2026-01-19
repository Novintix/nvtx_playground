from pydantic import BaseModel
from typing import Dict, List, Optional


class SymptomInput(BaseModel):
    user_input: str
    previous_notes: Optional[Dict[str, str]] = None


class FollowUpQuestion(BaseModel):
    question: str
    reason: str


class SymptomAgentResponse(BaseModel):
    identified_symptoms: List[str]
    follow_up_questions: List[FollowUpQuestion]
    clinical_notes: Dict[str, str]
    ready_for_next_agent: bool
