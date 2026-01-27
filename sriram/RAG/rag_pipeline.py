"""
Main RAG pipeline orchestrator.
Coordinates all components for document processing and query handling.
"""

from typing import Dict, Optional, List
from pathlib import Path
import google.generativeai as genai

from config import GEMINI_API_KEY
from document_parser import DocumentParser
from preprocessor import TextPreprocessor
from chunker import AdvancedChunker
from embedder import Embedder
from vector_store import VectorStore
from reranker import Reranker
from llm_handler import LLMHandler
from logger import setup_logger

logger = setup_logger(__name__)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)


class RAGPipeline:
    """
    Orchestrates the complete RAG pipeline.
    Handles document ingestion and query processing.
    """
    
    def __init__(self, index_name: str = "default"):
        """
        Initialize RAG pipeline.
        
        Args:
            index_name: Name for the vector index
        """
        logger.info(f"Initializing RAG pipeline: {index_name}")
        
        self.index_name = index_name
        self.parser = DocumentParser()
        self.preprocessor = TextPreprocessor()
        self.chunker = AdvancedChunker()
        self.embedder = Embedder()
        self.vector_store = VectorStore(index_name)
        self.reranker = Reranker()
        self.llm_handler = LLMHandler()
        
        logger.info("RAG pipeline initialized successfully")
    
    def ingest_document(self, file_path: str, save_index: bool = True) -> Dict:
        """
        Ingest and process a document.
        
        Args:
            file_path: Path to PDF file
            save_index: Whether to save the index to disk
        
        Returns:
            Dictionary with ingestion statistics
        
        Raises:
            Exception: If ingestion fails
        """
        try:
            logger.info(f"Starting document ingestion: {file_path}")
            
            # Step 1: Parse document
            parsed_doc = self.parser.parse_pdf(file_path)
            
            # Step 2: Preprocess text
            clean_text = self.preprocessor.preprocess(parsed_doc["full_text"])
            
            # Step 3: Chunk text
            chunks = self.chunker.chunk_text(
                clean_text,
                metadata=parsed_doc["metadata"]
            )
            
            # Add page information to chunks
            chunks = self._enrich_chunks_with_pages(chunks, parsed_doc["pages"])
            
            # Step 4: Generate embeddings
            embeddings = self.embedder.embed_chunks(chunks)
            
            # Step 5: Create vector index
            self.vector_store.create_index(embeddings, chunks)
            
            # Step 6: Save index if requested
            if save_index:
                self.vector_store.save_index()
            
            stats = {
                "file_name": parsed_doc["metadata"]["file_name"],
                "total_pages": parsed_doc["metadata"]["total_pages"],
                "total_chunks": len(chunks),
                "embedding_dimension": embeddings.shape[1],
                "index_saved": save_index
            }
            
            logger.info(f"Document ingestion complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)
            raise
    
    def query(self, query_text: str, 
              metadata_filter: Optional[Dict] = None) -> Dict:
        """
        Process a query and generate answer.
        
        Args:
            query_text: User query
            metadata_filter: Optional metadata filters
        
        Returns:
            Dictionary with answer and sources
        
        Raises:
            Exception: If query processing fails
        """
        try:
            logger.info(f"Processing query: {query_text}")
            
            # Step 1: Embed query
            query_embedding = self.embedder.embed_query(query_text)
            
            # Step 2: Retrieve from vector store
            retrieved_chunks = self.vector_store.search(
                query_embedding,
                metadata_filter=metadata_filter
            )
            
            if not retrieved_chunks:
                logger.warning("No chunks retrieved for query")
                return {
                    "answer": "No relevant information found in the document.",
                    "query": query_text,
                    "sources": []
                }
            
            # Step 3: Re-rank results
            reranked_chunks = self.reranker.rerank(query_text, retrieved_chunks)
            
            # Step 4: Generate answer
            result = self.llm_handler.generate_answer(query_text, reranked_chunks)
            
            logger.info("Query processing complete")
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}", exc_info=True)
            raise
    
    def load_existing_index(self):
        """
        Load existing index from disk.
        
        Raises:
            Exception: If loading fails
        """
        try:
            logger.info(f"Loading existing index: {self.index_name}")
            self.vector_store.load_index()
            logger.info("Index loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}", exc_info=True)
            raise
    
    def _enrich_chunks_with_pages(self, chunks: List[Dict], 
                                   pages: List[Dict]) -> List[Dict]:
        """
        Enrich chunks with page number information.
        
        Args:
            chunks: List of chunks
            pages: List of page information
        
        Returns:
            Enriched chunks
        """
        # Simple heuristic: assign page based on character position
        total_chars = sum(p["char_count"] for p in pages)
        
        for chunk in chunks:
            # Estimate page number (simplified)
            chunk["metadata"]["page_number"] = 1  # Default
            
        return chunks
