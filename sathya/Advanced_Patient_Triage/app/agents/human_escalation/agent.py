import os
import json
import re
import httpx
from dotenv import load_dotenv
from .prompt import SYSTEM_PROMPT

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _extract_json(text: str) -> dict:
    """
    Groq should return JSON. This fallback extracts the first JSON object
    if extra text appears (should be rare if prompt is strict).
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


async def human_escalation_agent(payload: dict) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing in .env")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Create the escalation JSON using ONLY the input below.\n"
                "INPUT:\n"
                f"{json.dumps(payload, ensure_ascii=False)}"
            ),
        },
    ]

    req = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GROQ_URL, json=req, headers=headers)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]

    return _extract_json(content)
