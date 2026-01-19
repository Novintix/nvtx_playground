from .agent import symptom_interpretation_agent
from .schema import SymptomAgentResponse


async def run_symptom_agent(user_input: str, previous_notes: dict | None = None) -> SymptomAgentResponse:
    result = await symptom_interpretation_agent(user_input, previous_notes)
    return SymptomAgentResponse(**result)
