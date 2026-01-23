from pydantic import BaseModel
from typing import Dict


class StartTriageRequest(BaseModel):
    user_input: str


class ContinueTriageRequest(BaseModel):
    session_id: str
    answers: Dict[str, str]
