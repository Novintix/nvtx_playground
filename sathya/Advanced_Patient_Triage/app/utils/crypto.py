import os
import json
from cryptography.fernet import Fernet
from app.config.settings import settings

# This key must be in your .env as TRIAGE_ENCRYPTION_KEY
if not settings.TRIAGE_ENCRYPTION_KEY:
    raise RuntimeError("TRIAGE_ENCRYPTION_KEY missing in .env")

fernet = Fernet(settings.TRIAGE_ENCRYPTION_KEY.encode())


def encrypt_dict(data: dict) -> str:
    """
    Encrypts a Python dict into a string (ciphertext).
    Safe to store in DB.
    """
    raw = json.dumps(data, ensure_ascii=False).encode()
    return fernet.encrypt(raw).decode()


def decrypt_dict(token: str) -> dict:
    """
    Decrypts ciphertext string back into a Python dict.
    """
    raw = fernet.decrypt(token.encode()).decode()
    return json.loads(raw)
