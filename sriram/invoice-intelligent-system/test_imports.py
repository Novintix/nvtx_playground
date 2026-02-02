"""
Test all imports to ensure system is ready
"""

print("=" * 70)
print("🧪 Testing Invoice Intelligence System Imports")
print("=" * 70)

# Test 1: Core modules
print("\n1️⃣ Testing core modules...")
try:
    import config
    print("   ✅ config")
except Exception as e:
    print(f"   ❌ config: {e}")

try:
    import logger
    print("   ✅ logger")
except Exception as e:
    print(f"   ❌ logger: {e}")

# Test 2: LangChain components
print("\n2️⃣ Testing LangChain components...")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("   ✅ ChatGoogleGenerativeAI")
except Exception as e:
    print(f"   ❌ ChatGoogleGenerativeAI: {e}")

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    print("   ✅ HuggingFaceEmbeddings")
except Exception as e:
    print(f"   ❌ HuggingFaceEmbeddings: {e}")

try:
    from langchain.agents import create_agent
    print("   ✅ create_agent")
except Exception as e:
    print(f"   ❌ create_agent: {e}")

# Test 3: LangGraph
print("\n3️⃣ Testing LangGraph...")
try:
    from langgraph.graph import StateGraph, END
    print("   ✅ StateGraph, END")
except Exception as e:
    print(f"   ❌ LangGraph: {e}")

# Test 4: FastMCP
print("\n4️⃣ Testing FastMCP...")
try:
    from fastmcp import FastMCP, Client
    print("   ✅ FastMCP, Client")
except Exception as e:
    print(f"   ❌ FastMCP: {e}")

# Test 5: FAISS
print("\n5️⃣ Testing FAISS...")
try:
    from langchain_community.vectorstores import FAISS
    print("   ✅ FAISS")
except Exception as e:
    print(f"   ❌ FAISS: {e}")

# Test 6: System modules
print("\n6️⃣ Testing system modules...")
try:
    from orchestrator import process_document
    print("   ✅ orchestrator")
except Exception as e:
    print(f"   ❌ orchestrator: {e}")

try:
    from rag_system import AdvancedRAGSystem
    print("   ✅ rag_system")
except Exception as e:
    print(f"   ❌ rag_system: {e}")

try:
    from query_router import get_router
    print("   ✅ query_router")
except Exception as e:
    print(f"   ❌ query_router: {e}")

# Test 7: API modules
print("\n7️⃣ Testing API modules...")
try:
    import api
    print("   ✅ api (Ingestion Service)")
except Exception as e:
    print(f"   ❌ api: {e}")

try:
    import query_service
    print("   ✅ query_service (Query Service)")
except Exception as e:
    print(f"   ❌ query_service: {e}")

try:
    import mcp_server
    print("   ✅ mcp_server (MCP Server)")
except Exception as e:
    print(f"   ❌ mcp_server: {e}")

print("\n" + "=" * 70)
print("✅ All imports successful! System is ready to run.")
print("=" * 70)
print("\n🚀 To start the system:")
print("   python start_all_services.py")
print("\n   Or start individually:")
print("   Terminal 1: python mcp_server.py")
print("   Terminal 2: python api.py")
print("   Terminal 3: python query_service.py")
print("=" * 70)
