import os
from itsdangerous import URLSafeSerializer
from dotenv import load_dotenv

load_dotenv()

SECRET = os.getenv("SESSION_SECRET")

serializer = URLSafeSerializer(SECRET, salt="oauth-state")


def sign_state(data: dict) -> str:
    return serializer.dumps(data)


def unsign_state(token: str) -> dict:
    return serializer.loads(token)
