# reranker.py
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np

from config import WEIGHTS, RERANKER_MODEL
from error_handler import log_info, log_warning

# Cross-encoder for precise relevance scoring
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    log_warning("⚠️ sentence-transformers not installed. Cross-encoder disabled.")

CURRENT_YEAR = datetime.now().year


class EvidenceReranker:
    """Multi-stage re-ranking with cross-encoder validation"""
    
    def __init__(self):
        self.cross_encoder = None
        
        if CROSS_ENCODER_AVAILABLE:
            try:
                log_info(f"🔄 Loading cross-encoder: {RERANKER_MODEL}...")
                self.cross_encoder = CrossEncoder(RERANKER_MODEL)
                log_info("✅ Cross-encoder loaded")
            except Exception as e:
                log_warning(f"⚠️ Failed to load cross-encoder: {e}")
    
    def rerank(
        self,
        query: str,
        papers: List[Dict],
        bi_encoder_scores: List[float]
    ) -> Tuple[List[Dict], float]:
        """
        Re-rank papers using multiple signals
        Returns: (ranked_papers, aggregate_confidence)
        """
        
        if not papers:
            return [], 0.0
        
        if len(papers) != len(bi_encoder_scores):
            log_warning(f"Mismatch: {len(papers)} papers vs {len(bi_encoder_scores)} scores")
            bi_encoder_scores = bi_encoder_scores[:len(papers)] + [0.5] * (len(papers) - len(bi_encoder_scores))
        
        # Stage 1: Cross-encoder scoring (if available)
        cross_scores = self._cross_encoder_score(query, papers)
        
        # Stage 2: Feature engineering
        features = self._extract_features(papers)
        
        # Stage 3: Weighted combination
        reranked = []
        for i, paper in enumerate(papers):
            # Normalize bi-encoder score (already similarity)
            bi_score = bi_encoder_scores[i]
            
            # Cross-encoder score (0-1 relevance)
            ce_score = cross_scores[i] if cross_scores else 0.5
            
            # Combine scores
            final_score = (
                WEIGHTS["relevance"] * bi_score +
                WEIGHTS["cross_encoder"] * ce_score +
                WEIGHTS["citations"] * features["citations"][i] +
                WEIGHTS["recency"] * features["recency"][i] +
                WEIGHTS["journal"] * features["journal"][i]
            )
            
            paper_copy = paper.copy()
            paper_copy["final_score"] = round(final_score, 4)
            paper_copy["score_breakdown"] = {
                "bi_encoder": round(bi_score, 3),
                "cross_encoder": round(ce_score, 3),
                "citations": round(features["citations"][i], 3),
                "recency": round(features["recency"][i], 3),
                "journal": round(features["journal"][i], 3)
            }
            
            reranked.append(paper_copy)
        
        # Sort by final score
        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Calculate aggregate confidence
        aggregate_confidence = self._calculate_aggregate_confidence(reranked, cross_scores)
        
        log_info(f"✅ Re-ranked {len(reranked)} papers (confidence: {aggregate_confidence:.3f})")
        
        return reranked, aggregate_confidence
    
    def _cross_encoder_score(self, query: str, papers: List[Dict]) -> Optional[List[float]]:
        """Score papers using cross-encoder (more accurate than bi-encoder)"""
        if not self.cross_encoder:
            return None
        
        try:
            # Prepare query-document pairs
            pairs = []
            for paper in papers:
                # Combine title and abstract for better matching
                text = f"{paper.get('title', '')} {paper.get('abstract', '')}"[:512]
                pairs.append((query, text))
            
            # Get relevance scores
            scores = self.cross_encoder.predict(pairs, batch_size=8)
            
            # Normalize to 0-1 (cross-encoder outputs raw logits/scores)
            scores = 1 / (1 + np.exp(-scores))  # Sigmoid normalization
            
            return scores.tolist()
            
        except Exception as e:
            log_warning(f"Cross-encoder scoring failed: {e}")
            return None
    
    def _extract_features(self, papers: List[Dict]) -> Dict[str, List[float]]:
        """Extract normalized features for each paper"""
        
        # Citation scores
        citations_raw = [self._citation_score(p.get("citations", 0)) for p in papers]
        citations_norm = self._normalize(citations_raw)
        
        # Recency scores
        recency_scores = [self._recency_score(p.get("year", 0)) for p in papers]
        
        # Journal quality scores
        journal_scores = [self._journal_score(p.get("journal", "")) for p in papers]
        
        return {
            "citations": citations_norm,
            "recency": recency_scores,
            "journal": journal_scores
        }
    
    def _citation_score(self, citations: int) -> float:
        """Log-scaled citation score"""
        if citations <= 0:
            return 0.0
        return min(1.0, np.log10(citations + 1) / 4.0)
    
    def _recency_score(self, year: int) -> float:
        """Recency scoring with smooth decay"""
        if not year or year <= 0:
            return 0.0
        
        age = CURRENT_YEAR - year
        
        if age < 0:
            return 0.0
        elif age <= 2:
            return 1.0
        elif age <= 5:
            return 0.8
        elif age <= 10:
            return 0.6
        elif age <= 20:
            return 0.3
        else:
            return 0.1
    
    def _journal_score(self, journal_name: str) -> float:
        """Journal quality tier scoring"""
        if not journal_name:
            return 0.3
        
        journal_lower = journal_name.lower()
        
        # Tier 1: Top-tier journals
        tier1 = [
            "nature", "science", "cell", "lancet",
            "new england journal of medicine", "nejm",
            "jama", "bmj", "nature medicine", "cell metabolism"
        ]
        
        # Tier 2: High-impact specialized
        tier2 = [
            "plos medicine", "immunity", "journal of clinical investigation",
            "circulation", "diabetes care", "cancer research",
            "journal of the american college of cardiology"
        ]
        
        # Tier 3: Good quality
        tier3 = [
            "frontiers in", "scientific reports",
            "international journal of", "european journal of",
            "bmc", "plos one"
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
        
        return 0.4  # Unknown journal
    
    def _normalize(self, values: List[float]) -> List[float]:
        """Min-max normalization"""
        if not values:
            return []
        
        if len(values) == 1:
            return [1.0]
        
        min_v, max_v = min(values), max(values)
        
        if abs(max_v - min_v) < 1e-9:
            return [1.0 for _ in values]
        
        return [(v - min_v) / (max_v - min_v) for v in values]
    
    def _calculate_aggregate_confidence(
        self,
        ranked_papers: List[Dict],
        cross_scores: Optional[List[float]]
    ) -> float:
        """Calculate overall confidence in the retrieved evidence"""
        
        if not ranked_papers:
            return 0.0
        
        # Top score (quality of best match)
        top_score = ranked_papers[0]["final_score"]
        
        # Score spread (discrimination between papers)
        if len(ranked_papers) > 1:
            score_spread = ranked_papers[0]["final_score"] - ranked_papers[-1]["final_score"]
        else:
            score_spread = 0
        
        # Cross-encoder agreement (if available)
        ce_agreement = 0.5
        if cross_scores and len(cross_scores) == len(ranked_papers):
            # Check if bi-encoder and cross-encoder agree on top paper
            bi_top_idx = 0  # Already sorted by bi-encoder initially
            ce_top_idx = np.argmax(cross_scores)
            agreement = 1.0 if bi_top_idx == ce_top_idx else 0.5
            
            # Average cross-encoder confidence
            ce_confidence = np.mean(cross_scores)
            ce_agreement = 0.5 * agreement + 0.5 * ce_confidence
        
        # Combine
        confidence = 0.4 * top_score + 0.3 * score_spread + 0.3 * ce_agreement
        
        return min(confidence, 1.0)
    
    def detect_contradictions(self, papers: List[Dict]) -> List[Dict]:
        """
        Simple contradiction detection based on sentiment/opposing claims
        Note: This is a simplified version - full implementation would use LLM
        """
        contradictions = []
        
        # Look for opposing keywords in abstracts
        opposing_pairs = [
            ("increases", "decreases"),
            ("promotes", "inhibits"),
            ("activates", "suppresses"),
            ("beneficial", "harmful"),
            ("positive", "negative")
        ]
        
        for i, p1 in enumerate(papers):
            for j, p2 in enumerate(papers[i+1:], i+1):
                abs1 = p1.get("abstract", "").lower()
                abs2 = p2.get("abstract", "").lower()
                
                for term1, term2 in opposing_pairs:
                    if term1 in abs1 and term2 in abs2:
                        contradictions.append({
                            "paper1": p1.get("pmid"),
                            "paper2": p2.get("pmid"),
                            "type": f"{term1} vs {term2}",
                            "description": f"Paper {p1.get('pmid')} suggests {term1} while Paper {p2.get('pmid')} suggests {term2}"
                        })
                    elif term2 in abs1 and term1 in abs2:
                        contradictions.append({
                            "paper1": p1.get("pmid"),
                            "paper2": p2.get("pmid"),
                            "type": f"{term2} vs {term1}",
                            "description": f"Paper {p1.get('pmid')} suggests {term2} while Paper {p2.get('pmid')} suggests {term1}"
                        })
        
        return contradictions


# Backward compatibility - keep old function signature
def rerank(papers: List[Dict], distances: List[float]) -> List[Dict]:
    """Legacy re-ranking function (without cross-encoder)"""
    reranker = EvidenceReranker()
    # Convert distances to similarities (inverse)
    similarities = [1.0 / (d + 1e-6) for d in distances]
    similarities = reranker._normalize(similarities)
    
    # Use a dummy query (won't be used for cross-encoder in legacy mode)
    ranked, _ = reranker.rerank("", papers, similarities)
    return ranked
 