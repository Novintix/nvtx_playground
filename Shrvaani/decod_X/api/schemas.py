from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str


class AgentResponse(BaseModel):
    analysis: str
    comparison: str
    policy_impact: str
    recommendations: str
    final_answer: str
