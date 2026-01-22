import re
from typing import List, Dict, Tuple, Any


def _norm(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text


def _snake_case(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def enforce_followup_policy(
    followups: List[Dict[str, Any]],
    notes: Dict[str, Any],
    max_questions: int = 5
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filters follow-up questions:
    ✅ removes duplicates by answer_key + question text
    ✅ removes keys already asked (stored in notes)
    ✅ enforces max_questions
    ✅ normalizes answer_key into snake_case (stability)
    ✅ preserves asked_keys order (no random set order)
    Updates notes['_asked_keys'].
    """

    # Keep asked keys as list for stable ordering
    asked_keys_list = notes.get("_asked_keys", [])
    if not isinstance(asked_keys_list, list):
        asked_keys_list = []

    asked_keys_set = set(asked_keys_list)
    seen_qtext = set()

    cleaned = []

    for q in followups:
        key = (q.get("answer_key") or "").strip()
        qtext = (q.get("question") or "").strip()
        reason = (q.get("reason") or "").strip()

        if not key or not qtext:
            continue

        # normalize key
        key = _snake_case(key)

        # reject bad keys
        if key in ["unknown", "unknown_key", ""]:
            continue

        # skip if already asked
        if key in asked_keys_set:
            continue

        ntext = _norm(qtext)
        if ntext in seen_qtext:
            continue

        seen_qtext.add(ntext)

        cleaned.append({
            "answer_key": key,
            "question": qtext,
            "reason": reason or "Needed for safe triage."
        })

        asked_keys_set.add(key)
        asked_keys_list.append(key)

        if len(cleaned) >= max_questions:
            break

    notes["_asked_keys"] = asked_keys_list
    return cleaned, notes
