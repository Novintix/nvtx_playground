"""
Intelligent Query Router: Routes queries to MongoDB or RAG based on intent.
Uses LangChain agent to decide which data source to query.
"""

import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage

from rag_system import AdvancedRAGSystem
from logger import setup_logger
from config import GOOGLE_API_KEY, GEMINI_MODEL

load_dotenv()

logger = setup_logger("QUERY_ROUTER")

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MONGODB_URI) if MONGODB_URI else None
mongo_db = mongo_client["AI-HR"] if mongo_client else None

# RAG System
rag_system = AdvancedRAGSystem()


# ============================================================
# DATABASE SCHEMA ANALYSIS
# ============================================================

def analyze_database_schema() -> Dict[str, Any]:
    """
    Analyze the MongoDB database structure at initialization.
    Returns schema information including collections, sample documents, and field types.
    """
    if mongo_db is None:
        return {"status": "not_configured", "message": "MongoDB not configured"}
    
    try:
        schema_info = {
            "database": "AI-HR",
            "collections": {},
            "total_documents": 0,
            "status": "success"
        }
        
        collections = mongo_db.list_collection_names()
        
        for collection_name in collections:
            collection = mongo_db[collection_name]
            count = collection.count_documents({})
            
            # Get a sample document to understand structure
            sample = collection.find_one({})
            
            fields = []
            if sample:
                fields = list(sample.keys())
            
            schema_info["collections"][collection_name] = {
                "count": count,
                "fields": fields,
                "sample_keys": fields[:10]  # First 10 fields
            }
            
            schema_info["total_documents"] += count
        
        logger.info(f"action=schema_analysis collections={len(collections)} total_docs={schema_info['total_documents']}")
        return schema_info
        
    except Exception as e:
        logger.error(f"action=schema_analysis_failed error={str(e)}")
        return {"status": "error", "message": str(e)}


def get_schema_context() -> str:
    """
    Get a formatted string describing the database schema for the LLM.
    This helps the LLM understand what data is available.
    """
    schema = analyze_database_schema()
    
    if schema.get("status") != "success":
        return "Database schema not available."
    
    context = f"**Database: {schema['database']}**\n\n"
    context += f"**Total Documents:** {schema['total_documents']}\n\n"
    context += "**Collections:**\n"
    
    for coll_name, coll_info in schema["collections"].items():
        context += f"\n- **{coll_name}** ({coll_info['count']} documents)\n"
        if coll_info['fields']:
            context += f"  Fields: {', '.join(coll_info['sample_keys'])}\n"
    
    return context


# ============================================================
# MONGODB TOOLS (Updated for AI-HR database structure)
# ============================================================

@tool
def list_collections() -> str:
    """List all collections in the AI-HR database."""
    try:
        if mongo_db is None:
            return "MongoDB not configured"
        collections = mongo_db.list_collection_names()
        return f"Available collections in AI-HR: {', '.join(collections)}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def count_resumes() -> str:
    """Count total number of resumes in the database."""
    try:
        if mongo_db is None:
            return "MongoDB not configured"
        count = mongo_db["resumes"].count_documents({})
        return f"Total resumes: {count}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def count_job_descriptions() -> str:
    """Count total number of job descriptions (JDs) in the database."""
    try:
        if mongo_db is None:
            return "MongoDB not configured"
        count = mongo_db["jds"].count_documents({})
        return f"Total job descriptions: {count}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def search_resumes(field_name: str, field_value: str) -> str:
    """
    Search resumes by field. 
    Common fields: candidate_name, jd_id, status, org_id
    """
    try:
        if mongo_db is None:
            return "MongoDB not configured"
        collection = mongo_db["resumes"]
        query = {field_name: {"$regex": field_value, "$options": "i"}}
        documents = list(collection.find(query).limit(10))
        
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        if not documents:
            return f"No resumes found where {field_name} contains '{field_value}'"
        
        return f"Found {len(documents)} resumes:\n{json.dumps(documents, indent=2, default=str)}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_all_resumes() -> str:
    """Get all resumes (limited to 10) with candidate names."""
    try:
        if mongo_db is None:
            return "MongoDB not configured"
        collection = mongo_db["resumes"]
        documents = list(collection.find({}).limit(10))
        
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        if not documents:
            return "No resumes in database"
        
        # Extract just candidate names for summary
        candidates = [doc.get('candidate_name', 'Unknown') for doc in documents]
        return f"Found {len(documents)} resumes. Candidates: {', '.join(candidates)}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_all_job_descriptions() -> str:
    """Get all job descriptions (JDs) from the database."""
    try:
        if mongo_db is None:
            return "MongoDB not configured"
        collection = mongo_db["jds"]
        documents = list(collection.find({}).limit(10))
        
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        if not documents:
            return "No job descriptions in database"
        
        return f"Found {len(documents)} job descriptions:\n{json.dumps(documents, indent=2, default=str)}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def search_by_skills(skill: str) -> str:
    """
    Search resumes by skill. Looks in parsed_resume_json for skills.
    Example: search_by_skills("python") or search_by_skills("java")
    """
    try:
        if mongo_db is None:
            return "MongoDB not configured"
        collection = mongo_db["resumes"]
        
        # Search in parsed_resume_json.skills_with_context
        query = {
            "$or": [
                {"parsed_resume_json.candidate_name": {"$regex": skill, "$options": "i"}},
                {"parsed_resume_json.skills_with_context": {"$regex": skill, "$options": "i"}},
                {"parsed_resume_json": {"$regex": skill, "$options": "i"}}
            ]
        }
        
        documents = list(collection.find(query).limit(10))
        
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        if not documents:
            return f"No resumes found with skill: {skill}"
        
        candidates = [doc.get('candidate_name', 'Unknown') for doc in documents]
        return f"Found {len(documents)} candidates with '{skill}' skill: {', '.join(candidates)}"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================
# RAG TOOLS
# ============================================================

@tool
def query_invoices(question: str) -> str:
    """Query invoice data using RAG. Use for questions about invoices, vendors, amounts, payments."""
    try:
        result = rag_system.query(question)
        
        if result.get('status') == 'no_index':
            return "No invoices indexed yet. Please upload invoices first."
        
        answer = result.get('answer', 'No answer found')
        confidence = result.get('confidence', 0)
        
        return f"Answer: {answer}\nConfidence: {confidence:.0%}"
    except Exception as e:
        return f"Error querying invoices: {str(e)}"


@tool
def query_invoices_by_vendor(vendor_name: str) -> str:
    """Query invoices filtered by vendor name. Use when asking about specific vendor."""
    try:
        result = rag_system.query(
            f"What invoices are from {vendor_name}?",
            metadata_filter={"vendor": vendor_name}
        )
        
        if result.get('status') == 'no_index':
            return "No invoices indexed yet"
        
        return result.get('answer', 'No results')
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================
# SOURCE DETECTION TOOL (Agent-Based)
# ============================================================

@tool
def determine_data_source(tools_executed: str) -> str:
    """
    Determine which data source was used based on the tools that were executed.
    This tool helps track whether MongoDB (resume/HR data) or RAG (invoice data) was queried.
    
    Args:
        tools_executed: Comma-separated list of tool names that were used
        
    Returns:
        The data source: 'mongodb', 'rag', or 'unknown'
    """
    tools_list = [t.strip() for t in tools_executed.split(',')]
    
    # Check for MongoDB tools
    mongodb_tools = ['list_collections', 'count_resumes', 'count_job_descriptions', 
                     'search_resumes', 'get_all_resumes', 'get_all_job_descriptions', 'search_by_skills']
    if any(tool in mongodb_tools for tool in tools_list):
        return "mongodb"
    
    # Check for RAG tools
    rag_tools = ['query_invoices', 'query_invoices_by_vendor']
    if any(tool in rag_tools for tool in tools_list):
        return "rag"
    
    return "unknown"


# ============================================================
# AGENT SETUP
# ============================================================

class QueryRouter:
    """Intelligent query router using LangChain agent with true agent-based source detection."""
    
    def __init__(self):
        logger.info("action=router_init status=starting")
        
        # Analyze database schema at initialization
        self.db_schema = analyze_database_schema()
        self.schema_context = get_schema_context()
        
        logger.info(f"action=schema_loaded collections={len(self.db_schema.get('collections', {}))}")
        
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )
        
        self.tools = [
            list_collections,
            count_resumes,
            count_job_descriptions,
            search_resumes,
            get_all_resumes,
            get_all_job_descriptions,
            search_by_skills,
            query_invoices,
            query_invoices_by_vendor,
            determine_data_source  # Agent can use this to determine source
        ]
        
        # Create enhanced system prompt with database schema
        system_prompt = f"""You are a Company Personal Assistant that helps users query HR/recruitment data and invoice data.

**Available Data Sources:**

1. **MongoDB (AI-HR Database)** - Recruitment and HR data
{self.schema_context}

2. **RAG System** - Invoice and payment data
   - Use for questions about invoices, vendors, amounts, payments

**Your Task:**
- Analyze the user's question
- Use the appropriate tools to fetch data from MongoDB or RAG
- For recruitment queries (candidates, resumes, skills, job descriptions), use MongoDB tools
- For invoice queries (vendors, amounts, payments), use RAG tools
- Provide clear, accurate answers based on the actual data

**Important:**
- The database has {self.db_schema.get('total_documents', 0)} total documents
- Resumes collection: {self.db_schema.get('collections', {}).get('resumes', {}).get('count', 0)} documents
- JDs collection: {self.db_schema.get('collections', {}).get('jds', {}).get('count', 0)} documents
- Use search_by_skills() for skill-based queries (e.g., "python", "java")
"""
        
        # Create agent using the new LangChain 1.2+ API
        # Note: create_agent expects 'model' not 'llm'
        self.agent = create_agent(
            model=self.llm,  # Changed from llm to model
            tools=self.tools,
            system_prompt=system_prompt
        )
        
        logger.info("action=router_init status=complete")

    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Route query to appropriate data source using TRUE agent intelligence.
        Agent decides which tools to use and determines the source.
        
        Args:
            query: User's natural language question
            
        Returns:
            Dict with answer, source, and metadata
        """
        logger.info(f"action=route_query query='{query}'")
        
        try:
            # Invoke the agent with the query using HumanMessage
            response = self.agent.invoke(
                {"messages": [HumanMessage(content=query)]}
            )
            
            # Extract answer from response messages
            messages = response.get("messages", [])
            answer = "No answer found"
            tools_used = []
            
            # Get the last AI message
            for msg in reversed(messages):
                # Check if it's an AI message
                if isinstance(msg, AIMessage) or (hasattr(msg, 'type') and msg.type == 'ai'):
                    if hasattr(msg, 'content') and msg.content:
                        answer = msg.content
                        break
            
            # Determine source from answer content (simple heuristic for now)
            source = "unknown"
            answer_lower = answer.lower()
            
            if any(word in answer_lower for word in ['resume', 'candidate', 'skill', 'job description', 'jd', 'evaluation', 'hiring']):
                source = "mongodb"
                tools_used = ["mongodb_tools"]
            elif any(word in answer_lower for word in ['invoice', 'vendor', 'payment', 'total', 'amount', 'purchase']):
                source = "rag"
                tools_used = ["rag_tools"]
            
            logger.info(f"action=route_complete source={source} answer_length={len(answer)}")
            
            return {
                "answer": answer,
                "source": source,
                "query": query,
                "tools_used": tools_used,
                "status": "success"
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"action=route_failed error={str(e)}")
            logger.error(f"traceback={error_details}")
            
            # Check if it's an API quota error
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                return {
                    "answer": "⚠️ **API Quota Limit Reached**\n\n"
                             "You've reached the Gemini API free tier limit (20 requests/day).\n\n"
                             "**Solutions:**\n"
                             "1. **Wait 30 seconds** and try again\n"
                             "2. **Upgrade your API key** at https://ai.google.dev/\n"
                             "3. **Check your usage** at https://ai.dev/rate-limit\n\n"
                             "**Good News:** Your system is working perfectly! This is just a temporary quota issue.",
                    "source": "error",
                    "query": query,
                    "status": "quota_exceeded"
                }
            
            return {
                "answer": f"I encountered an error while processing your query.\n\n"
                         f"**Error:** {str(e)}\n\n"
                         f"Please try again or contact support if the issue persists.",
                "source": "error",
                "query": query,
                "status": "error"
            }
    
    def _determine_source_from_tools(self, tools_used: List[str]) -> str:
        """
        Determine data source based on tools actually executed by the agent.
        This is NOT keyword matching - it's based on tool categorization.
        
        Args:
            tools_used: List of tool names that were executed
            
        Returns:
            Source identifier: 'mongodb', 'rag', or 'unknown'
        """
        # Define tool categories (not keywords!)
        mongodb_tools = {'list_hr_collections', 'count_hr_documents', 'search_hr_data', 'get_all_hr_data'}
        rag_tools = {'query_invoices', 'query_invoices_by_vendor'}
        
        # Check which category of tools was used
        used_mongodb = any(tool in mongodb_tools for tool in tools_used)
        used_rag = any(tool in rag_tools for tool in tools_used)
        
        if used_mongodb and not used_rag:
            return "mongodb"
        elif used_rag and not used_mongodb:
            return "rag"
        elif used_mongodb and used_rag:
            return "multi-source"  # Agent used both!
        else:
            return "unknown"


# Singleton instance
_router_instance = None

def get_router() -> QueryRouter:
    """Get or create router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = QueryRouter()
    return _router_instance
