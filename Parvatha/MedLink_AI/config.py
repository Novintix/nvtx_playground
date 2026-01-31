# config.py
from pathlib import Path

# -----------------------------
# NCBI Configuration
# -----------------------------
NCBI_EMAIL = "parvatha2510@gmail.com"
NCBI_API_KEY = "a3e8077e028e51beb7254e79945b2de38d08"

MAX_PAPERS_DEFAULT = 25
MAX_PAPERS_RANGE = (10, 50)

# -----------------------------
# Storage Paths
# -----------------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

FAISS_PATH = DATA_DIR / "faiss_index"
SQLITE_DB = DATA_DIR / "cache.db"

FAISS_PATH.mkdir(exist_ok=True)

# -----------------------------
# Re-ranking Weights
# -----------------------------
WEIGHTS = {
    "relevance": 0.4,
    "citations": 0.3,
    "recency": 0.2,
    "journal": 0.1
}

# -----------------------------
# LangChain Configuration
# -----------------------------
LLM_MODEL = "google/flan-t5-large"
EMBEDDING_MODEL = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
MAX_TOKEN_LENGTH = 512
GENERATION_MAX_TOKENS = 256

# -----------------------------
# Multi-hop Configuration
# -----------------------------
MAX_HOPS = 2
TOP_K_PER_HOP = 5

# -----------------------------
# Error Messages
# -----------------------------
ERROR_MESSAGES = {
    "ncbi_connection": "⚠️ Unable to connect to NCBI. Check internet connection.",
    "no_papers": "📭 No papers found. Try different keywords.",
    "faiss_error": "⚠️ Vector database error. Try rebuilding index.",
    "model_error": "⚠️ Model loading failed. Check memory or dependencies.",
    "generation_error": "⚠️ Answer generation failed. Using fallback method."
}