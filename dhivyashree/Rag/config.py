import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "rag_chat_db"
COLLECTION_NAME = "group_chat_messages"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Model config
MODEL_NAME = "llama-3.3-70b-versatile"
