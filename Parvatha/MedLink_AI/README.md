🧬 MedLink AI – Medical Research Literature Navigator

MedLink AI is an agentic, multi-hop Retrieval-Augmented Generation (RAG) system designed to help medical researchers efficiently explore, connect, and synthesize biomedical literature from PubMed using real research papers.

🚀 What It Does

Fetches real biomedical research papers from PubMed (NCBI)

Performs semantic + keyword-based retrieval

Uses multi-hop reasoning to discover hidden connections across papers

Re-ranks evidence using scientific relevance, recency, and journal quality

Generates evidence-grounded, mechanistic answers using LLMs

Displays answers with supporting research papers and justification

🧠 Core Features

Hybrid RAG: FAISS-based semantic search + exact keyword retrieval

Multi-Hop Reasoning: Iterative query expansion across evidence

Evidence-Based Answers: No hallucinations, grounded in abstracts

Justification Scoring: Confidence score backed by research papers

Caching & Memory: SQLite-backed query and paper caching

Professional UI: Streamlit interface for researchers

🛠️ Tech Stack

Backend / AI

Python 3.12

LangChain

LangGraph (agent orchestration)

Retrieval-Augmented Generation (RAG)

FAISS (vector search)

PubMedBERT (biomedical embeddings)

Groq API (LLaMA 3.1 models for reasoning)

Data Sources

PubMed / NCBI (Biopython Entrez API)

Storage

SQLite (query cache, paper metadata, scores, history)

Frontend

Streamlit (custom medical-themed UI)