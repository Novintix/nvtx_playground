#embed_store.py
import os
import faiss
import pickle
import torch
import numpy as np
from typing import List, Dict, Tuple, Optional
from transformers import AutoTokenizer, AutoModel
from langchain_core.embeddings import Embeddings

from config import FAISS_PATH, EMBEDDING_MODEL
from error_handler import handle_error, log_info

os.makedirs(FAISS_PATH, exist_ok=True)


class PubMedBERTEmbeddings(Embeddings):
    """LangChain-compatible PubMedBERT embeddings"""
    
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        self.model = AutoModel.from_pretrained(EMBEDDING_MODEL)
        self.model.eval()
    
    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output.last_hidden_state
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * mask, dim=1) / torch.clamp(
            mask.sum(dim=1), min=1e-9
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        with torch.no_grad():
            encoded = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512
            )
            output = self.model(**encoded)
            embeddings = self._mean_pooling(output, encoded["attention_mask"])
            return embeddings.cpu().numpy().tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return self.embed_documents([text])[0]


class PubMedEmbeddingStore:
    """Enhanced embedding store with FAISS and metadata"""
    
    def __init__(self):
        try:
            log_info("🧠 Loading PubMedBERT embeddings...")
            
            self.embeddings = PubMedBERTEmbeddings()
            self.dimension = 768  # PubMedBERT dimension
            
            # Native FAISS index with Inner Product (for cosine similarity)
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata: List[Dict] = []
            
            # Load existing index
            self._load()
            
            log_info(f"✅ Loaded {len(self.metadata)} papers from index")
            
        except Exception as e:
            raise RuntimeError(handle_error(e, "PubMedEmbeddingStore init"))
    
    def has_paper(self, pmid: str) -> bool:
        """Check if paper exists in index"""
        return any(p.get("pmid") == pmid for p in self.metadata)
    
    def get_embedding(self, pmid: str) -> Optional[np.ndarray]:
        """Retrieve embedding for a specific paper by PMID"""
        # Find index of paper with this PMID
        idx = None
        for i, meta in enumerate(self.metadata):
            if meta.get("pmid") == pmid:
                idx = i
                break
        
        if idx is not None and idx < self.index.ntotal:
            # Reconstruct the vector from FAISS
            # FAISS doesn't store vectors directly accessible by ID in IndexFlatIP
            # We need to search for it or maintain a separate array
            # Since we have the index, we can get it via reconstruct
            try:
                return self.index.reconstruct(int(idx))
            except:
                return None
        return None
    
    def add_paper(self, paper: Dict):
        """Add single paper to index"""
        try:
            abstract = paper.get("abstract", "")
            if not isinstance(abstract, str) or not abstract.strip():
                return
            
            embedding = self.embeddings.embed_query(abstract)
            embedding_array = np.array([embedding], dtype=np.float32)
            
            # L2 normalize for cosine similarity
            faiss.normalize_L2(embedding_array)
            
            # Add to FAISS
            self.index.add(embedding_array)
            self.metadata.append(paper)
            
            # Auto-save periodically
            if len(self.metadata) % 10 == 0:
                self._save()
                
        except Exception as e:
            log_info(f"⚠️ Failed to add paper {paper.get('pmid')}: {e}")
    
    def build_index(self, papers: List[Dict]):
        """Build index from scratch"""
        try:
            log_info(f"🔢 Building index for {len(papers)} papers...")
            
            texts, metas = [], []
            for p in papers:
                if isinstance(p.get("abstract"), str) and p["abstract"].strip():
                    texts.append(p["abstract"])
                    metas.append(p)
            
            if not texts:
                raise ValueError("No valid abstracts to embed")
            
            # Batch embed
            embeddings = self.embeddings.embed_documents(texts)
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # L2 normalize
            faiss.normalize_L2(embeddings_array)
            
            # Add to FAISS
            self.index.add(embeddings_array)
            self.metadata.extend(metas)
            
            self._save()
            log_info("✅ Index built successfully")
            
        except Exception as e:
            raise RuntimeError(handle_error(e, "build_index"))
    
    def search(self, query: str, top_k: int = 10) -> Tuple[List[Dict], List[float], List[float]]:
        """
        Search for similar papers
        Returns: (papers, similarity_scores, uncertainties)
        """
        try:
            if not isinstance(query, str) or not query.strip():
                raise ValueError("Query must be non-empty string")
            
            if self.index.ntotal == 0:
                log_warning("⚠️ FAISS index is empty!")
                return [], [], []
            
            # Get query embedding
            query_embedding = self.embeddings.embed_query(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            
            # L2 normalize
            faiss.normalize_L2(query_array)
            
            # Search
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_array, k)
            
            papers = []
            sim_scores = []
            uncertainties = []
            
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadata) and idx >= 0:
                    papers.append(self.metadata[idx])
                    # Convert distance to similarity score (FAISS returns inner product)
                    sim_scores.append(float(distances[0][i]))
                    uncertainties.append(self.metadata[idx].get("embedding_uncertainty", 0.0))
            
            log_info(f"🔍 FAISS search found {len(papers)} papers (index size: {self.index.ntotal})")
            
            return papers, sim_scores, uncertainties
            
        except Exception as e:
            error_msg = handle_error(e, "search")
            log_warning(error_msg)
            return [], [], []
    
    def calculate_evidence_confidence(self, papers: List[Dict], similarities: List[float]) -> float:
        """Calculate aggregate confidence score for retrieved evidence"""
        if not papers or not similarities:
            return 0.0
        
        # Top similarity score (best match quality)
        top_sim = max(similarities) if similarities else 0
        
        # Similarity spread (how well top results match vs bottom)
        sim_range = max(similarities) - min(similarities) if len(similarities) > 1 else 0
        
        # Coverage (number of relevant papers found)
        coverage = min(len([s for s in similarities if s > 0.5]) / 5, 1.0)
        
        # Year consistency (prefer recent consensus)
        years = [p.get("year", 0) for p in papers if p.get("year", 0) > 0]
        if years:
            year_std = np.std(years) if len(years) > 1 else 0
            year_consistency = max(0, 1.0 - year_std / 20)
        else:
            year_consistency = 0.5
        
        # Combined confidence
        confidence = (
            0.4 * top_sim +
            0.2 * sim_range +
            0.2 * coverage +
            0.2 * year_consistency
        )
        
        return min(confidence, 1.0)
    
    def _save(self):
        """Save index to disk"""
        try:
            faiss.write_index(self.index, str(FAISS_PATH / "index.faiss"))
            with open(FAISS_PATH / "metadata.pkl", "wb") as f:
                pickle.dump(self.metadata, f)
        except Exception as e:
            log_info(f"⚠️ Failed to save index: {e}")
    
    def _load(self):
        """Load index from disk"""
        try:
            index_path = FAISS_PATH / "index.faiss"
            metadata_path = FAISS_PATH / "metadata.pkl"
            
            if index_path.exists() and metadata_path.exists():
                self.index = faiss.read_index(str(index_path))
                with open(metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
                log_info(f"📂 Loaded FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            log_info(f"⚠️ Could not load existing index: {e}")