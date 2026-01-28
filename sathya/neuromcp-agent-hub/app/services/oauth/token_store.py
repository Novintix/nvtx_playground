from __future__ import annotations
from app.config.mongo import tokens_collection


async def upsert_token(provider: str, access_token: str, refresh_token: str = ""):
    """
    Save or update OAuth token for provider.
    """
    await tokens_collection.update_one(
        {"provider": provider},
        {"$set": {
            "provider": provider,
            "access_token": access_token,
            "refresh_token": refresh_token
        }},
        upsert=True
    )


async def get_token(provider: str):
    """
    Fetch OAuth token for provider.
    """
    return await tokens_collection.find_one({"provider": provider})
