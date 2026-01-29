from dotenv import load_dotenv
from ingestion.ingest import load_financial_data, load_policy_data
from vector_store.store import create_vector_store
from rag.retriever import retrieve_context

load_dotenv()

if __name__ == "__main__":
    finance_docs = load_financial_data("data/sample_finance.csv")
    policy_docs = load_policy_data("data/sales_policy.txt")

    all_docs = finance_docs + policy_docs
    vectordb = create_vector_store(all_docs)

    query = "Why are sales down this year?"
    context = retrieve_context(vectordb, query)

    print("\n--- Financial Context ---")
    for c in context["financial_context"]:
        print(c)

    print("\n--- Policy Context ---")
    for c in context["policy_context"]:
        print(c)
