# Invoice Intelligence System - Architecture

## 🎯 System Overview

A unified intelligence system that combines **5 cutting-edge AI technologies** to provide intelligent document processing and multi-source querying capabilities.

### Core Technologies Integration

1. **LangChain** - Agent framework, tools, embeddings, LLM integration
2. **LangGraph** - Workflow orchestration with conditional routing
3. **MCP (FastMCP)** - Microservices architecture for agent tools
4. **Neuro-Symbolic AI** - Deterministic business rule validation
5. **Advanced RAG** - Semantic search with metadata filtering

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                             │
├──────────────────────────┬──────────────────────────────────────────┤
│   Ingestion UI           │   Query UI                               │
│   (localhost:8001)       │   (localhost:8002)                       │
│   - Upload documents     │   - Natural language queries             │
│   - View processing      │   - Multi-source routing                 │
└──────────┬───────────────┴──────────────┬───────────────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────────┐   ┌──────────────────────────────────────┐
│  INGESTION SERVICE       │   │  QUERY SERVICE                       │
│  (Port 8001)             │   │  (Port 8002)                         │
│                          │   │                                      │
│  ┌────────────────────┐  │   │  ┌────────────────────────────────┐ │
│  │   LangGraph        │  │   │  │   LangChain Agent              │ │
│  │   Orchestrator     │  │   │  │   (create_agent)               │ │
│  │                    │  │   │  │                                │ │
│  │   ┌──────────────┐ │  │   │  │   ┌──────────────────────────┐│ │
│  │   │ Ingestion    │ │  │   │  │   │  MongoDB Tools           ││ │
│  │   │ Node         │ │  │   │  │   │  - count_resumes()       ││ │
│  │   └──────┬───────┘ │  │   │  │   │  - search_by_skills()    ││ │
│  │          │         │  │   │  │   │  - get_all_resumes()     ││ │
│  │   ┌──────▼───────┐ │  │   │  │   └──────────────────────────┘│ │
│  │   │ OCR Node     │ │  │   │  │                                │ │
│  │   │ (Conditional)│ │  │   │  │   ┌──────────────────────────┐│ │
│  │   └──────┬───────┘ │  │   │  │   │  RAG Tools               ││ │
│  │          │         │  │   │  │   │  - query_invoices()      ││ │
│  │   ┌──────▼───────┐ │  │   │  │   │  - query_by_vendor()     ││ │
│  │   │ Structuring  │ │  │   │  │   └──────────────────────────┘│ │
│  │   │ Node (LLM)   │ │  │   │  │                                │ │
│  │   └──────┬───────┘ │  │   │  └────────────────────────────────┘ │
│  │          │         │  │   │                                      │
│  │   ┌──────▼───────┐ │  │   │  Intelligent Routing:                │
│  │   │ Validation   │ │  │   │  - Analyzes query intent             │
│  │   │ Node         │ │  │   │  - Selects appropriate tools         │
│  │   │ (Neuro-Sym)  │ │  │   │  - Executes and returns answer       │
│  │   └──────────────┘ │  │   │                                      │
│  └────────────────────┘  │   └──────────────────────────────────────┘
└──────────┬───────────────┘                      │
           │                                      │
           ▼                                      ▼
┌──────────────────────────┐   ┌──────────────────────────────────────┐
│  MCP SERVER              │   │  DATA SOURCES                        │
│  (Port 8000)             │   │                                      │
│                          │   │  ┌────────────────┬────────────────┐ │
│  FastMCP Tools:          │   │  │  MongoDB       │  RAG System    │ │
│  1. process_pdf()        │   │  │  (AI-HR)       │  (FAISS)       │ │
│  2. process_image()      │   │  │                │                │ │
│  3. process_excel()      │   │  │  Collections:  │  Components:   │ │
│  4. process_word()       │   │  │  - resumes     │  - Embeddings  │ │
│  5. perform_ocr()        │   │  │  - jds         │  - Chunking    │ │
│  6. structure_invoice()  │   │  │  - evaluations │  - Indexing    │ │
│  7. validate_invoice()   │   │  │  - users       │  - Retrieval   │ │
│                          │   │  └────────────────┴────────────────┘ │
└──────────────────────────┘   └──────────────────────────────────────┘
```

---

## 🔧 Technology Deep Dive

### 1. LangChain Integration

**Purpose**: Agent framework, tool orchestration, embeddings, LLM integration

**Components**:

#### A. Agent Creation (LangChain 1.2.6+)
```python
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage

agent = create_agent(
    model=llm,  # ChatGoogleGenerativeAI
    tools=tools,  # MongoDB + RAG tools
    system_prompt=system_prompt
)
```

#### B. Tool Definitions
```python
from langchain_core.tools import tool

@tool
def count_resumes() -> str:
    """Count total resumes in MongoDB."""
    # Implementation

@tool
def query_invoices(question: str) -> str:
    """Query invoice data using RAG."""
    # Implementation
```

#### C. Embeddings for RAG
```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=GOOGLE_API_KEY
)
```

#### D. Vector Store
```python
from langchain_community.vectorstores import FAISS

vector_store = FAISS.from_documents(
    documents=chunks,
    embedding=embeddings
)
```

**Key Features**:
- ✅ Tool-based agent architecture
- ✅ Automatic tool selection based on query
- ✅ Message-based invocation (HumanMessage/AIMessage)
- ✅ Semantic embeddings for RAG
- ✅ FAISS vector store integration

---

### 2. LangGraph Integration

**Purpose**: Workflow orchestration with conditional routing

**Implementation**:

```python
from langgraph.graph import StateGraph, END

# Define workflow
workflow = StateGraph(InvoiceState)

# Add nodes
workflow.add_node("ingestion", ingestion_node)
workflow.add_node("ocr", ocr_node)
workflow.add_node("structuring", structuring_node)
workflow.add_node("validation", validation_node)

# Add conditional edges
workflow.add_conditional_edges(
    "ingestion",
    route_after_ingestion,  # Decides: OCR or skip
    {
        "needs_ocr": "ocr",
        "skip_ocr": "structuring"
    }
)

# Compile graph
app = workflow.compile()
```

**Workflow Nodes**:

1. **Ingestion Node**: Extract text from documents
2. **OCR Node** (Conditional): Apply OCR if needed
3. **Structuring Node**: LLM-based data extraction
4. **Validation Node**: Neuro-symbolic rule checking

**Conditional Routing**:
```python
def route_after_ingestion(state: InvoiceState) -> str:
    if state["needs_ocr"]:
        return "needs_ocr"
    return "skip_ocr"
```

**Key Features**:
- ✅ State-based workflow management
- ✅ Conditional branching (OCR decision)
- ✅ Node-based processing pipeline
- ✅ Automatic state propagation
- ✅ Visual workflow representation

---

### 3. MCP (Model Context Protocol) Integration

**Purpose**: Microservices architecture for agent tools

**Implementation**:

```python
from fastmcp import FastMCP

mcp = FastMCP("Invoice Processing Tools")

@mcp.tool()
def process_pdf(file_path: str) -> str:
    """Extract text from PDF files."""
    # PyPDF2 implementation
    return extracted_text

@mcp.tool()
def perform_ocr(image_path: str) -> str:
    """Perform OCR using Azure Computer Vision."""
    # Azure CV implementation
    return ocr_text

@mcp.tool()
def structure_invoice(raw_text: str) -> str:
    """Structure invoice data using Gemini LLM."""
    # Gemini API call
    return structured_json

@mcp.tool()
def validate_invoice(invoice_data_json: str) -> str:
    """Apply neuro-symbolic validation rules."""
    # Business rules implementation
    return validation_results
```

**MCP Server**:
```python
if __name__ == "__main__":
    mcp.run(transport="stdio", port=8000)
```

**7 Agent Tools**:
1. `process_pdf()` - PDF text extraction
2. `process_image()` - Image processing
3. `process_excel()` - Excel data extraction
4. `process_word()` - Word document processing
5. `perform_ocr()` - Azure OCR integration
6. `structure_invoice()` - Gemini LLM structuring
7. `validate_invoice()` - Neuro-symbolic validation

**Key Features**:
- ✅ Microservices architecture
- ✅ Tool isolation and reusability
- ✅ Standardized tool interface
- ✅ Independent scaling
- ✅ Easy tool addition/removal

---

### 4. Neuro-Symbolic AI Integration

**Purpose**: Deterministic business rule validation

**Implementation**:

```python
def validate_invoice(invoice_data_json: str) -> str:
    """
    Apply 5 neuro-symbolic validation rules.
    Combines neural (LLM extraction) with symbolic (rule checking).
    """
    invoice_data = json.loads(invoice_data_json)
    validation_results = []
    
    # Rule 1: Total Calculation (Symbolic)
    if subtotal + tax == total (within tolerance):
        status = "PASS"
    else:
        status = "FAIL"
    
    # Rule 2: Positive Amounts (Symbolic)
    if total > 0:
        status = "PASS"
    
    # Rule 3: Required Fields (Symbolic)
    if vendor and invoice_date exist:
        status = "PASS"
    
    # Rule 4: Date Validity (Symbolic)
    if date_format_valid and date <= today:
        status = "PASS"
    
    # Rule 5: Line Items Consistency (Symbolic)
    if sum(line_items) == subtotal (within tolerance):
        status = "PASS"
    
    return validation_results
```

**5 Validation Rules**:

1. **Total Calculation**: `subtotal + tax = total` (±2% tolerance)
2. **Positive Amounts**: All amounts must be > 0
3. **Required Fields**: Vendor and invoice_date must exist
4. **Date Validity**: Date format valid and not in future
5. **Line Items Consistency**: Sum of line items ≈ subtotal

**Neuro-Symbolic Flow**:
```
Neural (LLM) → Extract data from document
     ↓
Symbolic (Rules) → Validate extracted data
     ↓
Result → PASS / FAIL / NEEDS_REVIEW
```

**Key Features**:
- ✅ Deterministic validation (no LLM hallucination)
- ✅ Business rule enforcement
- ✅ Explainable results
- ✅ Fast execution (no API calls)
- ✅ Combines neural extraction with symbolic validation

---

### 5. Advanced RAG Integration

**Purpose**: Semantic search with metadata filtering

**Implementation**:

#### A. Document Chunking
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=128,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = text_splitter.create_documents(
    texts=[document_text],
    metadatas=[{
        "doc_id": doc_id,
        "vendor": vendor,
        "invoice_date": invoice_date,
        "total": total
    }]
)
```

#### B. Embedding & Indexing
```python
# Create embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004"
)

# Create FAISS index
vector_store = FAISS.from_documents(
    documents=chunks,
    embedding=embeddings
)

# Save index
vector_store.save_local("data/vector_store/faiss_index")
```

#### C. Semantic Retrieval
```python
def query(self, query: str, metadata_filter: dict = None):
    # Retrieve relevant chunks
    if metadata_filter:
        docs = self.vector_store.similarity_search(
            query,
            k=5,
            filter=metadata_filter
        )
    else:
        docs = self.vector_store.similarity_search(query, k=5)
    
    # Generate answer using LLM
    context = "\n\n".join([doc.page_content for doc in docs])
    answer = self.llm.invoke(f"Context: {context}\n\nQuestion: {query}")
    
    return answer
```

#### D. Metadata Filtering
```python
# Query specific vendor
result = rag_system.query(
    "What is the total amount?",
    metadata_filter={"vendor": "Acme Corporation"}
)

# Query specific date range
result = rag_system.query(
    "Show invoices from January",
    metadata_filter={"invoice_date": {"$gte": "2024-01-01"}}
)
```

**RAG Components**:

1. **Semantic Chunking**: Intelligent text splitting with overlap
2. **Metadata Enrichment**: Document metadata for filtering
3. **Vector Embeddings**: text-embedding-004 model
4. **FAISS Index**: Fast similarity search
5. **Context Retrieval**: Top-K relevant chunks
6. **LLM Generation**: Answer synthesis from context

**Key Features**:
- ✅ Multi-document indexing
- ✅ Semantic search (not keyword matching)
- ✅ Metadata filtering (vendor, date, amount)
- ✅ Persistent FAISS index
- ✅ Confidence scoring
- ✅ Context-aware answers

---

## 🔄 Data Flow

### Ingestion Flow (Document Upload)

```
1. User uploads document (PDF/DOCX/XLSX/Image)
   ↓
2. LangGraph Orchestrator starts workflow
   ↓
3. Ingestion Node (MCP Tool)
   - Extracts text using appropriate tool
   - Sets needs_ocr flag
   ↓
4. Conditional Routing
   - If needs_ocr → OCR Node (Azure CV)
   - Else → Skip to Structuring
   ↓
5. Structuring Node (MCP Tool + LLM)
   - Gemini extracts structured data
   - Returns JSON with fields
   ↓
6. Validation Node (Neuro-Symbolic)
   - Applies 5 business rules
   - Returns PASS/FAIL/NEEDS_REVIEW
   ↓
7. RAG Indexing (LangChain)
   - Chunks document
   - Creates embeddings
   - Adds to FAISS index
   ↓
8. Result returned to user
```

### Query Flow (User Question)

```
1. User asks question in natural language
   ↓
2. LangChain Agent receives query
   ↓
3. Agent analyzes intent and selects tools
   ↓
4. Tool Execution:
   
   MongoDB Tools (HR queries):
   - count_resumes()
   - search_by_skills()
   - get_all_resumes()
   - etc.
   
   RAG Tools (Invoice queries):
   - query_invoices()
   - query_by_vendor()
   - etc.
   ↓
5. Agent synthesizes answer
   ↓
6. Response returned with source attribution
```

---

## 🎯 Key Design Decisions

### 1. Separate Services Architecture

**Decision**: Split into 3 independent services (Ingestion, Query, MCP)

**Rationale**:
- Independent scaling
- Clear separation of concerns
- Easier maintenance
- Microservices pattern

### 2. LangChain 1.2.6+ API

**Decision**: Use `create_agent()` with message-based invocation

**Rationale**:
- Future-proof (latest API)
- Better conversation history
- More flexible tool integration
- Recommended by LangChain

### 3. Neuro-Symbolic Validation

**Decision**: Combine LLM extraction with rule-based validation

**Rationale**:
- Prevents LLM hallucination in validation
- Deterministic business rules
- Explainable results
- Fast execution (no API calls)

### 4. FAISS for Vector Store

**Decision**: Use FAISS instead of cloud vector DB

**Rationale**:
- Local storage (no external dependencies)
- Fast similarity search
- Persistent index
- Cost-effective

### 5. MongoDB for Structured Data

**Decision**: Use MongoDB for HR data, RAG for invoices

**Rationale**:
- Structured data → Database queries
- Unstructured data → Semantic search
- Best tool for each use case
- Unified query interface

---

## 📊 Technology Matrix

| Technology | Component | Purpose | Integration Point |
|------------|-----------|---------|-------------------|
| **LangChain** | Agent Framework | Tool orchestration, embeddings | `query_router.py` |
| **LangChain** | RAG System | Semantic search | `rag_system.py` |
| **LangGraph** | Workflow | Document processing pipeline | `orchestrator.py` |
| **FastMCP** | Microservices | Agent tools backend | `mcp_server.py` |
| **Neuro-Symbolic** | Validation | Business rule checking | `validate_invoice()` |
| **FAISS** | Vector Store | Similarity search | `rag_system.py` |
| **MongoDB** | Database | Structured data storage | `query_router.py` |
| **Gemini** | LLM | Text generation, structuring | All components |

---

## 🚀 System Capabilities

### Multi-Source Querying

**MongoDB Queries** (Structured Data):
- "How many resumes do we have?"
- "Find candidates with Python skills"
- "List all job descriptions"
- "Show me candidates named John"

**RAG Queries** (Unstructured Data):
- "What is the total invoice amount?"
- "Who is the vendor for invoice INV-001?"
- "Show me all invoices from Acme Corp"
- "What items were purchased?"

### Intelligent Routing

The LangChain agent automatically:
1. Analyzes query intent
2. Selects appropriate tools (MongoDB or RAG)
3. Executes tools
4. Synthesizes answer
5. Attributes source

### Document Processing

Supports multiple formats:
- PDF (text extraction)
- DOCX (Word documents)
- XLSX (Excel spreadsheets)
- PNG/JPG (OCR with Azure CV)

### Validation & Quality

5 neuro-symbolic rules ensure:
- Mathematical accuracy
- Data completeness
- Business logic compliance
- Date validity
- Consistency checks

---

## 🎓 Learning Outcomes

This system demonstrates:

1. ✅ **LangChain Agent Architecture** - Tool-based agents with create_agent()
2. ✅ **LangGraph Workflows** - Conditional routing and state management
3. ✅ **MCP Microservices** - Tool isolation and reusability
4. ✅ **Neuro-Symbolic AI** - Combining neural and symbolic approaches
5. ✅ **Advanced RAG** - Semantic search with metadata filtering
6. ✅ **Multi-Source Integration** - Unified querying across data sources
7. ✅ **Production Patterns** - Logging, error handling, separation of concerns

---

## 📝 Summary

This invoice intelligence system showcases the **effective and meaningful integration** of 5 cutting-edge AI technologies:

- **LangChain** provides the agent framework and RAG capabilities
- **LangGraph** orchestrates complex document processing workflows
- **MCP** enables microservices architecture for agent tools
- **Neuro-Symbolic AI** ensures deterministic validation
- **Advanced RAG** enables semantic search across documents

The result is a **production-ready, scalable, intelligent system** that can process documents, validate data, and answer questions across multiple data sources with a unified natural language interface.

---

**Architecture Version**: 2.0  
**Last Updated**: February 2, 2026  
**LangChain Version**: 1.2.6+  
**Status**: Production Ready ✅
