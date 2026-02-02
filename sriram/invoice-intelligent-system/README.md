# Invoice Intelligence System

A unified AI system integrating **LangChain**, **LangGraph**, **MCP**, **Neuro-Symbolic AI**, and **Advanced RAG** for intelligent document processing and multi-source querying.

## 📚 Documentation

**→ See [ARCHITECTURE.md](ARCHITECTURE.md) for complete system architecture and technology integration details.**

## 🎯 Quick Overview

### System Components

1. **Ingestion Service** (Port 8001) - Document upload and processing
2. **Query Service** (Port 8002) - Intelligent multi-source querying  
3. **MCP Server** (Port 8000) - Agent tools backend

### Technology Stack

| Technology | Purpose |
|------------|---------|
| **LangChain** | Agent framework, RAG, embeddings |
| **LangGraph** | Workflow orchestration |
| **FastMCP** | Microservices for agent tools |
| **Neuro-Symbolic AI** | Business rule validation |
| **Advanced RAG** | Semantic search with FAISS |

### Data Sources

- **MongoDB** (AI-HR database) - Structured data (resumes, job descriptions)
- **RAG/FAISS** - Unstructured data (invoices, documents)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key
MONGODB_URI=your_mongodb_connection_string
AZURE_CV_ENDPOINT=your_azure_cv_endpoint
AZURE_CV_KEY=your_azure_cv_key
```

### 3. Start Services

```bash
# Terminal 1: MCP Server
python mcp_server.py

# Terminal 2: Ingestion Service
python api.py

# Terminal 3: Query Service
python query_service.py
```

### 4. Access UIs

- **Ingestion**: http://localhost:8001
- **Query**: http://localhost:8002

## 💡 Example Queries

### MongoDB Queries (HR Data)
```
How many resumes do we have?
Find candidates with Python skills
List all job descriptions
```

### RAG Queries (Invoice Data)
```
What is the total invoice amount?
Who is the vendor?
Show me all invoices from Acme Corporation
```

## 📖 Learn More

**For detailed architecture, technology integration, and design decisions:**

→ **[Read ARCHITECTURE.md](ARCHITECTURE.md)**

## 📦 Project Structure

```
invoice-intelligence-system/
├── api.py                  # Ingestion service (Port 8001)
├── query_service.py        # Query service (Port 8002)
├── mcp_server.py           # MCP tools server (Port 8000)
├── orchestrator.py         # LangGraph workflow
├── query_router.py         # LangChain agent
├── rag_system.py           # RAG implementation
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── ARCHITECTURE.md         # 📚 Complete architecture guide
└── README.md               # This file
```

## 🎓 Key Features

✅ **True Agent Intelligence** - LangChain agent with tool selection  
✅ **Workflow Orchestration** - LangGraph conditional routing  
✅ **Microservices Architecture** - FastMCP tool isolation  
✅ **Deterministic Validation** - Neuro-symbolic business rules  
✅ **Semantic Search** - Advanced RAG with metadata filtering  
✅ **Multi-Source Querying** - Unified interface for MongoDB + RAG  
✅ **Production Ready** - Logging, error handling, separation of concerns  

## 📝 Status

- ✅ All 5 technologies integrated effectively
- ✅ MongoDB integration working (AI-HR database)
- ✅ RAG system operational (FAISS index)
- ✅ LangChain 1.2.6+ compatible
- ✅ Production-ready architecture

---

**For complete architecture details, technology deep-dive, and design decisions:**  
**→ [ARCHITECTURE.md](ARCHITECTURE.md)**
