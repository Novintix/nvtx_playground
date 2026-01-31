# reranker.py
from datetime import datetime
from typing import List, Dict, Tuple
from config import WEIGHTS
from error_handler import log_info


CURRENT_YEAR = datetime.now().year


def normalize(values: List[float]) -> List[float]:
    """
    Min-max normalization to [0, 1]
    Handles edge cases (empty, single value, all same)
    """
    if not values:
        return []
    
    if len(values) == 1:
        return [1.0]
    
    min_v, max_v = min(values), max(values)
    
    if abs(max_v - min_v) < 1e-9:  # All values same
        return [1.0 for _ in values]
    
    return [(v - min_v) / (max_v - min_v) for v in values]


def journal_score(journal_name: str) -> float:
    """
    Enhanced journal ranking with tier system
    """
    if not journal_name:
        return 0.3
    
    journal_lower = journal_name.lower()
    
    # Tier 1: Top medical journals (1.0)
    tier1 = [
        "nature", "science", "cell", "lancet",
        "new england journal of medicine", "nejm",
        "jama", "bmj", "nature medicine"
    ]
    
    # Tier 2: High-impact specialized journals (0.8)
    tier2 = [
        "plos", "immunity", "journal of clinical",
        "circulation", "diabetes", "cancer research"
    ]
    
    # Tier 3: Good journals (0.6)
    tier3 = [
        "frontiers", "scientific reports",
        "international journal", "european journal"
    ]
    
    for journal in tier1:
        if journal in journal_lower:
            return 1.0
    
    for journal in tier2:
        if journal in journal_lower:
            return 0.8
    
    for journal in tier3:
        if journal in journal_lower:
            return 0.6
    
    return 0.4  # Default for unknown journals


def recency_score(year: int) -> float:
    """
    Recency scoring with smooth decay
    Recent papers (last 5 years) get high scores
    """
    if not year or year <= 0:
        return 0.0
    
    age = CURRENT_YEAR - year
    
    if age < 0:  # Future year (error)
        
        return 0.0
    elif age <= 2:  # Very recent
        return 1.0
    elif age <= 5:  # Recent
        return 0.8
    elif age <= 10:  # Moderately recent
        return 0.6
    elif age <= 20:  # Older
        return 0.3
    else:  # Very old
        return 0.1


def citation_score_enhanced(citations: int) -> float:
    """
    Enhanced citation scoring with logarithmic scaling
    """
    if citations <= 0:
        return 0.0
    
    # Logarithmic scaling (handles wide range of citation counts)
    import math
    return min(1.0, math.log10(citations + 1) / 4.0)  # Scales roughly to [0, 1]


def rerank(
    papers: List[Dict],
    distances: List[float]
) -> List[Dict]:
    """
    Enhanced multi-factor re-ranking with explainability
    
    Returns papers sorted by weighted score with breakdown
    """
    
    if not papers:
        return []
    
    if len(papers) != len(distances):
        log_info(f"⚠️ Papers ({len(papers)}) and distances ({len(distances)}) mismatch")
        distances = distances[:len(papers)] + [1.0] * (len(papers) - len(distances))
    
    # --- 1. Relevance Score (from FAISS distance) ---
    # Lower distance = higher relevance
    relevance_raw = [1.0 / (d + 1e-6) for d in distances]
    relevance_norm = normalize(relevance_raw)
    
    # --- 2. Citation Score ---
    citation_raw = [citation_score_enhanced(p.get("citations", 0)) for p in papers]
    citation_norm = normalize(citation_raw) if any(citation_raw) else [0.0] * len(papers)
    
    # --- 3. Recency Score ---
    recency_raw = [recency_score(p.get("year", 0)) for p in papers]
    
    # --- 4. Journal Quality Score ---
    journal_raw = [journal_score(p.get("journal", "")) for p in papers]
    
    # --- Combine Scores ---
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
    
    # Sort by final score (descending)
    reranked.sort(key=lambda x: x["final_score"], reverse=True)
    
    log_info(f"✅ Re-ranked {len(reranked)} papers")
    
    return reranked


def get_top_papers(papers: List[Dict], top_k: int = 5) -> List[Dict]:
    """Get top K papers after re-ranking"""
    return papers[:top_k]


def explain_ranking(paper: Dict) -> str:
    """Generate human-readable explanation of paper ranking"""
    
    if "score_breakdown" not in paper:
        return "No ranking information available"
    
    breakdown = paper["score_breakdown"]
    final = paper.get("final_score", 0)
    
    explanation = f"Overall Score: {final:.3f}\n"
    explanation += f"  - Relevance: {breakdown['relevance']:.3f} (40% weight)\n"
    explanation += f"  - Citations: {breakdown['citations']:.3f} (30% weight)\n"
    explanation += f"  - Recency: {breakdown['recency']:.3f} (20% weight)\n"
    explanation += f"  - Journal: {breakdown['journal']:.3f} (10% weight)\n"
    
    return explanation