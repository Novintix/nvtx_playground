# config.py

NCBI_EMAIL = "parvatha2510@gmail.com"  # REQUIRED by NCBI
NCBI_API_KEY = "a7f45b3edcba250eaffa9164ae79dbd10509"     # optional but faster

MAX_PAPERS_DEFAULT = 25
MAX_PAPERS_RANGE = (10, 50)

FAISS_PATH = "data/faiss_index"
SQLITE_DB = "data/cache.db"

# Re-ranking weights
WEIGHTS = {
    "relevance": 0.4,
    "citations": 0.3,
    "recency": 0.2,
    "journal": 0.1
}
