import os
from langchain_chroma import Chroma
from langchain_mistralai import MistralAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

persistent_directory = "db/chroma_db"

# Load embeddings  model
print("📦 Loading Mistral embedding model...")
embedding_model = MistralAIEmbeddings(
    model="mistral-embed",
    mistral_api_key=os.getenv("MISTRAL_API_KEY")
)

# Load vector store
print(f"📚 Loading vector store from {persistent_directory}...")
db = Chroma(
    persist_directory=persistent_directory,
    embedding_function=embedding_model,
    collection_metadata={"hnsw:space": "cosine"}  
)

print(f"✅ Vector store loaded successfully!\n")

# Create retriever
retriever = db.as_retriever(search_kwargs={"k": 3})

# Alternative: With similarity score threshold
# retriever = db.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={
#         "k": 5,
#         "score_threshold": 0.3
#     }
# )

# ============================================================================
# Dynamic Query Loop
# ============================================================================
print("-" * 80)
print("🤖 RAG Retrieval System - Ask me anything!")
print("-" * 80)
print("Type 'exit' or 'quit' to stop\n")

while True:
    # Get user input
    query = input("💬 Your Question: ").strip()
    
    # Exit condition
    if query.lower() in ['exit', 'quit', 'q']:
        print("\n👋 Goodbye!")
        break
    
    # Skip empty queries
    if not query:
        print("⚠️ Please enter a question.\n")
        continue
    
    print("\n🔍 Searching for relevant documents...\n")
    
    try:
        # Retrieve relevant documents
        relevant_docs = retriever.invoke(query)
        
        # Display results
        print(f"📚 Found {len(relevant_docs)} relevant document(s):\n")
        print("--- Context ---\n")
        
        for i, doc in enumerate(relevant_docs, 1):
            print(f"Document {i}:")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"Content:\n{doc.page_content}\n")
            print("-" * 80)
        
        print("\n")
    
    except Exception as e:
        print(f"❌ Error: {e}\n")

# ============================================================================
# Example Questions for testing:
# ============================================================================
# 1. "What was NVIDIA's first graphics accelerator called?"
# 2. "Which company did NVIDIA acquire to enter the mobile processor market?"
# 3. "What was Microsoft's first hardware product release?"
# 4. "How much did Microsoft pay to acquire GitHub?"
# 5. "In what year did Tesla begin production of the Roadster?"
# 6. "Who succeeded Ze'ev Drori as CEO in October 2008?"
# 7. "What was the name of the autonomous spaceport drone ship that achieved the first successful sea landing?"
# 8. "What was the original name of Microsoft before it became Microsoft?"