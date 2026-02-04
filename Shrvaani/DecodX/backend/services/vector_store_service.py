import os
import shutil
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from backend.config.settings import ROOT_DIR

# Creates or updates the Chroma vector store with given documents.
def create_vector_store(documents):
    """Creates or updates the Chroma vector store."""
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db_path = str(ROOT_DIR / "vector_store" / "chroma")
    
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        persist_directory=db_path
    )
    return vectordb

# Returns a LangChain retriever for the existing vector database.
def get_retriever():
    """Returns a retriever for the existing vector store."""
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db_path = str(ROOT_DIR / "vector_store" / "chroma")
    
    if not os.path.exists(db_path):
        return None
        
    vectordb = Chroma(persist_directory=db_path, embedding_function=embedding)
    return vectordb.as_retriever(search_kwargs={"k": 3})
