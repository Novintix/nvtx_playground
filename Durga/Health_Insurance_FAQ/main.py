import os
from dotenv import load_dotenv
from vectorstore import create_vectorstore
from agent_graph import build_graph

# Load environment variables from .env file
load_dotenv()

# Verify GROQ_API_KEY is loaded
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")
print(f"✓ GROQ_API_KEY loaded (length: {len(api_key)})")

print("Creating vectorstore...")
vectorstore = create_vectorstore()
print("✓ Vectorstore created")

print("Building graph...")
graph = build_graph()
print("✓ Graph built")

questions = [
    "What is health insurance?",
    "Is cataract surgery covered?",
    "Can I claim insurance for knee surgery in the first year?"
]

for q in questions:
    result = graph.invoke({
        "question": q,
        "vectorstore": vectorstore
    })

    print("\nQuestion:", q)
    print("Used RAG:", "YES" if result.get("need_retrieval", "").strip().upper() == "YES" else "NO")
    print("Answer:", (result.get("answer") or "").strip())
