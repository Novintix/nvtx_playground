from typing import Any, Dict
from .schema import HumanEscalationInput, HumanEscalationOutput
from .agent import human_escalation_agent


class AgentRunError(Exception):
    pass


async def run_human_escalation_agent(
    identified_symptoms: list[str],
    clinical_notes: Dict[str, Any],
    risk_hypothesis: Dict[str, Any],
    risk_scoring: Dict[str, Any],
    routing_hint: Dict[str, Any] | None = None,
    session_id: str | None = None,
) -> HumanEscalationOutput:
    """
    Calls Groq, validates JSON output with Pydantic, returns typed result.
    """
    inp = HumanEscalationInput(
        session_id=session_id,
        identified_symptoms=identified_symptoms,
        clinical_notes=clinical_notes,
        risk_hypothesis=risk_hypothesis,
        risk_scoring=risk_scoring,
        routing_hint=routing_hint,
    )

    try:
        raw = await human_escalation_agent(inp.model_dump())
        return HumanEscalationOutput(**raw)
    except Exception as e:
        raise AgentRunError(f"Human escalation agent failed: {str(e)}")
