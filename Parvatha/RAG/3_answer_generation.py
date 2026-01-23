import os
from langchain_chroma import Chroma
from langchain_mistralai import MistralAIEmbeddings, ChatMistralAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Optional
import sys

def load_vector_store(persistent_directory: str, api_key: str):
    """Load the vector store with embeddings."""
    try:
        print("📦 Loading Mistral embedding model...")
        embedding_model = MistralAIEmbeddings(
            model="mistral-embed",
            mistral_api_key=api_key
        )

        print(f"📚 Loading vector store from {persistent_directory}...")
        
        if not os.path.exists(persistent_directory):
            raise FileNotFoundError(f"Vector store directory not found: {persistent_directory}")
        
        db = Chroma(
            persist_directory=persistent_directory,
            embedding_function=embedding_model,
            collection_metadata={"hnsw:space": "cosine"}  
        )
        
        print("✅ Vector store loaded successfully!\n")
        return db
    
    except Exception as e:
        print(f"❌ Error loading vector store: {e}")
        sys.exit(1)

def search_documents(db, query: str, k: int = 5, use_threshold: bool = False, threshold: float = 0.3):
    """Search for relevant documents in the vector store."""
    try:
        if use_threshold:
            retriever = db.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": k,
                    "score_threshold": threshold
                }
            )
            print(f"🔍 Searching with similarity threshold ≥ {threshold}...")
        else:
            retriever = db.as_retriever(search_kwargs={"k": k})
        
        print(f"🔍 Searching for: '{query}'\n")
        relevant_docs = retriever.invoke(query)
        
        if not relevant_docs:
            print("⚠️  No relevant documents found.\n")
        else:
            print(f"✅ Found {len(relevant_docs)} relevant document(s)\n")
        
        return relevant_docs
    
    except Exception as e:
        print(f"❌ Error searching documents: {e}")
        return []

def display_documents(query: str, documents):
    """Display retrieved documents."""
    print(f"📄 User Query: {query}")
    print("=" * 80)
    print("--- Retrieved Context ---")
    print("=" * 80)
    
    if not documents:
        print("No documents to display.\n")
        return
    
    for i, doc in enumerate(documents, 1):
        print(f"\n📃 Document {i}:")
        print("-" * 80)
        print(f"{doc.page_content}")
        print("-" * 80)
        
        # Display metadata if available
        if hasattr(doc, 'metadata') and doc.metadata:
            print(f"📌 Metadata: {doc.metadata}")

def create_combined_input(query: str, documents):
    """Create a combined input prompt from query and documents."""
    if not documents:
        return f"""Question: {query}

No relevant documents were found to answer this question. Please respond with:
"I don't have any relevant documents to answer that question. Please try rephrasing your query or check if the vector store contains the necessary information."
"""
    
    combined_input = f"""Based on the following documents, please answer this question: {query}

Documents:
{chr(10).join([f"- {doc.page_content}" for doc in documents])}

Please provide a clear, helpful answer using only the information from these documents. If you can't find the answer in the documents, say "I don't have enough information to answer that question based on the provided documents."
"""
    return combined_input

def generate_answer(combined_input: str, api_key: str, model_name: str = "mistral-large-latest"):
    """Generate an answer using the Mistral LLM."""
    try:
        print("🤖 Generating answer with Mistral...\n")
        
        model = ChatMistralAI(
            model=model_name,
            mistral_api_key=api_key,
            temperature=0.7  # Adjust for creativity vs consistency
        )

        messages = [
            SystemMessage(content="You are a helpful assistant that answers questions based on provided documents. Be concise and accurate."),
            HumanMessage(content=combined_input),
        ]

        result = model.invoke(messages)
        
        return result
    
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        sys.exit(1)

def main(query: Optional[str] = None, 
         persistent_directory: str = "db/chroma_db", 
         k: int = 5, 
         use_threshold: bool = False, 
         threshold: float = 0.3,
         model_name: str = "mistral-large-latest"):
    """Main function to run the RAG pipeline."""
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        raise ValueError("❌ MISTRAL_API_KEY not found in environment variables. Please set it in your .env file.")
    
    # Handle missing query
# Get query from user if not provided
    if not query:
        query = input("🧠 Enter your question: ").strip()
    
    if not query:
        print("❌ Query cannot be empty.")
        sys.exit(1)

    
    print("\n" + "=" * 80)
    print("🚀 RAG PIPELINE STARTING")
    print("=" * 80 + "\n")

    # Load vector store
    db = load_vector_store(persistent_directory, api_key)
    
    # Search for relevant documents
    relevant_docs = search_documents(db, query, k, use_threshold, threshold)
    
    # Display retrieved documents
    display_documents(query, relevant_docs)
    
    # Create combined input
    combined_input = create_combined_input(query, relevant_docs)
    
    # Generate answer
    result = generate_answer(combined_input, api_key, model_name)
    
    # Display result
    print("\n" + "=" * 80)
    print("--- Generated Response ---")
    print("=" * 80)
    print(result.content)
    print("=" * 80 + "\n")
    
    return result

if __name__ == "__main__":
    main()
    
 