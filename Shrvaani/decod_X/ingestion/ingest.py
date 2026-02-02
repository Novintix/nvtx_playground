import pandas as pd
from langchain_core.documents import Document

def load_financial_data(path: str):
    df = pd.read_csv(path)
    docs = []

    for _, row in df.iterrows():
        content = (
            f"Year: {row['year']}, Region: {row['region']}, "
            f"Product: {row['product']}, Revenue: {row['revenue']}, "
            f"Cost: {row['cost']}, Discount: {row['discount_applied']}%"
        )

        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source": "finance",
                    "year": row["year"],
                    "region": row["region"],
                    "product": row["product"]
                }
            )
        )
    return docs


from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_policy_data(path: str):
    with open(path, "r") as f:
        text = f.read()

    # Enterprise-grade Chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # ~100-150 words per chunk
        chunk_overlap=50,    # Context continuity
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[{"source": "policy"}]
    )
    
    return chunks
