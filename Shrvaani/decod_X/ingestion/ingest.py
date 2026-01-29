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
                    "year": row["year"],
                    "region": row["region"],
                    "product": row["product"],
                    "source": "finance"
                }
            )
        )

    return docs


def load_policy_data(path: str):
    with open(path, "r") as f:
        text = f.read()

    return [
        Document(
            page_content=text,
            metadata={"source": "policy"}
        )
    ]
