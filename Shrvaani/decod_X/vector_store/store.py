from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def create_vector_store(documents):
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        persist_directory="./vector_store/chroma"
    )

    vectordb.persist()
    return vectordb
