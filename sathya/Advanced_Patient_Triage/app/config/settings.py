import os
from pathlib import Path
from dotenv import load_dotenv

# Project root (folder that contains "app")
ROOT_DIR = Path(__file__).resolve().parents[2]

# Always load .env from project root
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


class Settings:
    ENV: str = os.getenv("ENV", "local")
    APP_NAME: str = os.getenv("APP_NAME", "Advanced Patient Triage")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    MONGODB_URI: str | None = os.getenv("MONGODB_URI")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "medical_agent")
    MONGODB_COLLECTION: str = os.getenv("MONGODB_COLLECTION", "symptom_interpretation")

    TRIAGE_ENCRYPTION_KEY: str | None = os.getenv("TRIAGE_ENCRYPTION_KEY")


settings = Settings()
