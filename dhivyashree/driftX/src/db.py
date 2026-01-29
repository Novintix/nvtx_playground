import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "driftx_db"

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def init_db():
    # MongoDB doesn't need strict schema initialization, 
    # but we can check connection here.
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info()
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

def create_room(room_id):
    db = get_db()
    
    # Check if room already exists
    if db.rooms.find_one({"_id": room_id}):
        return False
        
    db.rooms.insert_one({
        "_id": room_id,
        "status": "ACTIVE",
        "created_at": datetime.datetime.now()
    })
    return True

def join_room(room_id):
    db = get_db()
    room = db.rooms.find_one({"_id": room_id})
    return room["status"] if room else None

def end_room(room_id):
    db = get_db()
    db.rooms.update_one(
        {"_id": room_id},
        {"$set": {"status": "ENDED"}}
    )

def add_message(room_id, username, content):
    db = get_db()
    message = {
        "room_id": room_id,
        "username": username,
        "content": content,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "created_at": datetime.datetime.now()
    }
    db.messages.insert_one(message)

def get_messages(room_id):
    db = get_db()
    # Find messages for the room, sort by creation time
    cursor = db.messages.find({"room_id": room_id}).sort("created_at", 1)
    
    messages = [
        {
            "username": msg["username"], 
            "content": msg["content"], 
            "timestamp": msg["timestamp"]
        } 
        for msg in cursor
    ]
    return messages

def get_room_status(room_id):
    db = get_db()
    room = db.rooms.find_one({"_id": room_id})
    return room["status"] if room else None

# Initialize on module load
init_db()
