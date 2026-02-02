"""
Advanced RAG System using LangChain.
Implements semantic chunking, metadata-rich retrieval, and reranking.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from logger import setup_logger
from config import (
    GOOGLE_API_KEY, GEMINI_MODEL, HUGGINGFACE_API_KEY, HUGGINGFACE_EMBED_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RETRIEVAL, TOP_K_RERANK,
    VECTOR_DB_PATH, CONFIDENCE_THRESHOLD
)

logger = setup_logger("RAG_SYSTEM")


class AdvancedRAGSystem:
    """
    Advanced RAG with LangChain components.
    Features:
    - Semantic chunking with metadata
    - FAISS vector store
    - Contextual compression (reranking)
    - Metadata filtering
    """
    
    def __init__(self):
        logger.info("action=rag_init status=starting")
        
        # Initialize HuggingFace embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=HUGGINGFACE_EMBED_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize LLM for reranking and generation
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Vector store
        self.vector_store = None
        
        # Try to load existing index
        self._load_index()
        
        logger.info("action=rag_init status=complete")
    
    def index_invoice(self, document_id: str, structured_data: Dict[str, Any]):
        """
        Index structured invoice data with rich metadata.
        
        Args:
            document_id: Unique document identifier
            structured_data: Structured invoice JSON
        """
        logger.info(f"doc={document_id} action=indexing_start")
        
        try:
            # Create semantic chunks with metadata
            documents = self._create_semantic_chunks(document_id, structured_data)
            
            if not documents:
                logger.warning(f"doc={document_id} action=indexing_skipped reason=no_documents")
                return
            
            # Create or update vector store
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
                logger.info(f"doc={document_id} action=vector_store_created chunks={len(documents)}")
            else:
                self.vector_store.add_documents(documents)
                logger.info(f"doc={document_id} action=vector_store_updated chunks={len(documents)}")
            
            # Save index
            self._save_index()
            
            logger.info(f"doc={document_id} action=indexing_complete")
            
        except Exception as e:
            logger.error(f"doc={document_id} action=indexing_failed error={str(e)}")
            raise
    
    def query(self, query_text: str, metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query indexed invoices with natural language.
        
        Args:
            query_text: User's question
            metadata_filter: Optional metadata filters (e.g., {"vendor": "Acme Corp"})
            
        Returns:
            Answer with sources and confidence
        """
        logger.info(f"action=query_start query='{query_text}' filter={metadata_filter}")
        
        try:
            if self.vector_store is None:
                logger.warning("action=query_failed reason=no_index")
                return {
                    "answer": "No invoices have been indexed yet. Please process documents first.",
                    "confidence": 0.0,
                    "sources": [],
                    "status": "no_index"
                }
            
            # Retrieve with optional metadata filtering
            if metadata_filter:
                retrieved_docs = self.vector_store.similarity_search(
                    query_text,
                    k=TOP_K_RETRIEVAL,
                    filter=metadata_filter
                )
            else:
                retrieved_docs = self.vector_store.similarity_search(
                    query_text,
                    k=TOP_K_RETRIEVAL
                )
            
            if not retrieved_docs:
                logger.warning("action=query_no_results")
                return {
                    "answer": "No relevant invoices found for your query.",
                    "confidence": 0.0,
                    "sources": [],
                    "status": "no_results"
                }
            
            # Simple reranking: limit to top K
            retrieved_docs = retrieved_docs[:TOP_K_RERANK]
            
            # Generate answer
            answer_data = self._generate_answer(query_text, retrieved_docs)
            
            logger.info(f"action=query_complete confidence={answer_data['confidence']:.2f}")
            return answer_data
            
        except Exception as e:
            logger.error(f"action=query_failed error={str(e)}")
            return {
                "answer": f"Query processing failed: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "status": "error"
            }
    
    def _create_semantic_chunks(self, document_id: str, structured_data: Dict[str, Any]) -> List[Document]:
        """
        Create semantically meaningful chunks with rich metadata.
        
        Strategy:
        1. Header chunk (invoice metadata)
        2. Individual line item chunks
        3. Financial summary chunk
        """
        documents = []
        
        # Extract common metadata
        vendor = structured_data.get("vendor", "Unknown")
        invoice_number = structured_data.get("invoice_number", "N/A")
        invoice_date = structured_data.get("invoice_date", "N/A")
        total = structured_data.get("total", 0)
        currency = structured_data.get("currency", "USD")
        
        # Chunk 1: Invoice Header
        header_text = f"""Invoice from {vendor}
Invoice Number: {invoice_number}
Date: {invoice_date}
Currency: {currency}
Total Amount: {total}"""
        
        documents.append(Document(
            page_content=header_text,
            metadata={
                "document_id": document_id,
                "chunk_type": "header",
                "vendor": vendor,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "total": total,
                "currency": currency
            }
        ))
        
        # Chunks 2-N: Individual Line Items
        for idx, item in enumerate(structured_data.get("line_items", []), start=1):
            item_text = f"""Line Item {idx} from invoice {invoice_number}
Vendor: {vendor}
Description: {item.get('description', 'N/A')}
Quantity: {item.get('quantity', 0)}
Unit Price: {item.get('unit_price', 0)}
Amount: {item.get('amount', 0)}"""
            
            documents.append(Document(
                page_content=item_text,
                metadata={
                    "document_id": document_id,
                    "chunk_type": "line_item",
                    "vendor": vendor,
                    "invoice_number": invoice_number,
                    "item_index": idx,
                    "description": item.get('description', ''),
                    "amount": item.get('amount', 0),
                    "total": total
                }
            ))
        
        # Chunk N+1: Financial Summary
        summary_text = f"""Financial Summary for invoice {invoice_number}
Vendor: {vendor}
Subtotal: {structured_data.get('subtotal', 0)}
Tax: {structured_data.get('tax', 0)}
Total: {total}
Currency: {currency}"""
        
        documents.append(Document(
            page_content=summary_text,
            metadata={
                "document_id": document_id,
                "chunk_type": "summary",
                "vendor": vendor,
                "invoice_number": invoice_number,
                "subtotal": structured_data.get('subtotal', 0),
                "tax": structured_data.get('tax', 0),
                "total": total,
                "currency": currency
            }
        ))
        
        logger.info(f"doc={document_id} action=chunking_complete chunks={len(documents)}")
        return documents
    
    def _generate_answer(self, query: str, retrieved_docs: List[Document]) -> Dict[str, Any]:
        """
        Generate answer from retrieved documents using LLM.
        """
        # Build context
        context_parts = []
        for idx, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"[Source {idx}]\n{doc.page_content}\n")
        
        context = "\n".join(context_parts)
        
        # Calculate confidence based on number of results
        confidence = min(len(retrieved_docs) / TOP_K_RETRIEVAL, 1.0)
        
        prompt = f"""You are an invoice data analyst. Answer the user's question based ONLY on the provided invoice data.

Retrieved Invoice Data:
{context}

User Question: {query}

Instructions:
1. Answer based ONLY on the provided data
2. If the data doesn't contain enough information, say "I don't have enough information to answer that"
3. Cite specific invoice numbers or vendors when relevant
4. Be concise and precise

Answer:"""
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content.strip()
            
            # Determine status
            if confidence < CONFIDENCE_THRESHOLD:
                status = "uncertain"
                answer = f"[Low Confidence] {answer}"
            else:
                status = "confident"
            
            return {
                "answer": answer,
                "confidence": float(confidence),
                "sources": [
                    {
                        "text": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    }
                    for doc in retrieved_docs
                ],
                "status": status
            }
            
        except Exception as e:
            logger.error(f"action=answer_generation_failed error={str(e)}")
            return {
                "answer": "Failed to generate answer from retrieved data.",
                "confidence": 0.0,
                "sources": [],
                "status": "error"
            }
    
    def _save_index(self):
        """Save FAISS index to disk."""
        if self.vector_store:
            index_path = VECTOR_DB_PATH / "faiss_index"
            self.vector_store.save_local(str(index_path))
            logger.info(f"action=index_saved path={index_path}")
    
    def _load_index(self):
        """Load FAISS index from disk."""
        index_path = VECTOR_DB_PATH / "faiss_index"
        if index_path.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                
                logger.info(f"action=index_loaded path={index_path}")
            except Exception as e:
                logger.warning(f"action=index_load_failed error={str(e)}")
