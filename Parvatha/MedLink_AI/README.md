# 🧬 MedLink AI  
**Medical Research Literature Navigator using Multi-Hop RAG**

MedLink AI is an **agentic, evidence-grounded Retrieval-Augmented Generation (RAG) system** that helps medical researchers explore, connect, and synthesize biomedical literature from **PubMed** using real research papers.

> Built to reduce literature review time, surface hidden connections, and generate mechanistic, evidence-based answers — without hallucinations.

---

## ✨ Key Capabilities

- 🔍 **Hybrid Retrieval**
  - Semantic search (PubMedBERT + FAISS)
  - Keyword-based PubMed retrieval
- 🔗 **Multi-Hop Reasoning**
  - Iterative query expansion using LangGraph
  - Discovers non-obvious cross-paper links
- 🧠 **Evidence-Grounded Answers**
  - Generated strictly from retrieved abstracts
  - No fabricated citations
- ⚖️ **Intelligent Re-Ranking**
  - Relevance, recency, journal quality, citation signals
- 📊 **Justification Score**
  - Confidence score backed by specific research papers
- 💾 **Persistent Caching**
  - SQLite-based query & paper cache
- 🖥️ **Professional UI**
  - Streamlit interface designed for medical research workflows

---

## 🏗️ Tech Stack

### AI & Orchestration
- **Python**
- **LangChain**
- **LangGraph** (agent orchestration)
- **Retrieval-Augmented Generation (RAG)**

### Models
- **PubMedBERT** – biomedical embeddings  
- **LLaMA 3.1 (Groq API)** – reasoning & synthesis  

### Search & Storage
- **FAISS** – vector similarity search  
- **SQLite** – caching, metadata, scoring  

### Data Source
- **PubMed / NCBI** (Biopython Entrez API)

### Frontend
- **Streamlit** (custom medical-themed UI)

---

## 🧠 How It Works (High Level)
<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/45c774b2-714b-454c-8346-914e238a9e47" />


## 🚀 Getting Started

###
1️⃣ Install Dependencies
 - pip install -r requirements.txt

2️⃣ Set Environment Variables
 - NCBI_EMAIL=your_email@example.com
 - NCBI_API_KEY=your_ncbi_api_key
 - GROQ_API_KEY=your_groq_api_key

3️⃣ Run the App
 - streamlit run app.py

