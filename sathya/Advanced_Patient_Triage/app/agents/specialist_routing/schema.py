from pydantic import BaseModel
from typing import Dict, Any, List, Literal


class SpecialistRoutingInput(BaseModel):
    identified_symptoms: List[str]
    clinical_notes: Dict[str, Any]
    risk_hypothesis: Dict[str, Any]   # Agent 2 output
    risk_scoring: Dict[str, Any]      # Agent 3 output


Specialty = Literal[
    "general_practice",
    "emergency_medicine",
    "cardiology",
    "neurology",
    "gastroenterology",
    "orthopedics",
    "pulmonology",
    "psychiatry",
    "obgyn",
    "urology",
    "dermatology"
]

Urgency = Literal["routine", "urgent", "emergency"]

CareSetting = Literal["self_care", "routine_clinic", "urgent_care", "emergency_er"]


class SpecialistRoutingOutput(BaseModel):
    specialty: Specialty
    urgency: Urgency
    recommended_care_setting: CareSetting
    routing_reasons: List[str]
    handoff_note: str
