from ncbi_fetcher import fetch_papers
from embed_store import PubMedEmbeddingStore

papers = fetch_papers("diabetes and insulin resistance", 10)

store = PubMedEmbeddingStore()
store.build_index(papers)

results = store.search("insulin sensitivity mechanisms", top_k=3)
print(results[0]["title"])
