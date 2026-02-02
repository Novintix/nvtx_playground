from typing import TypedDict, List

class ReasoningState(TypedDict):
    query: str
    financial_context: List[str]
    policy_context: List[str]
    analysis: str
    comparison: str
    policy_check: str
    recommendations: str
    final_answer: str
