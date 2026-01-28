# test_rag.py
from ncbi_fetcher import fetch_papers
from embed_store import PubMedEmbeddingStore
from reranker import rerank
from rag_generator import MedicalRAGGenerator

query = "What are the main mechanisms linking insulin resistance and lifestyle factors?"

# Step 1: Fetch
papers = fetch_papers(query, 15)

# Step 2: Vector store
store = PubMedEmbeddingStore()
store.build_index(papers)

# Step 3: Retrieval
retrieved, distances = store.search(query, top_k=5)

# Step 4: Re-ranking
reranked = rerank(retrieved, distances)

# Step 5: RAG generation
rag = MedicalRAGGenerator()
answer = rag.generate_answer(query, reranked)

print("\n🧾 FINAL ANSWER:\n")
print(answer)
