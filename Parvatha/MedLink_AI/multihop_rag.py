# multihop_rag.py
from typing import List, Dict, Tuple, TypedDict
from langgraph.graph import StateGraph, END

from ncbi_fetcher import NCBIFetcher
from embed_store import PubMedEmbeddingStore
from reranker import rerank
from rag_generator import MedicalRAGGenerator
from error_handler import log_info, log_warning, handle_error
from config import MAX_HOPS, TOP_K_PER_HOP


# ==================================================
# State Definition for LangGraph
# ==================================================
class RAGState(TypedDict):
    query: str
    original_query: str
    hop: int
    papers: List[Dict]
    distances: List[float]
    ranked_papers: List[Dict]
    final_answer: str
    error: str


# ==================================================
# Global Singletons (Load Once)
# ==================================================
_fetcher = None
_store = None
_generator = None


def get_fetcher() -> NCBIFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = NCBIFetcher()
    return _fetcher


def get_store() -> PubMedEmbeddingStore:
    global _store
    if _store is None:
        _store = PubMedEmbeddingStore()
    return _store


def get_generator() -> MedicalRAGGenerator:
    global _generator
    if _generator is None:
        _generator = MedicalRAGGenerator()
    return _generator


# ==================================================
# Node 1: Fetch Papers from NCBI
# ==================================================
def fetch_papers_node(state: RAGState) -> RAGState:
    try:
        query = state["query"]
        log_info(f"📥 Node 1: Fetching papers for '{query[:50]}...'")

        fetcher = get_fetcher()
        generator = get_generator()

        # ✅ LLM-based PubMed query normalization
        pubmed_query = generator.normalize_pubmed_query(query)
        log_info(f"🔎 PubMed query (LLM): '{pubmed_query}'")

        papers = fetcher.fetch_papers(pubmed_query, max_results=10)

        if not papers:
            log_warning("⚠️ No papers fetched from NCBI")
            state["papers"] = []
            state["error"] = "No papers fetched from NCBI."
            return state

        # Add papers to vector store
        store = get_store()
        for paper in papers:
            if not store.has_paper(paper["pmid"]):
                store.add_paper(paper)

        log_info(f"✅ Fetched and indexed {len(papers)} papers")
        state["papers"] = papers

    except Exception as e:
        error_msg = handle_error(e, "fetch_papers_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["papers"] = []

    return state


# ==================================================
# Node 2: Retrieve Similar Papers
# ==================================================
def retrieve_papers_node(state: RAGState) -> RAGState:
    try:
        if state.get("error"):
            return state

        query = state["query"]
        log_info(f"🔍 Node 2: Searching vector store for '{query[:50]}...'")

        store = get_store()
        papers, distances = store.search(query, top_k=TOP_K_PER_HOP)

        if not papers:
            log_warning("⚠️ No papers retrieved from vector store")
            state["papers"] = []
            state["distances"] = []
            return state

        log_info(f"✅ Retrieved {len(papers)} papers")
        state["papers"] = papers
        state["distances"] = distances

    except Exception as e:
        error_msg = handle_error(e, "retrieve_papers_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["papers"] = []
        state["distances"] = []

    return state


# ==================================================
# Node 3: Re-rank Papers
# ==================================================
def rerank_papers_node(state: RAGState) -> RAGState:
    try:
        if state.get("error"):
            return state

        papers = state.get("papers", [])
        distances = state.get("distances", [])

        if not papers:
            log_warning("⚠️ No papers to re-rank")
            state["ranked_papers"] = []
            return state

        log_info(f"⚖️ Node 3: Re-ranking {len(papers)} papers...")
        ranked = rerank(papers, distances)

        log_info(f"✅ Re-ranked papers (top score: {ranked[0].get('final_score', 0):.3f})")
        state["ranked_papers"] = ranked

    except Exception as e:
        error_msg = handle_error(e, "rerank_papers_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["ranked_papers"] = state.get("papers", [])

    return state


# ==================================================
# Node 4: Query Expansion (Multi-hop)
# ==================================================
def expand_query_node(state: RAGState) -> RAGState:
    try:
        if state.get("error"):
            return state

        hop = state.get("hop", 1)
        ranked_papers = state.get("ranked_papers", [])
        original_query = state["original_query"]

        log_info(f"🔄 Node 4: Query expansion (hop {hop})")

        # Increment hop
        state["hop"] = hop + 1

        # Natural expansion (LLM will normalize in next fetch)
        if ranked_papers and hop < MAX_HOPS:
            top_titles = [p["title"] for p in ranked_papers[:2]]
            expanded = original_query + " mechanisms " + " ".join(top_titles)
            state["query"] = expanded
            log_info(f"   Expanded query: '{expanded[:60]}...'")

    except Exception as e:
        error_msg = handle_error(e, "expand_query_node")
        log_warning(error_msg)
        state["error"] = error_msg

    return state


# ==================================================
# Node 5: Generate Answer
# ==================================================
def generate_answer_node(state: RAGState) -> RAGState:
    try:
        query = state["original_query"]
        papers = state.get("ranked_papers", [])

        log_info("🧠 Node 5: Generating answer...")

        if not papers:
            state["final_answer"] = "No relevant papers found to answer this query."
            return state

        generator = get_generator()
        answer = generator.generate_answer(query, papers)

        log_info(f"✅ Answer generated ({len(answer)} chars)")
        state["final_answer"] = answer

    except Exception as e:
        error_msg = handle_error(e, "generate_answer_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["final_answer"] = f"Error generating answer: {error_msg}"

    return state


# ==================================================
# Routing Logic
# ==================================================
def should_continue(state: RAGState) -> str:
    if state.get("error"):
        return "generate"

    hop = state.get("hop", 1)

    if hop >= MAX_HOPS:
        log_info(f"🛑 Max hops ({MAX_HOPS}) reached, generating answer")
        return "generate"

    log_info(f"➡️ Continue to hop {hop + 1}")
    return "continue"


# ==================================================
# Build LangGraph
# ==================================================
def build_multihop_graph() -> StateGraph:
    workflow = StateGraph(RAGState)

    workflow.add_node("fetch", fetch_papers_node)
    workflow.add_node("retrieve", retrieve_papers_node)
    workflow.add_node("rerank", rerank_papers_node)
    workflow.add_node("expand", expand_query_node)
    workflow.add_node("generate", generate_answer_node)

    workflow.set_entry_point("fetch")
    workflow.add_edge("fetch", "retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "expand")

    workflow.add_conditional_edges(
        "expand",
        should_continue,
        {
            "continue": "retrieve",
            "generate": "generate"
        }
    )

    workflow.add_edge("generate", END)

    return workflow.compile()


# ==================================================
# Main MultiHopRAG Class
# ==================================================
class MultiHopRAG:
    def __init__(self):
        log_info("🚀 Initializing Multi-Hop RAG with LangGraph...")
        self.graph = build_multihop_graph()
        log_info("✅ LangGraph compiled successfully")

    def run(self, query: str) -> Tuple[str, List[Dict]]:
        try:
            if not query or not isinstance(query, str):
                return "Invalid query provided.", []

            query = query.strip()
            log_info(f"🔬 Starting multi-hop RAG for: '{query[:60]}...'")

            initial_state = RAGState(
                query=query,
                original_query=query,
                hop=1,
                papers=[],
                distances=[],
                ranked_papers=[],
                final_answer="",
                error=""
            )

            # ✅ LangGraph-safe invocation
            final_state = self.graph.invoke(
                initial_state,
                {"output_keys": ["final_answer", "ranked_papers", "error"]}
            )

            answer = final_state.get("final_answer", "No answer generated.")
            papers = final_state.get("ranked_papers", [])

            if final_state.get("error"):
                log_warning(f"⚠️ Pipeline completed with errors: {final_state['error']}")
            else:
                log_info("✅ Pipeline completed successfully")

            return answer, papers

        except Exception as e:
            error_msg = handle_error(e, "MultiHopRAG.run")
            log_warning(error_msg)
            return f"Error in multi-hop RAG: {error_msg}", []
