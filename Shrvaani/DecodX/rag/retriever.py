def retrieve_context(vectordb, query: str, k: int = 4):
    results = vectordb.similarity_search(query, k=k)

    return {
        "financial_context": [
            r.page_content for r in results if r.metadata["source"] == "finance"
        ],
        "policy_context": [
            r.page_content for r in results if r.metadata["source"] == "policy"
        ]
    }
