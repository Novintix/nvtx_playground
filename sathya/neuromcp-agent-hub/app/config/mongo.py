from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "neuromcp")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Collection for OAuth tokens
tokens_collection = db["oauth_tokens"]
