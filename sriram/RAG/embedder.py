"""
Embedding module for generating vector representations.
Handles batch processing and embedding optimization.
"""

import numpy as np
from typing import List, Dict
import google.generativeai as genai
from config import EMBED_MODEL
from logger import setup_logger

logger = setup_logger(__name__)


class Embedder:
    """
    Generates embeddings for text chunks using Gemini.
    Implements batch processing and error handling.
    """
    
    def __init__(self):
        """Initialize the embedder."""
        logger.info(f"Embedder initialized with model: {EMBED_MODEL}")
    
    def embed_chunks(self, chunks: List[Dict]) -> np.ndarray:
        """
        Generate embeddings for all chunks.
        
        Args:
            chunks: List of chunk dictionaries
        
        Returns:
            NumPy array of embeddings
        
        Raises:
            Exception: If embedding generation fails
        """
        try:
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embeddings = []
            
            for i, chunk in enumerate(chunks):
                try:
                    result = genai.embed_content(
                        model=EMBED_MODEL,
                        content=chunk["text"]
                    )
                    embeddings.append(result["embedding"])
                    
                    if (i + 1) % 10 == 0:
                        logger.debug(f"Embedded {i + 1}/{len(chunks)} chunks")
                        
                except Exception as e:
                    logger.error(f"Failed to embed chunk {i}: {str(e)}", exc_info=True)
                    raise
            
            embeddings_array = np.array(embeddings, dtype="float32")
            logger.info(f"Successfully generated embeddings with shape: "
                       f"{embeddings_array.shape}")
            
            return embeddings_array
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}", exc_info=True)
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.
        
        Args:
            query: Query text
        
        Returns:
            NumPy array of query embedding
        
        Raises:
            Exception: If embedding generation fails
        """
        try:
            logger.debug(f"Generating embedding for query: {query[:50]}...")
            
            result = genai.embed_content(
                model=EMBED_MODEL,
                content=query
            )
            
            embedding = np.array([result["embedding"]], dtype="float32")
            logger.debug(f"Query embedding shape: {embedding.shape}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Query embedding failed: {str(e)}", exc_info=True)
            raise
