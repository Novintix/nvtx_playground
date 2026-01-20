import re
from typing import List, Dict, Tuple

def _norm(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

def enforce_followup_policy(
    followups: List[Dict],
    notes: Dict,
    max_questions: int = 5
) -> Tuple[List[Dict], Dict]:
    """
    Filters follow-up questions:
    - removes duplicates by answer_key and question text
    - removes keys already asked (stored in notes)
    - enforces max_questions
    Updates notes['_asked_keys'].
    """
    asked_keys = set(notes.get("_asked_keys", []))
    seen_qtext = set()

    cleaned = []
    for q in followups:
        key = (q.get("answer_key") or "").strip()
        qtext = (q.get("question") or "").strip()
        reason = (q.get("reason") or "").strip()

        if not key or not qtext:
            continue

        # skip if already asked
        if key in asked_keys:
            continue

        ntext = _norm(qtext)
        if ntext in seen_qtext:
            continue

        seen_qtext.add(ntext)
        cleaned.append({"answer_key": key, "question": qtext, "reason": reason})
        asked_keys.add(key)

        if len(cleaned) >= max_questions:
            break

    notes["_asked_keys"] = list(asked_keys)
    return cleaned, notes
