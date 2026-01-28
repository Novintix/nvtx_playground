from fastapi import FastAPI
from pydantic import BaseModel

from src.document_loader import load_and_chunk_pdf
from src.vector_store import create_vector_store
from src.llm import get_llm
from src.rag_chain import create_rag_chain


app = FastAPI(title="PDF RAG System")

# Startup initialization
chunks = load_and_chunk_pdf("data/Example.pdf")
vector_db = create_vector_store(chunks)
llm = get_llm()
rag_chain = create_rag_chain(llm, vector_db)


class QueryRequest(BaseModel):
    question: str


@app.post("/ask")
def ask_question(request: QueryRequest):
    response = rag_chain({"query": request.question})

    return {
        "answer": response["result"],
        "sources": [
            doc.metadata for doc in response["source_documents"]
        ]
    }
