from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from pinecone import Pinecone, ServerlessSpec
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

def create_vector_store(documents):
    """
    Creates a vector store using either Pinecone (production) or Chroma (local dev).
    Automatically selects based on PINECONE_API_KEY environment variable.
    """
    embedding = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    
    # For now, always use Chroma for local development
    # Pinecone support can be enabled by uncommenting the code and installing dependencies
    print("💻 Using Chroma (Local Dev Mode)")
    
    db_path = "./vector_store/chroma"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        persist_directory=db_path
    )
    
    return vectordb


def retrieve_context(vectordb, query, k=5):
    results = vectordb.similarity_search(query, k=k)

    policy_context = []
    financial_context = []
    seen_content = set()

    for doc in results:
        # Deduplication Check
        if doc.page_content in seen_content:
            continue
        seen_content.add(doc.page_content)

        if doc.metadata.get("source") == "policy":
            policy_context.append(doc.page_content)
        elif doc.metadata.get("source") == "finance":
            financial_context.append(doc.page_content)

    return {
        "policy_context": policy_context,
        "financial_context": financial_context
    }
