import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()


def load_documnets(docs_path):
    """Load all text files from the docs directory"""
    print(f"Loading documents from: {docs_path}...")
    
    if not os.path.exists(docs_path):
        raise FileNotFoundError(f"The specified path {docs_path} does not exist. Please provide a valid path to your company documents.")
    
    loader = DirectoryLoader(
        path=docs_path, 
        glob="**/*.txt", 
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    
    documents = loader.load()

    if len(documents) == 0:
        raise FileNotFoundError(f"No .txt files found in {docs_path}. Please add your company documents.")
    
    for i, doc in enumerate(documents):
        print(f"\nDocuments {i+1}:")
        print(f"  Source: {doc.metadata['source']}")
        print(f"  Content length: {len(doc.page_content)} characters")  
        print(f"  Content preview: {doc.page_content[:100]}...")
        print(f"  metadata: {doc.metadata}")
    
    return documents

def split_documents(documents, chunk_size=1000, chunk_overlap=0):
    """Split documents into smaller chunks"""
    print("Splitting documents into chunks...")
    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separator="\n"
    )
    
    chunks = text_splitter.split_documents(documents)
    
    if chunks:
        for i, chunk in enumerate(chunks[:5]):
            print(f"\nChunk {i+1}:")
            print(f"  Source: {chunk.metadata['source']}")
            print(f"  Content length: {len(chunk.page_content)} characters")  
            print(f"  Content preview:")
            print(chunk.page_content)
            print("-"*50)
        
        if len(chunks)>5:
            print(f"\n.. and {len(chunks)-5} more chunks")

    return chunks

def create_vector_store(chunks, persist_directory="db/chroma_db"):
    """Create and persists ChromaDB vectore store"""
    print("Creating embeddings and storing in ChromaDB")
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("--- Creating vector store ---")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_metadata = {"hnsw:space":"cosine"}
    )
    print("--- Finished creating vector store ---")
    print(f"Vector store created and persisted at: {persist_directory}")
    
    return vector_store    



def main():
    print("Main function")
    documents = load_documnets(docs_path="docs")
    chunks = split_documents(documents)
    vector_store = create_vector_store(chunks)


if __name__ == "__main__":
    main()