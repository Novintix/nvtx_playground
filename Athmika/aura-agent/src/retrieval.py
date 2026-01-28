import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

DATA_FOLDER = "data"
DB_INDEX_PATH = "faiss_index"

def ingest_resume(file_path: str):
    if not os.path.exists(file_path):
        return "No resume found.", None

    # 1. Load PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    full_text = "\n".join([d.page_content for d in docs])

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # 3. Create Embeddings (Using the FIXED model name)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # 4. Save Vector Store
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
    vectorstore.save_local(DB_INDEX_PATH)

    print("✅ Resume Ingested with Groq Embeddings (all-MiniLM-L6-v2)!")
    return full_text, vectorstore

def get_retriever():
    # Must use the SAME model name for retrieval
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if os.path.exists(DB_INDEX_PATH):
        vectorstore = FAISS.load_local(
            DB_INDEX_PATH, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    else:
        return None