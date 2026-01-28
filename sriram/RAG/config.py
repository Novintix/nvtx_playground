"""
Configuration module for RAG system.
Centralizes all configuration parameters and API keys.
"""

import os
from pathlib import Path

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model Configuration
EMBED_MODEL = "text-embedding-004"
LLM_MODEL = "gemini-flash-latest"

# Chunking Configuration
CHUNK_SIZE = 512  # Tokens per chunk
CHUNK_OVERLAP = 128  # Overlap between chunks for context preservation
MIN_CHUNK_SIZE = 50  # Minimum chunk size to avoid tiny fragments (reduced from 100)

# Semantic Chunking Configuration
SEMANTIC_SIMILARITY_THRESHOLD = 0.75  # Threshold for semantic similarity
USE_SEMANTIC_CHUNKING = False  # Toggle between semantic and context-aware chunking (disabled for stability)

# Retrieval Configuration
TOP_K_RETRIEVAL = 5  # Number of chunks to retrieve initially
TOP_K_RERANK = 3  # Number of chunks after re-ranking

# FAISS Configuration
FAISS_INDEX_TYPE = "L2"  # L2 or IP (Inner Product)

# Logging Configuration
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "process.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Storage Configuration
UPLOAD_DIR = Path("uploads")
INDEX_DIR = Path("indexes")

# Create necessary directories
LOG_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
