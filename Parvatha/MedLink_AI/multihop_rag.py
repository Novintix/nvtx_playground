#multihop_rag.py
"""
Enhanced Multi-Hop RAG with Domain Validation and Uncertainty Quantification
LangGraph-based agent workflow for MedGuard Evidence
"""

from typing import List, Dict, Tuple, TypedDict, Optional
from langgraph.graph import StateGraph, END

from ncbi_fetcher import NCBIFetcher
from embed_store import PubMedEmbeddingStore
from reranker import EvidenceReranker
from rag_generator import MedicalRAGGenerator, GeneratedAnswer
from query_validator import QueryValidator, ValidationResult, ValidationStatus
from error_handler import log_info, log_warning, handle_error
from config import MAX_HOPS, TOP_K_PER_HOP, MIN_DOMAIN_RELEVANCE, MIN_ANSWER_CONFIDENCE


# ==================================================
# Enhanced State Definition
# ==================================================
class RAGState(TypedDict):
    # Input
    query: str
    original_query: str
    
    # Validation
    validation_result: Optional[ValidationResult]
    is_validated: bool
    
    # Multi-hop tracking
    hop: int
    
    # Evidence collection
    papers: List[Dict]
    similarities: List[float]
    uncertainties: List[float]
    
    # Re-ranking
    ranked_papers: List[Dict]
    retrieval_confidence: float
    contradictions: List[Dict]
    
    # Generation
    generated_answer: Optional[GeneratedAnswer]
    final_answer: str
    should_answer: bool
    
    # Error handling
    error: str
    rejection_reason: str


# ==================================================
# Global Singletons
# ==================================================
_components = {}


def get_component(name: str):
    """Lazy loading of components"""
    if name not in _components:
        if name == "fetcher":
            _components[name] = NCBIFetcher()
        elif name == "store":
            _components[name] = PubMedEmbeddingStore()
        elif name == "reranker":
            _components[name] = EvidenceReranker()
        elif name == "generator":
            _components[name] = MedicalRAGGenerator()
        elif name == "validator":
            _components[name] = QueryValidator()
    return _components[name]


# ==================================================
# Node 0: Validate Query (NEW - Domain Guard)
# ==================================================
def validate_query_node(state: RAGState) -> RAGState:
    """Validate query before any retrieval - THE DOMAIN GUARD"""
    try:
        query = state["original_query"]
        log_info(f"🛡️  Validating query: '{query[:60]}...'")
        
        validator = get_component("validator")
        result = validator.validate(query)
        
        state["validation_result"] = result
        state["is_validated"] = True
        
        if not result.is_valid:
            log_warning(f"🚫 Query rejected: {result.status.value}")
            state["rejection_reason"] = result.rejection_reason
            state["final_answer"] = _format_rejection_response(result)
            state["should_answer"] = False
            state["error"] = f"VALIDATION_FAILED: {result.status.value}"
        else:
            log_info(f"✅ Query validated (relevance: {result.relevance_score:.2f})")
            state["rejection_reason"] = ""
            state["should_answer"] = True
            
    except Exception as e:
        error_msg = handle_error(e, "validate_query_node")
        log_warning(error_msg)
        state["error"] = error_msg
        # Fail open - allow query to proceed if validator breaks
        state["is_validated"] = True
        state["should_answer"] = True
    
    return state


def _format_rejection_response(result: ValidationResult) -> str:
    """Format rejection message for user"""
    response = f"""🚫 **Query Rejected - Outside Medical Domain**

**Reason:** {result.rejection_reason}

**Domain Relevance Score:** {result.relevance_score:.2f} (threshold: {MIN_DOMAIN_RELEVANCE})

**How to Fix:**
{result.suggestion}

---
**What this system does:**
MedGuard Evidence is a specialized biomedical research assistant that searches peer-reviewed literature (PubMed) to answer medical research questions. It requires queries focused on:
- Diseases and conditions
- Biological mechanisms
- Clinical research
- Drug effects and interactions
- Medical diagnostics and therapeutics

For general knowledge questions, please use ChatGPT, Perplexity, or other general-purpose AI assistants."""
    return response


# ==================================================
# Routing: Should we continue after validation?
# ==================================================
def route_after_validation(state: RAGState) -> str:
    """Route to retrieval if valid, else to end"""
    if state.get("error", "").startswith("VALIDATION_FAILED"):
        return "reject"
    return "retrieve"


# ==================================================
# Node 1: Fetch Papers (Enhanced with cache check)
# ==================================================
def fetch_papers_node(state: RAGState) -> RAGState:
    """Fetch papers from NCBI with intelligent caching"""
    try:
        if state.get("error"):
            return state
        
        query = state["query"]
        log_info(f"📥 Fetching papers for: '{query[:50]}...'")
        
        fetcher = get_component("fetcher")
        generator = get_component("generator")
        
        # LLM-based query normalization
        pubmed_query = generator.normalize_pubmed_query(query)
        log_info(f"🔎 Normalized query: '{pubmed_query}'")
        
        # Fetch papers
        papers = fetcher.fetch_papers(pubmed_query, max_results=15)
        
        if not papers:
            log_warning("⚠️ No papers fetched from NCBI")
            state["papers"] = []
            state["error"] = "NO_PAPERS: No relevant papers found in PubMed"
            return state
        
        # Add to vector store
        store = get_component("store")
        new_papers = [p for p in papers if not store.has_paper(p["pmid"])]
        if new_papers:
            log_info(f"📚 Adding {len(new_papers)} new papers to index")
            store.build_index(new_papers)
        
        log_info(f"✅ Fetched {len(papers)} papers")
        state["papers"] = papers
        
    except Exception as e:
        error_msg = handle_error(e, "fetch_papers_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["papers"] = []
    
    return state


# ==================================================
# Node 2: Retrieve from Vector Store
# ==================================================
def retrieve_papers_node(state: RAGState) -> RAGState:
    """Retrieve semantically similar papers"""
    try:
        if state.get("error"):
            return state
        
        query = state["query"]
        log_info(f"🔍 Retrieving papers for: '{query[:50]}...'")
        
        store = get_component("store")
        
        # Enhanced search returns uncertainties too
        papers, similarities, uncertainties = store.search(query, top_k=TOP_K_PER_HOP * 3)
        
        if not papers:
            log_warning("⚠️ No papers retrieved from vector store")
            state["papers"] = []
            state["similarities"] = []
            state["uncertainties"] = []
            return state
        
        log_info(f"✅ Retrieved {len(papers)} papers from index")
        state["papers"] = papers
        state["similarities"] = similarities
        state["uncertainties"] = uncertainties
        
    except Exception as e:
        error_msg = handle_error(e, "retrieve_papers_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["papers"] = []
        state["similarities"] = []
        state["uncertainties"] = []
    
    return state


# ==================================================
# Node 3: Re-rank and Validate Evidence
# ==================================================
def rerank_papers_node(state: RAGState) -> RAGState:
    """Re-rank papers and calculate confidence"""
    try:
        if state.get("error"):
            return state
        
        papers = state.get("papers", [])
        similarities = state.get("similarities", [])
        
        if not papers:
            state["ranked_papers"] = []
            state["retrieval_confidence"] = 0.0
            return state
        
        log_info(f"⚖️ Re-ranking {len(papers)} papers...")
        
        reranker = get_component("reranker")
        query = state["query"]
        
        # Multi-factor re-ranking
        ranked, confidence = reranker.rerank(query, papers, similarities)
        
        # Detect contradictions
        contradictions = reranker.detect_contradictions(ranked[:5])
        
        log_info(f"✅ Re-ranked (confidence: {confidence:.3f}, contradictions: {len(contradictions)})")
        
        state["ranked_papers"] = ranked
        state["retrieval_confidence"] = confidence
        state["contradictions"] = contradictions
        
        # Early exit if confidence too low
        if confidence < 0.3:
            log_warning(f"⚠️ Very low retrieval confidence: {confidence:.3f}")
            state["error"] = f"LOW_CONFIDENCE: Evidence quality too low ({confidence:.2f})"
        
    except Exception as e:
        error_msg = handle_error(e, "rerank_papers_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["ranked_papers"] = state.get("papers", [])
        state["retrieval_confidence"] = 0.5
    
    return state


# ==================================================
# Node 4: Multi-hop Expansion (Enhanced)
# ==================================================
def expand_query_node(state: RAGState) -> RAGState:
    """Expand query for multi-hop reasoning"""
    try:
        if state.get("error"):
            return state
        
        hop = state.get("hop", 1)
        ranked_papers = state.get("ranked_papers", [])
        original_query = state["original_query"]
        
        log_info(f"🔄 Query expansion (hop {hop}/{MAX_HOPS})")
        
        # Increment hop
        state["hop"] = hop + 1
        
        # Smart expansion: extract key concepts from top papers
        if ranked_papers and hop < MAX_HOPS:
            # Get MeSH terms or keywords from top papers
            expansion_terms = []
            
            # Use titles for expansion
            top_titles = [p["title"] for p in ranked_papers[:2]]
            for title in top_titles:
                # Extract key noun phrases (simplified)
                words = title.split()
                key_terms = [w for w in words if len(w) > 5 and w.isalpha()]
                expansion_terms.extend(key_terms[:3])
            
            # Deduplicate and limit
            expansion_terms = list(set(expansion_terms))[:5]
            
            if expansion_terms:
                expanded = f"{original_query} {' '.join(expansion_terms)}"
                state["query"] = expanded
                log_info(f"   Expanded with: {', '.join(expansion_terms)}")
        
    except Exception as e:
        error_msg = handle_error(e, "expand_query_node")
        log_warning(error_msg)
        # Non-critical error, continue
    
    return state


# ==================================================
# Routing: Continue or Generate?
# ==================================================
def should_continue(state: RAGState) -> str:
    """Decide whether to continue multi-hop or generate answer"""
    if state.get("error"):
        return "generate"
    
    hop = state.get("hop", 1)
    
    if hop >= MAX_HOPS:
        log_info(f"🛑 Max hops reached, generating answer")
        return "generate"
    
    # Check if we have good enough results to stop early
    if state.get("retrieval_confidence", 0) > 0.8 and state.get("hop", 1) > 1:
        log_info("✅ High confidence achieved, stopping early")
        return "generate"
    
    log_info(f"➡️ Continue to hop {hop + 1}")
    return "continue"


# ==================================================
# Node 5: Generate Answer (Enhanced with Uncertainty)
# ==================================================
def generate_answer_node(state: RAGState) -> RAGState:
    """Generate structured answer with confidence"""
    try:
        original_query = state["original_query"]
        papers = state.get("ranked_papers", [])
        confidence = state.get("retrieval_confidence", 0.5)
        contradictions = state.get("contradictions", [])
        
        log_info("🧠 Generating structured answer...")
        
        if not papers:
            state["final_answer"] = "No relevant papers found to answer this query."
            state["should_answer"] = False
            return state
        
        generator = get_component("generator")
        
        # Generate structured answer with uncertainty
        result = generator.generate_structured_answer(
            query=original_query,
            papers=papers,
            retrieval_confidence=confidence
        )
        
        state["generated_answer"] = result
        state["should_answer"] = result.should_answer
        
        # Format final answer
        if result.should_answer:
            state["final_answer"] = _format_success_answer(result, contradictions)
        else:
            state["final_answer"] = _format_low_confidence_answer(result)
        
        log_info(f"✅ Answer generated (confidence: {result.confidence_score:.3f}, grade: {result.evidence_grade.value})")
        
    except Exception as e:
        error_msg = handle_error(e, "generate_answer_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["final_answer"] = f"Error generating answer: {error_msg}"
        state["should_answer"] = False
    
    return state


def _format_success_answer(result: GeneratedAnswer, contradictions: List[Dict]) -> str:
    """Format successful answer with full details"""
    
    output = f"""## {result.mechanistic_explanation.split('\\n')[0] if result.mechanistic_explanation else 'Analysis'}

**Mechanistic Explanation:**
{result.mechanistic_explanation}

**Overall Conclusion:**
{result.overall_conclusion}

---

**Evidence Grade:** {result.evidence_grade.value}
**Confidence Score:** {result.confidence_score:.2f}

**Justification Rationale:**
{result.justification_rationale}

**Key Supporting Papers:**"""
    
    for i, paper in enumerate(result.key_papers, 1):
        output += f"\\n{i}. **{paper['title']}** — {paper['support']}"
    
    if contradictions:
        output += "\\n\\n⚠️ **Potential Contradictions Detected:**"
        for c in contradictions[:3]:
            output += f"\\n- {c['description']}"
    
    if result.uncertainty_flags:
        output += f"\\n\\n⚠️ **Uncertainty Flags:** {', '.join(result.uncertainty_flags)}"
    
    output += f"\\n\\n📊 **Limitations:** {result.limitations}"
    
    return output


def _format_low_confidence_answer(result: GeneratedAnswer) -> str:
    """Format low confidence warning"""
    
    return f"""⚠️ **INSUFFICIENT CONFIDENCE TO ANSWER**

**Confidence Score:** {result.confidence_score:.2f} (required: {MIN_ANSWER_CONFIDENCE})

**Evidence Grade:** {result.evidence_grade.value}

**Available Information:**
{result.overall_conclusion}

**Why Confidence is Low:**
{result.justification_rationale}

**Limitations:**
{result.limitations}

---

**Recommendation:**
The available evidence is insufficient for a reliable answer. Consider:
1. Refining your query with more specific medical terms
2. Checking if this is an emerging research area with limited literature
3. Consulting domain experts for clinical decisions

**Papers Found (low relevance):**
""" + "\\n".join([f"- {p['title'][:80]}..." for p in result.key_papers[:3]])


# ==================================================
# Build Enhanced LangGraph
# ==================================================
def build_multihop_graph() -> StateGraph:
    """Build the enhanced multi-hop RAG workflow"""
    
    workflow = StateGraph(RAGState)
    
    # Add all nodes
    workflow.add_node("validate", validate_query_node)
    workflow.add_node("fetch", fetch_papers_node)
    workflow.add_node("retrieve", retrieve_papers_node)
    workflow.add_node("rerank", rerank_papers_node)
    workflow.add_node("expand", expand_query_node)
    workflow.add_node("generate", generate_answer_node)
    
    # Entry point
    workflow.set_entry_point("validate")
    
    # Validation routing
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "reject": "generate",  # Will output rejection message
            "retrieve": "fetch"
        }
    )
    
    # Normal flow
    workflow.add_edge("fetch", "retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "expand")
    
    # Multi-hop loop
    workflow.add_conditional_edges(
        "expand",
        should_continue,
        {
            "continue": "retrieve",  # Loop back for more papers
            "generate": "generate"
        }
    )
    
    # End
    workflow.add_edge("generate", END)
    
    return workflow.compile()


# ==================================================
# Main MultiHopRAG Class (Enhanced)
# ==================================================
class MultiHopRAG:
    """Enhanced Multi-Hop RAG with Domain Guard and Uncertainty"""
    
    def __init__(self):
        log_info("🚀 Initializing Enhanced Multi-Hop RAG with MedGuard...")
        self.graph = build_multihop_graph()
        log_info("✅ LangGraph compiled with validation layer")

    def run(self, query: str) -> Tuple[str, List[Dict]]:
        """Run the complete RAG pipeline"""
        try:
            if not query or not isinstance(query, str):
                return "Invalid query provided.", []
            
            query = query.strip()
            log_info(f"🔬 Starting MedGuard pipeline for: '{query[:60]}...'")
            
            initial_state = RAGState(
                query=query,
                original_query=query,
                validation_result=None,
                is_validated=False,
                hop=1,
                papers=[],
                similarities=[],
                uncertainties=[],
                ranked_papers=[],
                retrieval_confidence=0.0,
                contradictions=[],
                generated_answer=None,
                final_answer="",
                should_answer=False,
                error="",
                rejection_reason=""
            )
            
            # Execute graph
            final_state = self.graph.invoke(initial_state)
            
            answer = final_state.get("final_answer", "No answer generated.")
            papers = final_state.get("ranked_papers", [])
            
            # Log completion status
            if final_state.get("validation_result") and not final_state["validation_result"].is_valid:
                log_info("🚫 Pipeline completed: Query rejected by domain guard")
            elif final_state.get("should_answer"):
                log_info(f"✅ Pipeline completed: Answer generated (confidence: {final_state.get('generated_answer', GeneratedAnswer('', '', '', None, 0.0, '', [], [], '', False)).confidence_score:.2f})")
            else:
                log_info("⚠️ Pipeline completed: Low confidence answer")
            
            return answer, papers
            
        except Exception as e:
            error_msg = handle_error(e, "MultiHopRAG.run")
            log_warning(error_msg)
            return f"Error in MedGuard pipeline: {error_msg}", []
 