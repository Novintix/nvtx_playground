"""
agent_main.py

Purpose:
- This file acts as the "entry point" for the Symptom Interpretation Agent.
- It calls the LLM-backed agent (agent.py), parses/validates output,
  and returns a Pydantic model to the API layer (FastAPI).

Why this is important:
- Keeps FastAPI routes clean (routes should not contain AI parsing logic)
- Ensures every response is schema-validated (guardrail)
"""

from typing import Optional, Dict, Any

from .agent import symptom_interpretation_agent
from .schema import SymptomAgentResponse


class AgentRunError(RuntimeError):
    """Raised when the agent fails to produce valid output after validation."""


async def run_symptom_agent(
    user_input: str,
    previous_notes: Optional[Dict[str, str]] = None
) -> SymptomAgentResponse:
    """
    Runs the Symptom Interpretation Agent end-to-end.

    Args:
        user_input: Raw symptom description from the patient/user.
        previous_notes: Optional notes from earlier turns (multi-turn support).

    Returns:
        SymptomAgentResponse: Validated structured output.

    Raises:
        AgentRunError: If the agent output is invalid or schema validation fails.
    """

    try:
        # 1) Call the LLM-backed agent (async HTTP call to Groq)
        raw_result: Dict[str, Any] = await symptom_interpretation_agent(
            user_input=user_input,
            previous_notes=previous_notes
        )

        # 2) Pydantic validation (hard guardrail)
        #    If fields/types are wrong, this throws a ValidationError.
        validated = SymptomAgentResponse(**raw_result)

        # 3) Additional business-rule enforcement:
        #    If follow-up questions exist, agent cannot be "ready".
        if validated.follow_up_questions and validated.ready_for_next_agent is True:
            validated.ready_for_next_agent = False

        return validated

    except Exception as e:
        # Make sure we surface a clean error to FastAPI layer
        # (so you can return a 500 with clear message)
        raise AgentRunError(f"Symptom agent failed: {str(e)}") from e
