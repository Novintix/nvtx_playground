from pymongo import MongoClient
from Rag.config import MONGO_URI, DB_NAME, COLLECTION_NAME

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def get_collection():
    db = get_db()
    return db[COLLECTION_NAME]

def init_db():
    """Ensures indexes exist"""
    collection = get_collection()
    # Index for date filtering
    collection.create_index("date")
    # Index for thread reconstruction
    collection.create_index("thread_id")
    # Index for full text search (optional backup)
    collection.create_index([("message_text", "text")])
    print("Database initialized and indexes created.")
