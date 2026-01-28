# multihop_graph.py
from langgraph.graph import StateGraph, END

from embed_store import PubMedEmbeddingStore
from reranker import rerank
from rag_generator import MedicalRAGGenerator


# --------------------------------------------------
# Graph State Definition
# --------------------------------------------------
class GraphState(dict):
    """
    Required keys (always present):
    - original_query : str
    - query          : str
    - hop            : int
    - retrieved_papers : list
    - distances        : list
    - final_papers     : list
    - answer           : str
    """
    pass


# --------------------------------------------------
# Node 1: Retrieval
# --------------------------------------------------
def retrieve_node(state: GraphState) -> GraphState:
    store = PubMedEmbeddingStore()

    query = state.get("query")
    if not isinstance(query, str) or not query.strip():
        query = state.get("original_query")

    papers, distances = store.search(query, top_k=5)

    state["retrieved_papers"] = papers
    state["distances"] = distances
    return state


# --------------------------------------------------
# Node 2: Re-ranking
# --------------------------------------------------
def rerank_node(state: GraphState) -> GraphState:
    reranked = rerank(
        state.get("retrieved_papers", []),
        state.get("distances", [])
    )

    state["final_papers"] = reranked
    return state


# --------------------------------------------------
# Node 3: Hop Expansion (SAFE)
# --------------------------------------------------
def hop_expansion_node(state: GraphState) -> GraphState:
    hop = state.get("hop", 1)

    # 🔒 Hard stop at max hops
    if hop >= 2:
        return state

    papers = state.get("final_papers", [])
    if not papers:
        return state

    base_query = state.get("original_query")

    # 🔒 Never expand from mutated queries
    if not isinstance(base_query, str) or not base_query.strip():
        return state

    top_titles = [p["title"] for p in papers[:2]]

    expanded_query = (
        base_query +
        " mechanisms " +
        " ".join(top_titles)
    )

    state["query"] = expanded_query
    state["hop"] = hop + 1
    return state


# --------------------------------------------------
# Node 4: Answer Generation
# --------------------------------------------------
def answer_node(state: GraphState) -> GraphState:
    rag = MedicalRAGGenerator()

    answer = rag.generate_answer(
        state.get("original_query"),
        state.get("final_papers", [])
    )

    state["answer"] = answer
    return state


# --------------------------------------------------
# Build LangGraph
# --------------------------------------------------
def build_multihop_graph():
    graph = StateGraph(GraphState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("expand", hop_expansion_node)
    graph.add_node("answer", answer_node)

    graph.set_entry_point("retrieve")

    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "expand")

    graph.add_conditional_edges(
        "expand",
        lambda s: "retrieve" if s.get("hop", 1) < 2 else "answer",
        {
            "retrieve": "retrieve",
            "answer": "answer"
        }
    )

    graph.add_edge("answer", END)

    return graph.compile()
