from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal


class RiskScoringInput(BaseModel):
    risk_output: Dict[str, Any] = Field(..., description="Agent 2 output JSON")
    clinical_notes: Dict[str, Any] = Field(..., description="Merged notes from session + agent1 clinical notes")
    identified_symptoms: List[str] = Field(default_factory=list)


class RiskScoringOutput(BaseModel):
    risk_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    safety_flags: List[str]
