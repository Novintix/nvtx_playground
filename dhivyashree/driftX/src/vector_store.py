from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def create_vector_store(text: str):
    """
    Creates a local FAISS vector store using local HuggingFace embeddings.
    No API key required for this step.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    
    # Use a small, fast local model (cpu-friendly)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    return vector_store

def retrieve_context(vector_store, query: str, k: int = 4) -> str:
    """
    Retrieves relevant text chunks for a given query.
    """
    docs = vector_store.similarity_search(query, k=k)
    return "\n\n".join([d.page_content for d in docs])
