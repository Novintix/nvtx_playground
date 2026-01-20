import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.config.db import symptom_collection
from app.utils.crypto import encrypt_dict, decrypt_dict

TTL_HOURS = 6  # session expires automatically (we'll use expires_at)


async def create_session() -> str:
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()

    doc = {
        "session_id": session_id,
        "created_at": now,
        "expires_at": now + timedelta(hours=TTL_HOURS),

        
        # inside create_session doc:
        "notes_enc": encrypt_dict({
            "_round_count": 0,
            "_asked_keys": []
        }),


        "history": []
    }

    await symptom_collection.insert_one(doc)
    return session_id


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    doc = await symptom_collection.find_one({"session_id": session_id})
    if not doc:
        return None

    # decrypt notes for usage in agent
    doc["notes"] = decrypt_dict(doc["notes_enc"])
    return doc


async def update_session(session_id: str, notes: dict, history_item: dict):
    await symptom_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {"notes_enc": encrypt_dict(notes)},
            "$push": {"history": history_item}
        }
    )
