import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

mcp = FastMCP("mongodb_mcp_server")


def get_mongo_client() -> MongoClient:
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return MongoClient(uri)


def get_database(db_name: str) -> Any:
    client = get_mongo_client()
    return client[db_name]


def get_collection(db_name: str, collection_name: str) -> Any:
    db = get_database(db_name)
    return db[collection_name]


@mcp.tool()
def ping() -> str:
    """Ping the MongoDB server to check connectivity."""
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        return "MongoDB connection successful"
    except ConnectionFailure as e:
        return f"MongoDB connection failed: {str(e)}"


@mcp.tool()
def list_databases() -> List[str]:
    """List all databases in the MongoDB instance."""
    try:
        client = get_mongo_client()
        return client.list_database_names()
    except Exception as e:
        raise RuntimeError(f"Failed to list databases: {str(e)}")


@mcp.tool()
def list_collections(db_name: str) -> List[str]:
    """List all collections in a specific database."""
    try:
        db = get_database(db_name)
        return db.list_collection_names()
    except Exception as e:
        raise RuntimeError(f"Failed to list collections in {db_name}: {str(e)}")


@mcp.tool()
def find_documents(db_name: str, collection_name: str, query: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Find documents in a collection matching the query."""
    try:
        collection = get_collection(db_name, collection_name)
        if query is None:
            query = {}
        cursor = collection.find(query).limit(limit)
        return list(cursor)
    except Exception as e:
        raise RuntimeError(f"Failed to find documents: {str(e)}")


@mcp.tool()
def count_documents(db_name: str, collection_name: str, query: Optional[Dict[str, Any]] = None) -> int:
    """Count documents in a collection matching the query."""
    try:
        collection = get_collection(db_name, collection_name)
        if query is None:
            query = {}
        return collection.count_documents(query)
    except Exception as e:
        raise RuntimeError(f"Failed to count documents: {str(e)}")


@mcp.tool()
def find_one_document(db_name: str, collection_name: str, query: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Find one document in a collection matching the query."""
    try:
        collection = get_collection(db_name, collection_name)
        if query is None:
            query = {}
        return collection.find_one(query)
    except Exception as e:
        raise RuntimeError(f"Failed to find document: {str(e)}")


@mcp.tool()
def get_collection_stats(db_name: str, collection_name: str) -> Dict[str, Any]:
    """Get statistics for a collection."""
    try:
        collection = get_collection(db_name, collection_name)
        return collection.database.command("collStats", collection_name)
    except Exception as e:
        raise RuntimeError(f"Failed to get collection stats: {str(e)}")


@mcp.tool()
def aggregate_documents(db_name: str, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Perform aggregation on a collection using a pipeline."""
    try:
        collection = get_collection(db_name, collection_name)
        cursor = collection.aggregate(pipeline)
        return list(cursor)
    except Exception as e:
        raise RuntimeError(f"Failed to aggregate documents: {str(e)}")


# Write and edit tools are commented out as requested
# @mcp.tool()
# def insert_document(db_name: str, collection_name: str, document: Dict[str, Any]) -> str:
#     """Insert a document into a collection."""
#     try:
#         collection = get_collection(db_name, collection_name)
#         result = collection.insert_one(document)
#         return f"Inserted document with ID: {result.inserted_id}"
#     except Exception as e:
#         raise RuntimeError(f"Failed to insert document: {str(e)}")

# @mcp.tool()
# def update_document(db_name: str, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> str:
#     """Update documents in a collection."""
#     try:
#         collection = get_collection(db_name, collection_name)
#         result = collection.update_many(query, {"$set": update})
#         return f"Updated {result.modified_count} documents"
#     except Exception as e:
#         raise RuntimeError(f"Failed to update documents: {str(e)}")

# @mcp.tool()
# def delete_documents(db_name: str, collection_name: str, query: Dict[str, Any]) -> str:
#     """Delete documents from a collection."""
#     try:
#         collection = get_collection(db_name, collection_name)
#         result = collection.delete_many(query)
#         return f"Deleted {result.deleted_count} documents"
#     except Exception as e:
#         raise RuntimeError(f"Failed to delete documents: {str(e)}")

# @mcp.tool()
# def create_collection(db_name: str, collection_name: str) -> str:
#     """Create a new collection in a database."""
#     try:
#         db = get_database(db_name)
#         db.create_collection(collection_name)
#         return f"Created collection: {collection_name}"
#     except Exception as e:
#         raise RuntimeError(f"Failed to create collection: {str(e)}")

# @mcp.tool()
# def drop_collection(db_name: str, collection_name: str) -> str:
#     """Drop a collection from a database."""
#     try:
#         collection = get_collection(db_name, collection_name)
#         collection.drop()
#         return f"Dropped collection: {collection_name}"
#     except Exception as e:
#         raise RuntimeError(f"Failed to drop collection: {str(e)}")


if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
