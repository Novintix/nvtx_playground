# test_reranker.py
from ncbi_fetcher import fetch_papers
from embed_store import PubMedEmbeddingStore
from reranker import rerank

query = "diabetes and insulin resistance"

# Step 1: Fetch papers (from cache or NCBI)
papers = fetch_papers(query, 10)

# Step 2: Build vector store
store = PubMedEmbeddingStore()
store.build_index(papers)

# Step 3: Semantic retrieval (NO FAISS ACCESS HERE)
retrieved_papers, distances = store.search(query, top_k=5)

# Step 4: Re-ranking
reranked = rerank(retrieved_papers, distances)

# Step 5: Display results
for p in reranked:
    print(p["title"])
    print("Score:", p["final_score"])
    print("Breakdown:", p["score_breakdown"])
    print("-" * 50)
