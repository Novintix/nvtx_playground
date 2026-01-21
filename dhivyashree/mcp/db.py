from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
import os

def get_checkpointer():
    """Establishes MongoDB connection and returns the checkpointer."""
    # Use local mongodb or get from env
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = MongoClient(mongodb_uri)
    
    # Using a specific database for the agent
    db = client["agent_db"]
    
    # Initialize the checkpointer
    checkpointer = MongoDBSaver(client=client, db_name="agent_db", checkpoint_collection_name="workflow")
    
    return checkpointer
