import os
from pathlib import Path
from dotenv import load_dotenv

# Path Management
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = ROOT_DIR / "data"

# Load environment
load_dotenv(ROOT_DIR / ".env")

# Settings
LLM_MODEL = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
