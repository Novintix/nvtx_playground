from typing import Dict, Any
from pydantic import BaseModel


class StartTriageRequest(BaseModel):
    user_input: str




class ContinueTriageRequest(BaseModel):
    session_id: str
    answers: Dict[str, Any]



# (Optional) if you use this anywhere else
class TriageResponse(BaseModel):
    session_id: str
    passed_to_agent2: bool
    agent_output: Dict[str, Any]
