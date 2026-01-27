from datetime import datetime
from typing import List, Optional, Dict, Any
from Rag.database.connection import get_collection

def retrieve_messages(
    start_date: str,
    end_date: str,
    query: Optional[str] = None, 
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieves messages based on a strict date range.
    This is the primary retrieval method for "Context Reconstruction"
    where the user wants to know what happened in a time window.
    
    Args:
        start_date (str): ISO date string (YYYY-MM-DD)
        end_date (str): ISO date string (YYYY-MM-DD)
        query (str, optional): Semantic query for re-ranking (not used in strict temporal mode).
        
    Returns:
        List[Dict]: List of message documents sorted by timestamp.
    """
    collection = get_collection()
    
    # Base filter: Date range
    # Assumption: User provides YYYY-MM-DD, we treat strict string match on 'date' field
    # or we can do range query on 'timestamp'. 
    # The sample data has "date": "2026-01-20".
    
    filter_query = {
        "date": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    # If a semantic query is present, ideally we would:
    # 1. Fetch all messages in date range.
    # 2. Rerank them locally using cross-encoder or embedding distance.
    # For this implementation, we will trust the date range is small enough 
    # to return ALL messages for the LLM to process.
    # The requirement says "Retrieve conversation windows", so getting the full chronological block is better.
    
    cursor = collection.find(filter_query).sort("timestamp", 1).limit(limit)
    
    messages = list(cursor)
    
    # Post-processing: If we had a vector store, we could filter here.
    # But for "Reconstruct Context", we intentionally avoid filtering out "noise" 
    # too aggressively because "noise" is often the glue of the conversation.
    
    return messages

def get_thread(thread_id: str) -> List[Dict[str, Any]]:
    """Retrieves a full conversation thread."""
    collection = get_collection()
    return list(collection.find({"thread_id": thread_id}).sort("timestamp", 1))
