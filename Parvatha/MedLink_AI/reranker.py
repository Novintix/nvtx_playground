# reranker.py
from datetime import datetime
from typing import List, Dict
from config import WEIGHTS


CURRENT_YEAR = datetime.now().year


def normalize(values: List[float]) -> List[float]:
    """
    Min-max normalization to [0, 1]
    """
    if not values:
        return []

    min_v, max_v = min(values), max(values)
    if min_v == max_v:
        return [1.0 for _ in values]

    return [(v - min_v) / (max_v - min_v) for v in values]


def journal_score(journal_name: str) -> float:
    """
    Simple heuristic journal ranking
    """
    top_journals = [
        "Nature",
        "The Lancet",
        "New England Journal of Medicine",
        "JAMA",
        "BMJ"
    ]

    for j in top_journals:
        if j.lower() in journal_name.lower():
            return 1.0

    return 0.4  # default neutral score


def recency_score(year: int) -> float:
    """
    More recent papers score higher
    """
    if not year or year <= 0:
        return 0.0

    age = CURRENT_YEAR - year
    return max(0.0, 1.0 - age / 20)  # papers older than ~20 years decay to 0


def rerank(
    papers: List[Dict],
    distances: List[float]
) -> List[Dict]:
    """
    Re-rank papers using weighted scoring
    """

    # --- Normalize semantic relevance (lower distance = better) ---
    relevance_raw = [1 / (d + 1e-6) for d in distances]
    relevance_norm = normalize(relevance_raw)

    # --- Citations (may be missing → safe default 0) ---
    citation_raw = [p.get("citations", 0) for p in papers]
    citation_norm = normalize(citation_raw) if any(citation_raw) else [0.0] * len(papers)

    # --- Recency ---
    recency_raw = [recency_score(p.get("year", 0)) for p in papers]

    # --- Journal quality ---
    journal_raw = [journal_score(p.get("journal", "")) for p in papers]

    reranked = []

    for i, paper in enumerate(papers):
        final_score = (
            WEIGHTS["relevance"] * relevance_norm[i] +
            WEIGHTS["citations"] * citation_norm[i] +
            WEIGHTS["recency"] * recency_raw[i] +
            WEIGHTS["journal"] * journal_raw[i]
        )

        paper_copy = paper.copy()
        paper_copy["final_score"] = round(final_score, 4)
        paper_copy["score_breakdown"] = {
            "relevance": round(relevance_norm[i], 3),
            "citations": round(citation_norm[i], 3),
            "recency": round(recency_raw[i], 3),
            "journal": round(journal_raw[i], 3)
        }

        reranked.append(paper_copy)

    reranked.sort(key=lambda x: x["final_score"], reverse=True)
    return reranked
