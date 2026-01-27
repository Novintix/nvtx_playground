"""
Re-ranking module for refining retrieval results.
Uses cross-encoder approach with Gemini for better relevance scoring.
"""

from typing import List, Dict
import google.generativeai as genai
from config import LLM_MODEL, TOP_K_RERANK
from logger import setup_logger

logger = setup_logger(__name__)


class Reranker:
    """
    Re-ranks retrieved chunks based on query relevance.
    Improves precision of top-k results.
    """
    
    def __init__(self):
        """Initialize the reranker."""
        logger.info("Reranker initialized")
    
    def rerank(self, query: str, chunks: List[Dict], 
               top_k: int = TOP_K_RERANK) -> List[Dict]:
        """
        Re-rank chunks based on relevance to query.
        
        Args:
            query: User query
            chunks: Retrieved chunks from vector search
            top_k: Number of top results to return after re-ranking
        
        Returns:
            Re-ranked list of chunks
        
        Raises:
            Exception: If re-ranking fails
        """
        try:
            logger.info(f"Re-ranking {len(chunks)} chunks for query")
            
            if len(chunks) <= top_k:
                logger.debug("Chunk count <= top_k, returning all chunks")
                return chunks
            
            # Score each chunk
            scored_chunks = []
            for chunk in chunks:
                relevance_score = self._calculate_relevance(query, chunk["text"])
                chunk["relevance_score"] = relevance_score
                scored_chunks.append(chunk)
            
            # Sort by relevance score (higher is better)
            scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Return top-k
            reranked = scored_chunks[:top_k]
            
            logger.info(f"Re-ranking complete. Returning top {len(reranked)} chunks")
            return reranked
            
        except Exception as e:
            logger.error(f"Re-ranking failed: {str(e)}", exc_info=True)
            # Return original chunks if re-ranking fails
            logger.warning("Returning original chunks due to re-ranking failure")
            return chunks[:top_k]
    
    def _calculate_relevance(self, query: str, chunk_text: str) -> float:
        """
        Calculate relevance score between query and chunk.
        
        Args:
            query: User query
            chunk_text: Chunk text
        
        Returns:
            Relevance score (0-1)
        """
        try:
            prompt = f"""
Rate the relevance of the following text passage to the query on a scale of 0 to 1.
Return ONLY a number between 0 and 1, where:
- 0 = completely irrelevant
- 1 = highly relevant

Query: {query}

Passage: {chunk_text[:500]}

Relevance score:"""
            
            model = genai.GenerativeModel(LLM_MODEL)
            response = model.generate_content(prompt)
            
            # Extract score from response
            score_text = response.text.strip()
            score = float(score_text)
            
            # Clamp score between 0 and 1
            score = max(0.0, min(1.0, score))
            
            return score
            
        except Exception as e:
            logger.warning(f"Failed to calculate relevance score: {e}")
            # Return neutral score on failure
            return 0.5
