from .schema import SpecialistRoutingInput, SpecialistRoutingOutput
from .agent import specialist_routing_agent


class AgentRunError(Exception):
    pass


async def run_specialist_routing_agent(
    identified_symptoms,
    clinical_notes,
    risk_hypothesis,
    risk_scoring,
) -> SpecialistRoutingOutput:
    try:
        inp = SpecialistRoutingInput(
            identified_symptoms=identified_symptoms,
            clinical_notes=clinical_notes,
            risk_hypothesis=risk_hypothesis,
            risk_scoring=risk_scoring,
        )

        raw = await specialist_routing_agent(inp.model_dump())
        return SpecialistRoutingOutput(**raw)

    except Exception as e:
        raise AgentRunError(f"Specialist routing agent failed: {str(e)}")
