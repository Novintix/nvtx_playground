# app/services/oauth/token_store.py
import os, json, asyncio
from pathlib import Path
from typing import Optional, Dict, Any

TOKENS_FILE = Path(os.getenv("TOKENS_FILE", ".tokens.json"))

def _read_tokens_sync() -> Dict[str, Any]:
    if not TOKENS_FILE.exists():
        return {}
    return json.loads(TOKENS_FILE.read_text(encoding="utf-8"))

def _write_tokens_sync(data: Dict[str, Any]) -> None:
    TOKENS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

async def get_token(provider: str) -> Optional[Dict[str, Any]]:
    store_mode = os.getenv("TOKEN_STORE", "file").lower()  # default file
    if store_mode != "file":
        raise RuntimeError("TOKEN_STORE is not 'file'. Set TOKEN_STORE=file for local dev.")

    data = await asyncio.to_thread(_read_tokens_sync)
    return data.get(provider)

async def upsert_token(provider: str, token_doc: Dict[str, Any]) -> None:
    store_mode = os.getenv("TOKEN_STORE", "file").lower()
    if store_mode != "file":
        raise RuntimeError("TOKEN_STORE is not 'file'. Set TOKEN_STORE=file for local dev.")

    data = await asyncio.to_thread(_read_tokens_sync)
    data[provider] = token_doc
    await asyncio.to_thread(_write_tokens_sync, data)
