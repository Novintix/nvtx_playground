import json
import httpx
from app.config.settings import settings
from .prompt import SYSTEM_PROMPT

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _safe_json(text: str) -> dict:
    """
    Strict JSON parse with fallback extraction.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


async def risk_hypothesis_agent(identified_symptoms: list, clinical_notes: dict) -> dict:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing")

    user_payload = {
        "identified_symptoms": identified_symptoms,
        "clinical_notes": clinical_notes,
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": 0,
        "top_p": 0.9,
    }

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GROQ_URL, json=payload, headers=headers)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]

    return _safe_json(content)
