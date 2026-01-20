import os
import json
import re
import httpx
from dotenv import load_dotenv
from .prompt import SYSTEM_PROMPT

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _extract_json(text: str) -> dict:
    """
    Groq will usually return clean JSON if prompted.
    This is a safety fallback: if it returns extra text, we pull the first JSON object.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


async def symptom_interpretation_agent(user_input: str, previous_notes: dict | None = None) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing in .env")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Patient input:\n{user_input}\n\n"
                f"Previous notes (may be null):\n{json.dumps(previous_notes or {}, ensure_ascii=False)}\n"
            ),
        },
    ]

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GROQ_URL, json=payload, headers=headers)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]

    return _extract_json(content)
