"""
Test MongoDB Connection
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

print("=" * 70)
print("🧪 Testing MongoDB Connection")
print("=" * 70)

if not MONGODB_URI:
    print("❌ MONGODB_URI not found in .env")
    exit(1)

print(f"\n📡 Connecting to MongoDB...")
print(f"   URI: {MONGODB_URI[:50]}...")

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.admin.command('ping')
    print("✅ Connection successful!")
    
    # List databases
    print("\n📊 Available databases:")
    for db_name in client.list_database_names():
        print(f"   - {db_name}")
    
    # Check AI-HR database
    db = client["AI-HR"]
    print(f"\n📁 Collections in AI-HR database:")
    collections = db.list_collection_names()
    
    if not collections:
        print("   ⚠️  No collections found")
    else:
        for coll_name in collections:
            count = db[coll_name].count_documents({})
            print(f"   - {coll_name}: {count} documents")
    
    # Test a query
    print(f"\n🔍 Testing query on 'resumes' collection...")
    resumes = db["resumes"]
    sample = resumes.find_one()
    
    if sample:
        print(f"✅ Found sample document")
        print(f"   Keys: {list(sample.keys())[:5]}...")
    else:
        print("⚠️  No documents in resumes collection")
    
    print("\n" + "=" * 70)
    print("✅ MongoDB is working correctly!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print("\n💡 Troubleshooting:")
    print("   1. Check if MongoDB URI is correct")
    print("   2. Check if your IP is whitelisted in MongoDB Atlas")
    print("   3. Check if username/password are correct")
    print("=" * 70)
