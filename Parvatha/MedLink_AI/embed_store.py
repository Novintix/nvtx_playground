# embed_store.py

# pyright: reportGeneralTypeIssues=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

import os
import faiss
import pickle
import torch
import numpy as np
from typing import Any
from typing import List, Dict, Tuple
from transformers import AutoTokenizer, AutoModel

from config import FAISS_PATH
from error_handler import handle_error

os.makedirs(FAISS_PATH, exist_ok=True)


class PubMedEmbeddingStore:
    def __init__(self):
        try:
            print("🧠 Loading PubMedBERT (Transformers-native)...")

            self.tokenizer = AutoTokenizer.from_pretrained(
                "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
            )
            self.model = AutoModel.from_pretrained(
                "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
            )

            self.model.eval()
            self.dimension = self.model.config.hidden_size

        except Exception as e:
            raise RuntimeError(handle_error(e))

        self.index: Any = faiss.IndexFlatL2(self.dimension)
        self.metadata: List[Dict] = []

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output.last_hidden_state
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * mask, dim=1) / torch.clamp(mask.sum(dim=1), min=1e-9)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        try:
            if not isinstance(texts, list) or not all(isinstance(t, str) and t.strip() for t in texts):
                raise ValueError("Embedding input must be a list of non-empty strings")

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
                return embeddings.cpu().numpy()

        except Exception as e:
            raise RuntimeError(handle_error(e))

    # -----------------------------
    # Incremental FAISS helpers
    # -----------------------------
    def has_paper(self, pmid: str) -> bool:
        return any(p.get("pmid") == pmid for p in self.metadata)

    def add_paper(self, paper: Dict):
        abstract = paper.get("abstract", "")
        if not isinstance(abstract, str) or not abstract.strip():
            return

        embedding = self.embed_texts([abstract])
        self.index.add(embedding)
        self.metadata.append(paper)

    # -----------------------------
    # Public API
    # -----------------------------
    def build_index(self, papers: List[Dict]):
        try:
            texts, metas = [], []

            for p in papers:
                if isinstance(p.get("abstract"), str) and p["abstract"].strip():
                    texts.append(p["abstract"])
                    metas.append(p)

            if not texts:
                raise ValueError("No valid abstracts to embed")

            print(f"🔢 Generating embeddings for {len(texts)} papers...")
            embeddings = self.embed_texts(texts)

            self.index.add(embeddings)
            self.metadata.extend(metas)

            self._save()
            print("✅ FAISS index built successfully")

        except Exception as e:
            raise RuntimeError(handle_error(e))

    def search(self, query: str, top_k: int = 5) -> Tuple[List[Dict], List[float]]:
        try:
            if not isinstance(query, str) or not query.strip():
                raise ValueError("Search query must be a non-empty string")

            query_vec = self.embed_texts([query])
            distances, indices = self.index.search(query_vec, top_k)

            papers = [self.metadata[i] for i in indices[0]]
            return papers, distances[0].tolist()

        except Exception as e:
            raise RuntimeError(handle_error(e))

    # -----------------------------
    # Persistence
    # -----------------------------
    def _save(self):
        faiss.write_index(self.index, os.path.join(FAISS_PATH, "index.faiss"))
        with open(os.path.join(FAISS_PATH, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata, f)
