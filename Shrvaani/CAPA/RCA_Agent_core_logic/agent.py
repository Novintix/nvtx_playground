# agent.py

from data import (
    HISTORICAL_CAUSE_FREQUENCY,
    TOTAL_CAPA_CASES,
    DEVICE_LOGS,
    LOG_EVIDENCE_MAP,
    FIVE_WHY_CHAINS
)
from embedding_mapper import map_cause_to_6m


def score_cause(cause: str, event_description: str):
    explanation = {}

    # 1. Historical frequency
    freq = HISTORICAL_CAUSE_FREQUENCY.get(cause, 0)
    freq_score = freq / TOTAL_CAPA_CASES
    explanation["historical_frequency"] = f"{freq} confirmed CAPAs"

    # 2. Log evidence
    hits = 0
    for keyword in LOG_EVIDENCE_MAP.get(cause, []):
        if any(keyword in log for log in DEVICE_LOGS):
            hits += 1

    evidence_score = min(hits * 0.4, 1.0)
    explanation["log_evidence"] = f"{hits} matching log signals"

    # 3. Penalty if no evidence
    penalty = 0.3 if hits == 0 else 0.0
    explanation["penalty"] = penalty

    # Final score
    final_score = (
        0.5 * freq_score + 0.5 * evidence_score - penalty
    )

    explanation["final_support_score"] = round(final_score, 3)

    return round(final_score, 3), explanation


def build_ranked_fishbone(causes, event_description):
    ranked = []

    for cause in causes:
        category, similarity = map_cause_to_6m(cause)
        score, why = score_cause(cause, event_description)
        
        # Add 5-Why if available
        five_why = FIVE_WHY_CHAINS.get(cause, ["No 5-Why chain available for this cause."])

        ranked.append({
            "cause": cause,
            "category": category,
            "support_score": score,
            "five_why": five_why,
            "why": {
                **why,
                "6M_mapping": similarity
            }
        })

    ranked.sort(key=lambda x: x["support_score"], reverse=True)
    return ranked
