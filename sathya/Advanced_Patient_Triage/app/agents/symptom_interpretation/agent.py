import os
import json
import re
from typing import Any, Dict, Optional, List

import httpx
from dotenv import load_dotenv

from .prompt import SYSTEM_PROMPT

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Prefer smaller model by default (change in .env if you want 70b)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Hard guardrails: required keys and basic type expectations
REQUIRED_KEYS = {
    "identified_symptoms": list,
    "follow_up_questions": list,
    "clinical_notes": dict,
    "ready_for_next_agent": bool,
}


class AgentOutputError(RuntimeError):
    """Raised when LLM output cannot be validated into the required schema."""


def _safe_json_extract(text: str) -> Dict[str, Any]:
    """
    More defensive JSON extraction:
    1) Try parse whole text as JSON
    2) If fails, find the FIRST top-level JSON object and parse it

    This reduces risk compared to greedy {.*} matching.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Find first '{' and last '}' and try minimal extraction.
        # Still not perfect, but better than greedy regex.
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def _validate_output(data: Dict[str, Any]) -> None:
    """
    Validate the agent output has required keys and correct types.
    We keep it strict to reduce silent failures.
    """
    for key, expected_type in REQUIRED_KEYS.items():
        if key not in data:
            raise AgentOutputError(f"Missing required key: {key}")
        if not isinstance(data[key], expected_type):
            raise AgentOutputError(
                f"Key '{key}' has wrong type. Expected {expected_type.__name__}, got {type(data[key]).__name__}"
            )

    # Validate follow_up_questions format if present
    for item in data["follow_up_questions"]:
        if not isinstance(item, dict):
            raise AgentOutputError("follow_up_questions items must be objects/dicts")
        if "question" not in item or "reason" not in item:
            raise AgentOutputError("Each follow_up_questions item must have 'question' and 'reason'")


def _build_messages(user_input: str, previous_notes: Optional[dict]) -> List[Dict[str, str]]:
    """
    Builds messages for the chat completion call.
    We enforce an internal step order by instructing the model to output only JSON.
    The 'steps' are internal and not shown to user; user sees only final JSON.
    """
    notes_json = json.dumps(previous_notes or {}, ensure_ascii=False)

    user_content = f"""
You MUST follow this execution order internally:
1) THINK: identify symptoms and missing details
2) ACT: (no external tools in this agent) extract structured fields
3) OBSERVE: ensure extracted fields are present and consistent
4) REASON: decide if clarification is needed and what to ask
5) RESPOND: output JSON ONLY (no extra text)

Patient input:
{user_input}

Previous notes:
{notes_json}
""".strip()

    return [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user", "content": user_content},
    ]


async def symptom_interpretation_agent(
    user_input: str,
    previous_notes: Optional[dict] = None,
    *,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    Guardrailed Symptom Interpretation Agent.

    Guarantees:
    - Always returns validated dict or raises a clear AgentOutputError
    - Output conforms to required schema keys/types
    - Deterministic settings by default
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing in .env")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = _build_messages(user_input, previous_notes)

    # deterministic
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0,
        # Optional: add top_p if you want more control.
        # Not all providers expose top_k; top_p is common.
        "top_p": 0.9,
    }

    last_error: Optional[Exception] = None

    async with httpx.AsyncClient(timeout=60) as client:
        for attempt in range(max_retries + 1):
            try:
                r = await client.post(GROQ_URL, json=payload, headers=headers)
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]

                data = _safe_json_extract(content)
                _validate_output(data)

                # Additional safety: if model says ready_for_next_agent=True but still asks questions, fix it.
                if data["follow_up_questions"] and data["ready_for_next_agent"] is True:
                    data["ready_for_next_agent"] = False

                return data

            except Exception as e:
                last_error = e
                # On retry, add a strict correction message to force valid JSON.
                payload["messages"].append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was invalid or not strictly valid JSON for the required schema. "
                            "Return ONLY valid JSON with keys: identified_symptoms, follow_up_questions, clinical_notes, ready_for_next_agent. "
                            "No markdown, no commentary."
                        ),
                    }
                )

    raise AgentOutputError(f"Failed to produce valid output after retries. Last error: {last_error}")
