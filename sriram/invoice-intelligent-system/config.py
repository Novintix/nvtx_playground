"""
Centralized configuration management.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "hf_jXVVqmOTBMvnZBTCuSzaccmJiKsPBXXX")
AZURE_CV_ENDPOINT = os.getenv("AZURE_CV_ENDPOINT")
AZURE_CV_KEY = os.getenv("AZURE_CV_KEY")

# Application Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8001))  # Changed from 8000 to 8001

# MCP Server Port (Unified)
MCP_PORT = int(os.getenv("MCP_PORT", 8000))

# Storage Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VECTOR_DB_PATH = DATA_DIR / "vector_store"
LOG_FILE = BASE_DIR / "process.log"

# RAG Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 512))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 128))
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", 5))
TOP_K_RERANK = int(os.getenv("TOP_K_RERANK", 3))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))

# Gemini Models
GEMINI_MODEL = "gemini-flash-latest"

# HuggingFace Embedding Model
HUGGINGFACE_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Create directories
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
VECTOR_DB_PATH.mkdir(exist_ok=True)
