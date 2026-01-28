"""
LLM handler module for generating responses.
Manages interaction with Gemini for answer generation.
"""

import google.generativeai as genai
from typing import List, Dict
from config import LLM_MODEL
from logger import setup_logger

logger = setup_logger(__name__)


class LLMHandler:
    """
    Handles LLM interactions for answer generation.
    """
    
    def __init__(self):
        """Initialize the LLM handler."""
        self.model = genai.GenerativeModel(LLM_MODEL)
        logger.info(f"LLMHandler initialized with model: {LLM_MODEL}")
    
    def generate_answer(self, query: str, context_chunks: List[Dict]) -> Dict:
        """
        Generate answer using retrieved context.
        
        Args:
            query: User query
            context_chunks: Retrieved and re-ranked chunks
        
        Returns:
            Dictionary with answer and metadata
        """
        try:
            logger.info(f"Generating answer for query: {query[:50]}...")
            
            # Build context from chunks
            context = self._build_context(context_chunks)
            
            # Create prompt
            prompt = self._create_prompt(query, context)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            result = {
                "answer": response.text,
                "query": query,
                "num_chunks_used": len(context_chunks),
                "sources": [
                    {
                        "chunk_id": chunk.get("chunk_id"),
                        "page_number": chunk.get("metadata", {}).get("page_number"),
                        "relevance_score": chunk.get("relevance_score", chunk.get("score"))
                    }
                    for chunk in context_chunks
                ]
            }
            
            logger.info("Answer generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}", exc_info=True)
            raise
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context string from chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            page_num = chunk.get("metadata", {}).get("page_number", "N/A")
            context_parts.append(
                f"[Source {i} - Page {page_num}]\n{chunk['text']}\n"
            )
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create prompt for LLM."""
        return f"""You are a helpful AI assistant. Answer the question based on the provided context.

CONTEXT:
{context}

QUESTION: {query}

INSTRUCTIONS:
- Provide a clear, accurate answer based on the context
- If the answer is not in the context, say "I could not find the answer in the provided documents"
- Cite source numbers when referencing specific information
- Be concise but comprehensive

ANSWER:"""
