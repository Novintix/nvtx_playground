from .schema import RiskScoringOutput
from .agent import risk_scoring_safety_agent


class RiskScoringError(Exception):
    pass


async def run_risk_scoring_agent(risk_output: dict, clinical_notes: dict) -> RiskScoringOutput:
    try:
        result = risk_scoring_safety_agent(
            risk_output=risk_output,
            clinical_notes=clinical_notes
        )
        return RiskScoringOutput(**result)
    except Exception as e:
        raise RiskScoringError(f"Risk scoring agent failed: {str(e)}") from e
