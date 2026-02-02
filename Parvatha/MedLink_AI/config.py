# config.py
from pathlib import Path

# =================================================
# Domain Guard Configuration
# =================================================
# Minimum biomedical relevance score to accept query (0-1)
MIN_DOMAIN_RELEVANCE = 0.45 
# Minimum confidence score to generate answer (0-1)
MIN_ANSWER_CONFIDENCE = 0.60

# =================================================
# Paper Fetching Configuration
# =================================================
MAX_PAPERS_DEFAULT = 25
MAX_PAPERS_RANGE = (10, 50)

# =================================================
# Storage Paths
# =================================================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

FAISS_PATH = DATA_DIR / "faiss_index"
SQLITE_DB = DATA_DIR / "cache.db"

FAISS_PATH.mkdir(exist_ok=True)

# =================================================
# Re-ranking Weights (Enhanced)
# =================================================
WEIGHTS = {
    "relevance": 0.35,      # Bi-encoder similarity
    "cross_encoder": 0.25,  # Cross-encoder relevance
    "citations": 0.20,      # Citation count
    "recency": 0.15,        # Publication year
    "journal": 0.05         # Journal impact
}

# =================================================
# Groq Model Configuration 
# =================================================
LLM_MODEL = "llama-3.1-8b-instant"
# Domain-specific embedding model
EMBEDDING_MODEL = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"

# Cross-encoder for re-ranking
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Token limits
MAX_TOKEN_LENGTH = 512

# =================================================
# Multi-hop Configuration
# =================================================
MAX_HOPS = 2
TOP_K_PER_HOP = 5
MAX_TOTAL_PAPERS = 20  # Prevent too many papers

# =================================================
# Evidence Quality Thresholds
# =================================================
CONFLICT_THRESHOLD = 0.3  # If consensus < 30%, flag as contradictory
EVIDENCE_GRADE_THRESHOLDS = {
    "A": 0.85,  # Systematic review / Multiple RCTs
    "B": 0.70,  # Single RCT / Strong cohort
    "C": 0.55,  # Cohort / Case-control
    "D": 0.40,  # Expert opinion / Weak evidence
    "INSUFFICIENT": 0.0
}

# =================================================
# Error Messages
# =================================================
ERROR_MESSAGES = {
    "ncbi_connection": "⚠️ Unable to connect to NCBI. Check internet connection.",
    "no_papers": "📭 No papers found. Try different keywords.",
    "faiss_error": "⚠️ Vector database error. Try rebuilding index.",
    "model_error": "⚠️ Model loading failed. Using lightweight fallback.",
    "generation_error": "⚠️ Answer generation failed. Using extractive fallback.",
    "domain_rejection": "🚫 This query appears to be outside the biomedical domain or contains logical inconsistencies.",
    "low_confidence": "⚠️ Insufficient high-quality evidence found to provide a reliable answer."
}
 
