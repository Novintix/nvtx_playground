"""
System Verification Script
Checks that all components are properly configured and ready to run
"""

import sys
from pathlib import Path

def check_file(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} MISSING: {filepath}")
        return False

def check_env():
    """Check .env configuration."""
    if not Path(".env").exists():
        print("❌ .env file not found!")
        print("   Create .env with: GOOGLE_API_KEY=your_key_here")
        return False
    
    with open(".env", "r") as f:
        content = f.read()
        
    has_google_key = "GOOGLE_API_KEY" in content
    
    if has_google_key:
        print("✅ .env file configured with GOOGLE_API_KEY")
        return True
    else:
        print("❌ .env missing GOOGLE_API_KEY")
        return False

def check_imports():
    """Check if required packages are installed."""
    packages = {
        "langchain": "LangChain",
        "langgraph": "LangGraph",
        "fastmcp": "FastMCP",
        "faiss": "FAISS",
        "fastapi": "FastAPI",
        "pymongo": "PyMongo (optional)",
    }
    
    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✅ {name} installed")
        except ImportError:
            if package == "pymongo":
                print(f"⚠️  {name} not installed (optional for HR data)")
            else:
                print(f"❌ {name} NOT installed")
                all_ok = False
    
    return all_ok

def main():
    print("=" * 70)
    print("🔍 Invoice Intelligence System - Verification")
    print("=" * 70)
    
    all_checks = []
    
    # Check core files
    print("\n📁 Checking Core Files...")
    all_checks.append(check_file("mcp_server.py", "MCP Server"))
    all_checks.append(check_file("api.py", "Ingestion Service"))
    all_checks.append(check_file("query_service.py", "Query Service"))
    all_checks.append(check_file("orchestrator.py", "LangGraph Orchestrator"))
    all_checks.append(check_file("rag_system.py", "RAG System"))
    all_checks.append(check_file("query_router.py", "Query Router"))
    all_checks.append(check_file("config.py", "Configuration"))
    all_checks.append(check_file("logger.py", "Logger"))
    
    # Check configuration
    print("\n⚙️  Checking Configuration...")
    all_checks.append(check_env())
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    all_checks.append(check_imports())
    
    # Check documentation
    print("\n📚 Checking Documentation...")
    check_file("README.md", "README")
    check_file("DEPLOYMENT_GUIDE.md", "Deployment Guide")
    check_file("SYSTEM_READY.md", "System Ready Status")
    
    # Final verdict
    print("\n" + "=" * 70)
    if all(all_checks):
        print("✅ ALL CHECKS PASSED - System is Ready!")
        print("=" * 70)
        print("\n🚀 To start the system:")
        print("   python start_all_services.py")
        print("\n   Or start services individually:")
        print("   Terminal 1: python mcp_server.py")
        print("   Terminal 2: python api.py")
        print("   Terminal 3: python query_service.py")
        print("\n📖 Read DEPLOYMENT_GUIDE.md for detailed instructions")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please fix the issues above")
        print("=" * 70)
        print("\n📖 See DEPLOYMENT_GUIDE.md for setup instructions")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
