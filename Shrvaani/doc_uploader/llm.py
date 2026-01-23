import os
import json
import re
from typing import Tuple

from langchain_groq import ChatGroq
from prompts import CLASSIFY_RESUME_PROMPT


llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.0,
)


def extract_json_anyhow(text: str) -> dict:
    """
    Extract JSON object from ANY messy Groq response.
    """
    if not text:
        raise ValueError("Empty LLM response")

    # try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # strip markdown ```json ... ```
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    # extract first {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response:\n{text}")

    json_str = match.group(0).strip()

    return json.loads(json_str)


def llm_classify_resume(resume_text: str) -> Tuple[str, float, str]:
    prompt = CLASSIFY_RESUME_PROMPT.format(resume_text=resume_text[:12000])

    resp = llm.invoke(prompt)
    raw = (resp.content or "").strip()

    print("\n================== GROQ RAW OUTPUT ==================")
    print(raw)
    print("====================================================\n")

    data = extract_json_anyhow(raw)

    category = str(data.get("category", "TECHNICAL")).upper().strip()
    confidence = float(data.get("confidence", 0.75))
    reason = str(data.get("reason", "Classified by LLM")).strip()

    if category not in ["TECHNICAL", "HR"]:
        category = "TECHNICAL"
        confidence = min(confidence, 0.60)
        reason = "Invalid category from LLM, default TECHNICAL"

    return category, confidence, reason
