from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# ============================
# Model Configuration (Groq)
# ============================

@dataclass(frozen=True)
class ModelSettings:
    # ✅ Groq OpenAI-Compatible Endpoint
    base_url: str = "https://api.groq.com/openai/v1"

    # ✅ Strong Groq Planning Model
    model: str = "llama-3.3-70b-versatile"

    # ✅ Stable agent planning parameters
    temperature: float = 0.2
    top_p: float = 0.9
    max_tokens: int = 900
    timeout_s: int = 45

    # ✅ Reduce repetition
    frequency_penalty: float = 0.2
    presence_penalty: float = 0.0


@dataclass(frozen=True)
class AppSettings:
    groq_api_key: str
    model: ModelSettings = ModelSettings()


def get_settings() -> AppSettings:
    key = os.getenv("GROQ_API_KEY", "").strip()

    if not key:
        raise RuntimeError(
            "❌ GROQ_API_KEY missing. Please add it in .env file."
        )

    return AppSettings(groq_api_key=key)
