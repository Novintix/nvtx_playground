from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional


class SBAR(BaseModel):
    situation: str = Field(..., description="One-liner of why escalation is happening now")
    background: str = Field(..., description="Short relevant background from notes")
    assessment: str = Field(..., description="Risk assessment summary (no diagnosis)")
    recommendation: str = Field(..., description="Next steps for clinician/human escalation")


class HumanEscalationInput(BaseModel):
    session_id: Optional[str] = None
    identified_symptoms: List[str]
    clinical_notes: Dict[str, Any]
    risk_hypothesis: Dict[str, Any]     # Agent 2 output dict
    risk_scoring: Dict[str, Any]        # Agent 3 output dict
    routing_hint: Optional[Dict[str, Any]] = None  # Agent 4 output dict (optional)


class HumanEscalationOutput(BaseModel):
    escalation_level: Literal["STAT", "URGENT"]
    escalation_reasons: List[str]
    safety_flags: List[str]
    missing_info: List[str]

    # Non-diagnostic immediate guidance (no meds)
    immediate_actions: List[str]

    # Clinician-ready handoff
    sbar: SBAR
    clinician_message: str
