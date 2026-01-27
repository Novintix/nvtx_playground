"""
Advanced chunking module with semantic and context-aware strategies.
Implements intelligent chunking based on content structure and semantics.
"""

import numpy as np
from typing import List, Dict
import google.generativeai as genai
from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE,
    SEMANTIC_SIMILARITY_THRESHOLD, USE_SEMANTIC_CHUNKING,
    EMBED_MODEL
)
from logger import setup_logger

logger = setup_logger(__name__)


class AdvancedChunker:
    """
    Implements semantic and context-aware chunking strategies.
    Preserves document structure and semantic coherence.
    """
    
    def __init__(self):
        """Initialize the chunker."""
        logger.info("AdvancedChunker initialized with semantic chunking: "
                   f"{USE_SEMANTIC_CHUNKING}")
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text using the configured strategy.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            logger.info(f"Starting chunking process for text of length: {len(text)}")
            
            if USE_SEMANTIC_CHUNKING:
                chunks = self._semantic_chunking(text)
            else:
                chunks = self._context_aware_chunking(text)
            
            # Fallback: if no chunks created, create one chunk from entire text
            if not chunks and text.strip():
                logger.warning("No chunks created, using entire text as single chunk")
                chunks = [{
                    "text": text,
                    "token_count": len(text.split()),
                    "type": "fallback"
                }]
            
            # Attach metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk["chunk_id"] = i
                chunk["metadata"] = metadata or {}
            
            logger.info(f"Created {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Chunking failed: {str(e)}", exc_info=True)
            raise
    
    def _context_aware_chunking(self, text: str) -> List[Dict]:
        """
        Context-aware chunking that respects sentence boundaries.
        
        Args:
            text: Text to chunk
        
        Returns:
            List of chunks with context preservation
        """
        logger.debug("Using context-aware chunking")
        
        # Split into sentences
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > CHUNK_SIZE and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "token_count": current_length,
                    "type": "context_aware"
                })
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk, CHUNK_OVERLAP
                )
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.split()) >= MIN_CHUNK_SIZE:
                chunks.append({
                    "text": chunk_text,
                    "token_count": current_length,
                    "type": "context_aware"
                })
        
        return chunks
    
    def _semantic_chunking(self, text: str) -> List[Dict]:
        """
        Semantic chunking based on content similarity.
        Groups semantically similar sentences together.
        
        Args:
            text: Text to chunk
        
        Returns:
            List of semantically coherent chunks
        """
        logger.debug("Using semantic chunking")
        
        sentences = self._split_sentences(text)
        
        if len(sentences) <= 3:
            return [{
                "text": text,
                "token_count": len(text.split()),
                "type": "semantic"
            }]
        
        # Get embeddings for sentences (batch processing)
        embeddings = self._get_sentence_embeddings(sentences)
        
        # Group sentences by semantic similarity
        chunks = []
        current_chunk = [sentences[0]]
        current_embedding = embeddings[0]
        
        for i in range(1, len(sentences)):
            similarity = self._cosine_similarity(current_embedding, embeddings[i])
            current_length = sum(len(s.split()) for s in current_chunk)
            
            # Check if should continue current chunk or start new one
            if (similarity >= SEMANTIC_SIMILARITY_THRESHOLD and 
                current_length + len(sentences[i].split()) <= CHUNK_SIZE):
                current_chunk.append(sentences[i])
                # Update running average of embeddings
                current_embedding = (current_embedding + embeddings[i]) / 2
            else:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                if len(chunk_text.split()) >= MIN_CHUNK_SIZE:
                    chunks.append({
                        "text": chunk_text,
                        "token_count": len(chunk_text.split()),
                        "type": "semantic"
                    })
                
                # Start new chunk
                current_chunk = [sentences[i]]
                current_embedding = embeddings[i]
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.split()) >= MIN_CHUNK_SIZE:
                chunks.append({
                    "text": chunk_text,
                    "token_count": len(chunk_text.split()),
                    "type": "semantic"
                })
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_sentences(self, sentences: List[str], 
                               overlap_tokens: int) -> List[str]:
        """Get sentences for overlap based on token count."""
        overlap = []
        token_count = 0
        
        for sentence in reversed(sentences):
            sentence_tokens = len(sentence.split())
            if token_count + sentence_tokens <= overlap_tokens:
                overlap.insert(0, sentence)
                token_count += sentence_tokens
            else:
                break
        
        return overlap
    
    def _get_sentence_embeddings(self, sentences: List[str]) -> np.ndarray:
        """Get embeddings for sentences using Gemini."""
        embeddings = []
        
        for sentence in sentences:
            try:
                result = genai.embed_content(
                    model=EMBED_MODEL,
                    content=sentence
                )
                embeddings.append(result["embedding"])
            except Exception as e:
                logger.warning(f"Failed to embed sentence, using zero vector: {e}")
                # Use zero vector as fallback
                embeddings.append([0.0] * 768)
        
        return np.array(embeddings, dtype="float32")
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
