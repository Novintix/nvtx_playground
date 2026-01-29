# multihop_rag.py

from ncbi_fetcher import fetch_papers
from embed_store import PubMedEmbeddingStore
from reranker import rerank
from rag_generator import MedicalRAGGenerator


class MultiHopRAG:
    def __init__(self):
        self.store = PubMedEmbeddingStore()
        self.rag = MedicalRAGGenerator()

    def run(self, query: str):
        """
        Guaranteed-answer 2-hop RAG pipeline
        """

        # ---------------------------
        # Hop 1: Fetch & retrieve
        # ---------------------------
        papers = fetch_papers(query, max_results=10)

        for p in papers:
            if not self.store.has_paper(p["pmid"]):
                self.store.add_paper(p)

        retrieved_1, dist_1 = self.store.search(query, top_k=5)
        ranked_1 = rerank(retrieved_1, dist_1)

        # ---------------------------
        # Hop 2: Expand query
        # ---------------------------
        if ranked_1:
            top_titles = [p["title"] for p in ranked_1[:2]]
            expanded_query = query + " mechanisms " + " ".join(top_titles)
        else:
            expanded_query = query

        retrieved_2, dist_2 = self.store.search(expanded_query, top_k=5)
        ranked_2 = rerank(retrieved_2, dist_2)

        # ---------------------------
        # Merge evidence
        # ---------------------------
        final_papers = []
        seen = set()

        for p in ranked_1 + ranked_2:
            pmid = p.get("pmid")
            if pmid and pmid not in seen:
                final_papers.append(p)
                seen.add(pmid)

        # ---------------------------
        # Final Answer (GUARANTEED)
        # ---------------------------
        answer = self.rag.generate_answer(query, final_papers)

        return answer, final_papers
