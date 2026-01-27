"""
Vector store module using FAISS for efficient similarity search.
Handles index creation, storage, and retrieval with metadata filtering.
"""

import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional
from config import FAISS_INDEX_TYPE, INDEX_DIR, TOP_K_RETRIEVAL
from logger import setup_logger

logger = setup_logger(__name__)


class VectorStore:
    """
    Manages FAISS vector index for similarity search.
    Supports metadata filtering and efficient retrieval.
    """
    
    def __init__(self, index_name: str = "default"):
        """
        Initialize vector store.
        
        Args:
            index_name: Name for the index (for saving/loading)
        """
        self.index_name = index_name
        self.index = None
        self.chunks = []
        self.dimension = None
        logger.info(f"VectorStore initialized: {index_name}")
    
    def create_index(self, embeddings: np.ndarray, chunks: List[Dict]):
        """
        Create FAISS index from embeddings.
        
        Args:
            embeddings: NumPy array of embeddings
            chunks: List of chunk dictionaries
        
        Raises:
            Exception: If index creation fails
        """
        try:
            logger.info(f"Creating FAISS index with {len(embeddings)} vectors")
            
            self.dimension = embeddings.shape[1]
            self.chunks = chunks
            
            # Create appropriate index type
            if FAISS_INDEX_TYPE == "L2":
                self.index = faiss.IndexFlatL2(self.dimension)
            else:
                self.index = faiss.IndexFlatIP(self.dimension)
            
            # Add vectors to index
            self.index.add(embeddings)
            
            logger.info(f"FAISS index created successfully. Total vectors: "
                       f"{self.index.ntotal}")
            
        except Exception as e:
            logger.error(f"Index creation failed: {str(e)}", exc_info=True)
            raise
    
    def search(self, query_embedding: np.ndarray, k: int = TOP_K_RETRIEVAL,
               metadata_filter: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar chunks in the index.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            metadata_filter: Optional metadata filters (e.g., {"page_number": 5})
        
        Returns:
            List of retrieved chunks with scores
        
        Raises:
            Exception: If search fails
        """
        try:
            if self.index is None:
                raise ValueError("Index not created. Call create_index first.")
            
            logger.debug(f"Searching index for top {k} results")
            
            # Perform search
            distances, indices = self.index.search(query_embedding, k)
            
            # Retrieve chunks
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.chunks):
                    chunk = self.chunks[idx].copy()
                    chunk["score"] = float(distances[0][i])
                    chunk["rank"] = i + 1
                    
                    # Apply metadata filtering if specified
                    if metadata_filter:
                        if self._matches_filter(chunk, metadata_filter):
                            results.append(chunk)
                    else:
                        results.append(chunk)
            
            logger.info(f"Retrieved {len(results)} chunks from index")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            raise
    
    def _matches_filter(self, chunk: Dict, metadata_filter: Dict) -> bool:
        """Check if chunk matches metadata filter."""
        chunk_metadata = chunk.get("metadata", {})
        
        for key, value in metadata_filter.items():
            if chunk_metadata.get(key) != value:
                return False
        
        return True
    
    def save_index(self):
        """
        Save FAISS index and chunks to disk.
        
        Raises:
            Exception: If saving fails
        """
        try:
            logger.info(f"Saving index: {self.index_name}")
            
            index_path = INDEX_DIR / f"{self.index_name}.index"
            chunks_path = INDEX_DIR / f"{self.index_name}.chunks"
            
            # Save FAISS index
            faiss.write_index(self.index, str(index_path))
            
            # Save chunks
            with open(chunks_path, 'wb') as f:
                pickle.dump(self.chunks, f)
            
            logger.info(f"Index saved successfully to {INDEX_DIR}")
            
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}", exc_info=True)
            raise
    
    def load_index(self):
        """
        Load FAISS index and chunks from disk.
        
        Raises:
            Exception: If loading fails
        """
        try:
            logger.info(f"Loading index: {self.index_name}")
            
            index_path = INDEX_DIR / f"{self.index_name}.index"
            chunks_path = INDEX_DIR / f"{self.index_name}.chunks"
            
            if not index_path.exists() or not chunks_path.exists():
                raise FileNotFoundError(f"Index files not found: {self.index_name}")
            
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Load chunks
            with open(chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)
            
            self.dimension = self.index.d
            
            logger.info(f"Index loaded successfully. Total vectors: {self.index.ntotal}")
            
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}", exc_info=True)
            raise
