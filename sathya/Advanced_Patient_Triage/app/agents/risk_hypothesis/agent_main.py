from .agent import risk_hypothesis_agent
from .schema import RiskHypothesisOutput


class RiskAgentRunError(RuntimeError):
    pass


async def run_risk_agent(identified_symptoms: list, clinical_notes: dict) -> RiskHypothesisOutput:
    try:
        raw = await risk_hypothesis_agent(identified_symptoms, clinical_notes)
        return RiskHypothesisOutput(**raw)
    except Exception as e:
        raise RiskAgentRunError(f"Risk agent failed: {str(e)}") from e
