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

retriever = db.as_retriever(search_type="similarity", search_kwargs={"k":5,"score_threshold":0.3})

relevant_docs = retriever.invoke(query)

print(f"Users Query: {query}\n")
print("---Context---")
for i,doc in enumerate(relevant_docs,1):
    print(f"\nDocument {i}:")
    print(doc.page_content)
    print("Metadata:", doc.metadata)