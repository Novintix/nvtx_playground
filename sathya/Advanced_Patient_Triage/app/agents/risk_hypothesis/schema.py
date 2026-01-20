from pydantic import BaseModel
from typing import List, Literal, Dict, Any


class RiskHypothesisInput(BaseModel):
    identified_symptoms: List[str]
    clinical_notes: Dict[str, Any]


class RiskHypothesisOutput(BaseModel):
    risk_level: Literal["low", "medium", "high", "critical"]
    risk_reasons: List[str]
    red_flags: List[str]
    triage_action: Literal["self_care", "routine_clinic", "urgent_care", "emergency_er"]
    confidence: Literal["low", "medium", "high"]
    handoff_summary: str
