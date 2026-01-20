import os
import warnings
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, initialize_agent, AgentType

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='google.api_core._python_version_support')

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

# MongoDB Connection
client = MongoClient(MONGODB_URI)
db = client["AI-HR"]

# ---------------- TOOLS ---------------- #

@tool
def list_collections() -> str:
    """List all collections in the AI-HR database."""
    try:
        collections = db.list_collection_names()
        return f"Available collections in AI-HR database: {', '.join(collections)}"
    except Exception as e:
        return f"Error listing collections: {str(e)}"

@tool
def count_documents(collection_name: str) -> str:
    """Count total documents in a specific collection. Pass the collection name as a string."""
    try:
        collection = db[collection_name]
        count = collection.count_documents({})
        return f"The '{collection_name}' collection has {count} documents."
    except Exception as e:
        return f"Error counting documents in '{collection_name}': {str(e)}"

@tool
def get_sample_document(collection_name: str) -> str:
    """Get one sample document from a collection to see its structure."""
    try:
        collection = db[collection_name]
        sample = collection.find_one()
        
        if sample:
            if '_id' in sample:
                sample['_id'] = str(sample['_id'])
            return f"Sample document from '{collection_name}':\n{json.dumps(sample, indent=2, default=str)}"
        else:
            return f"No documents found in '{collection_name}'"
    except Exception as e:
        return f"Error getting sample from '{collection_name}': {str(e)}"

@tool
def find_all_documents(collection_name: str) -> str:
    """Find all documents in a collection (limited to 10 results)."""
    try:
        collection = db[collection_name]
        documents = list(collection.find({}).limit(10))
        
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        if not documents:
            return f"No documents found in '{collection_name}'"
        
        return f"Found {len(documents)} documents in '{collection_name}':\n{json.dumps(documents, indent=2, default=str)}"
    except Exception as e:
        return f"Error finding documents in '{collection_name}': {str(e)}"

@tool
def search_by_field(collection_name: str, field_name: str, field_value: str) -> str:
    """Search for documents where a field matches a value (case-insensitive)."""
    try:
        collection = db[collection_name]
        query = {field_name: {"$regex": field_value, "$options": "i"}}
        documents = list(collection.find(query).limit(10))
        
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        if not documents:
            return f"No documents found in '{collection_name}' where {field_name} contains '{field_value}'"
        
        return f"Found {len(documents)} documents:\n{json.dumps(documents, indent=2, default=str)}"
    except Exception as e:
        return f"Error searching in '{collection_name}': {str(e)}"

# ---------------- LLM ---------------- #
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)

tools = [
    list_collections,
    count_documents,
    get_sample_document,
    find_all_documents,
    search_by_field
]

# ---------------- AGENT (Using STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION) ---------------- #
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5
)

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    print("🤖 MongoDB AI-HR Agent Ready!")
    print("="*60)
    print(f"📊 Connected to database: AI-HR")
    print("="*60)
    
    while True:
        print("\n" + "="*60)
        user_query = input("💬 Ask a question (or 'quit' to exit): ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not user_query:
            continue
        
        try:
            print(f"\n{'='*60}")
            response = agent_executor.invoke({"input": user_query})
            
            print(f"\n{'='*60}")
            print("✅ ANSWER:")
            print(f"{'='*60}")
            print(response["output"])
        except Exception as e:
            print(f"❌ Error: {str(e)}")