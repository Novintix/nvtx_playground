import os
import torch
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_mistralai import MistralAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
  
load_dotenv()

def load_documents(docs_path="docs"):
    """Load all text files from the docs directory"""
    print(f"Loading documents from {docs_path}...")
    
    # Check if docs directory exists
    if not os.path.exists(docs_path):
        raise FileNotFoundError(
            f"The directory {docs_path} does not exist. "
            f"Please create it and add your company files."
        )
    
    # Load all .txt files from the docs directory
    loader = DirectoryLoader(
        path=docs_path,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    
    documents = loader.load()
    
    if len(documents) == 0:
        raise FileNotFoundError(
            f"No .txt files found in {docs_path}. "
            f"Please add your company documents."
        )
    
    print(f"✅ Loaded {len(documents)} document(s)")
    
    # Show first 2 documents
    for i, doc in enumerate(documents[:2]):
        print(f"\nDocument {i+1}:")
        print(f"  Source: {doc.metadata['source']}")
        print(f"  Content length: {len(doc.page_content)} characters")
        print(f"  Content preview: {doc.page_content[:100]}...")

    return documents


def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """Split documents into smaller chunks with overlap"""
    print("\nSplitting documents into chunks...")
    
    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        separator="\n"
    )
    
    chunks = text_splitter.split_documents(documents)
    
    print(f"✅ Created {len(chunks)} chunk(s)")
    
    if chunks:
        # Show first 3 chunks
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Source: {chunk.metadata['source']}")
            print(f"Length: {len(chunk.page_content)} characters")
            print(f"Content preview:")
            print(chunk.page_content[:200] + "...")
            print("-" * 50)
        
        if len(chunks) > 3:
            print(f"\n... and {len(chunks) - 3} more chunks")
    
    return chunks


def create_vector_store(chunks, persist_directory="db/chroma_db"):
    """Create and persist ChromaDB vector store with Mistral embeddings"""
    print("\nCreating embeddings and storing in ChromaDB...")
    
    embedding_model = MistralAIEmbeddings(
        model="mistral-embed",
        mistral_api_key=os.getenv("MISTRAL_API_KEY")
    )
    
    print("--- Creating vector store ---")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_directory, 
        collection_metadata={"hnsw:space": "cosine"}
    )
    print("--- Finished creating vector store ---")
    
    print(f"✅ Vector store created and saved to {persist_directory}")
    return vectorstore


def load_existing_vectorstore(persist_directory="db/chroma_db"):
    """Load an existing vector store"""
    print("Loading existing vector store...")
    
    embedding_model = MistralAIEmbeddings(
        model="mistral-embed",
        mistral_api_key=os.getenv("MISTRAL_API_KEY")
    )
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model, 
        collection_metadata={"hnsw:space": "cosine"}
    )
    
    try:
        count = vectorstore._collection.count()
        print(f"✅ Loaded existing vector store with {count} chunks")
    except Exception as e:
        print(f"⚠️ Could not get collection count: {e}")
    
    return vectorstore


def main():
    """Main ingestion pipeline"""
    print("RAG Document Ingestion Pipeline (Mistral Embeddings)")
    
    # Define paths
    docs_path = "docs"
    persist_directory = "db/chroma_db"
    
    # Check if vector store already exists
    if os.path.exists(persist_directory) and os.listdir(persist_directory):
        print("\n✅ Vector store already exists. No need to re-process documents.")
        vectorstore = load_existing_vectorstore(persist_directory)
        return vectorstore
    
    print("\n📁 Persistent directory does not exist. Initializing vector store...\n")
    
    try:
        # Step 1: Load documents
        documents = load_documents(docs_path)
        
        # Step 2: Split into chunks
        chunks = split_documents(documents, chunk_size=1000, chunk_overlap=200)
        
        # Step 3: Create vector store
        vectorstore = create_vector_store(chunks, persist_directory)
        
        print("\n" + "-" * 60)
        print("✅ Ingestion complete! Your documents are ready for RAG queries.")
        print("-" * 60)
        
        return vectorstore
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return None
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()