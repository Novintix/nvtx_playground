from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

persist_directory = "db/chroma_db"

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding_model,
    collection_metadata={"hnsw:space":"cosine"}
)

query = "Which island does SpaceX lease for its launches in the Pacific?"

retriever = db.as_retriever(search_type="mmr", search_kwargs={"k":5, "fetch_k":10, "lambda_mult":0.5})

relevant_docs = retriever.invoke(query)
seen_sources = set()
unique_docs = []

for doc in relevant_docs:
    source = doc.metadata.get("source")
    if source not in seen_sources:
        unique_docs.append(doc)
        seen_sources.add(source)

print(f"Users Query: {query}\n")
print("---Context---")
for i,doc in enumerate(unique_docs,1):
    print(f"\nDocument {i}:")
    print(doc.page_content)
    print("Metadata:", doc.metadata)