21.01.2026
feedback on the RAG
1. Good job with the defensive checks 
if not os.path.exists(docs_path):
    raise FileNotFoundError(...)

always try to handle as much as errors as possible. 

2. Very small mistake "def load_documnets" but someone else assigned to this may mess up so always take care of spelling and variable name.

3. embedding_model = SentenceTransformer(model_name="all-MiniLM-L6-v2")
This and the below code may debate with each other

Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
)

because LangChain expects an embeddings interface, not a raw SentenceTransformer

Overall - okaish : 3.5/5 

