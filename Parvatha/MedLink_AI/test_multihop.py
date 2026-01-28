# test_multihop.py
from multihop_graph import build_multihop_graph

query = "What are the mechanisms linking insulin resistance and lifestyle factors?"

graph = build_multihop_graph()

initial_state = {
    "query": query,
    "original_query": query,
    "hop": 1,
    "retrieved_papers": [],
    "distances": [],
    "final_papers": [],
    "answer": ""
}

final_state = graph.invoke(initial_state)

print("\n🧠 MULTI-HOP ANSWER:\n")
print(final_state["answer"])
