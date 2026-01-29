# app/services/db/mongo.py
import os
from typing import Optional

_client = None
_tokens_collection = None

def _mongo_enabled() -> bool:
    # If you want: disable mongo completely when mock tools enabled
    if os.getenv("MOCK_TOOLS", "false").lower() == "true":
        return False
    return os.getenv("USE_MONGO_TOKENS", "true").lower() == "true"

def get_tokens_collection():
    """
    Lazy init. This function is the ONLY place allowed to create MongoClient.
    Nothing should create a client at import time.
    """
    global _client, _tokens_collection

    if not _mongo_enabled():
        raise RuntimeError("Mongo disabled (MOCK_TOOLS=true or USE_MONGO_TOKENS=false)")

    if _tokens_collection is not None:
        return _tokens_collection

    from pymongo import MongoClient  # import inside = safe
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        raise RuntimeError("MONGO_URI is missing but Mongo is enabled")

    _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db_name = os.getenv("MONGO_DB", "neuro")
    _tokens_collection = _client[db_name]["tokens"]
    return _tokens_collection
