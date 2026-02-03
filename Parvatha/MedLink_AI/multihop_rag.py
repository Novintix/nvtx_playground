from typing import List, Dict, Tuple, TypedDict, Optional
from langgraph.graph import StateGraph, END
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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
    response_mode: str 
    
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
        
        # Fetch papers - DYNAMIC based on mode
        response_mode = state.get("response_mode", "Detailed")
        mode_config = {
            "Concise": 8,
            "Detailed": 15,
            "Comprehensive": 25
        }
        max_results = mode_config.get(response_mode, 15)
        
        papers = fetcher.fetch_papers(pubmed_query, max_results=max_results)
        
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
# NEW: Dynamic Consistency Calculator
# ==================================================
def calculate_dynamic_consistency(papers: List[Dict]) -> Dict:
    """
    Calculate consistency metrics based on actual semantic similarity between papers.
    Returns detailed consistency analysis for dynamic assessment.
    """
    if not papers or len(papers) < 2:
        return {
            "consistency_score": 1.0 if papers else 0.0,
            "agreement_level": "High" if papers else "Insufficient",
            "agreement_details": [],
            "contradictions": [],
            "avg_similarity": 0.0,
            "min_similarity": 0.0,
            "divergent_papers": []
        }
    
    # Get embeddings from store
    store = get_component("store")
    
    paper_embeddings = []
    valid_papers = []
    
    for p in papers:
        emb = store.get_embedding(p["pmid"])
        if emb is not None:
            paper_embeddings.append(emb)
            valid_papers.append(p)
    
    # Calculate pairwise similarities
    if len(paper_embeddings) < 2:
        return {
            "consistency_score": 0.5,
            "agreement_level": "Unknown",
            "agreement_details": [],
            "contradictions": [],
            "avg_similarity": 0.0,
            "min_similarity": 0.0,
            "divergent_papers": []
        }
    
    embeddings_matrix = np.array(paper_embeddings)
    similarity_matrix = cosine_similarity(embeddings_matrix)
    
    # Get upper triangle (excluding diagonal)
    upper_tri_indices = np.triu_indices(len(paper_embeddings), k=1)
    pairwise_sims = similarity_matrix[upper_tri_indices]
    
    avg_sim = float(np.mean(pairwise_sims))
    min_sim = float(np.min(pairwise_sims))
    max_sim = float(np.max(pairwise_sims))
    std_sim = float(np.std(pairwise_sims))
    
    # Determine agreement level based on distribution
    if avg_sim >= 0.85 and std_sim < 0.1:
        agreement_level = "Very High"
    elif avg_sim >= 0.75 and std_sim < 0.15:
        agreement_level = "High"
    elif avg_sim >= 0.65:
        agreement_level = "Moderate"
    elif avg_sim >= 0.5:
        agreement_level = "Partial"
    else:
        agreement_level = "Low"
    
    # Find divergent papers (those with low average similarity to others)
    divergent_papers = []
    contradictions = []
    
    for i, paper in enumerate(valid_papers):
        # Average similarity of this paper to all others
        avg_to_others = np.mean([similarity_matrix[i][j] for j in range(len(paper_embeddings)) if i != j])
        
        if avg_to_others < 0.5:
            divergent_papers.append({
                "title": paper.get("title", "Unknown")[:60],
                "pmid": paper.get("pmid"),
                "avg_similarity": float(avg_to_others)
            })
        
        # Check for specific contradictions (very low similarity pairs)
        for j in range(i + 1, len(valid_papers)):
            if similarity_matrix[i][j] < 0.4:
                contradictions.append({
                    "paper_a": valid_papers[i].get("title", "Unknown")[:50],
                    "paper_b": valid_papers[j].get("title", "Unknown")[:50],
                    "similarity": float(similarity_matrix[i][j])
                })
    
    # Generate agreement details
    agreement_details = []
    for i, paper in enumerate(valid_papers[:3]):
        if i == 0:
            label = "Strong support"
        elif i == 1:
            label = "Supports findings"
        else:
            label = "Consistent with mechanism"
        agreement_details.append({
            "title": paper.get("title", "Unknown")[:60],
            "agreement": label
        })
    
    return {
        "consistency_score": round(avg_sim, 3),
        "agreement_level": agreement_level,
        "agreement_details": agreement_details,
        "contradictions": contradictions,
        "avg_similarity": round(avg_sim, 3),
        "min_similarity": round(min_sim, 3),
        "max_similarity": round(max_sim, 3),
        "similarity_std": round(std_sim, 3),
        "divergent_papers": divergent_papers
    }


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
        response_mode = state.get("response_mode", "Detailed")
        
        log_info(f"🧠 Generating structured answer (mode: {response_mode})...")
        
        if not papers:
            state["final_answer"] = "No relevant papers found to answer this query."
            state["should_answer"] = False
            return state
        
        generator = get_component("generator")
        
        # Generate structured answer with uncertainty and MODE
        result = generator.generate_structured_answer(
            query=original_query,
            papers=papers,
            retrieval_confidence=confidence,
            response_mode=response_mode
        )
        
        state["generated_answer"] = result
        state["should_answer"] = result.should_answer
        
        # Calculate DYNAMIC consistency based on paper embeddings
        consistency_analysis = calculate_dynamic_consistency(papers)
        
        # Format final answer with MODE and DYNAMIC consistency
        if result.should_answer:
            state["final_answer"] = _format_success_answer(
                result, 
                consistency_analysis,
                papers, 
                response_mode
            )
        else:
            state["final_answer"] = _format_low_confidence_answer(result)
        
        log_info(f"✅ Answer generated (confidence: {result.confidence_score:.3f}, consistency: {consistency_analysis['consistency_score']:.3f})")
        
    except Exception as e:
        error_msg = handle_error(e, "generate_answer_node")
        log_warning(error_msg)
        state["error"] = error_msg
        state["final_answer"] = f"Error generating answer: {error_msg}"
        state["should_answer"] = False
    
    return state


# ==================================================
# FORMATTING - 7 MANDATORY SECTIONS ONLY (FIXED)
# ==================================================

def _format_success_answer(result: GeneratedAnswer, consistency_analysis: Dict, papers: List[Dict], mode: str = "Detailed") -> str:
    """Format successful answer - 7 MANDATORY SECTIONS ONLY with DYNAMIC consistency"""
    
    # 1. EXECUTIVE SUMMARY (Answer Reasoning)
    output = f"""## 📋 Executive Summary

{result.overall_conclusion}

---

## 🔬 Key Findings

"""
    
    # 2. KEY FINDINGS (Bullet points)
    findings = _extract_key_findings(result.mechanistic_explanation, max_findings=5)
    for finding in findings:
        output += f"• {finding}\n"
    
    # 3. MECHANISTIC EXPLANATION
    output += f"""
---

## 🧬 Mechanistic Explanation

{result.mechanistic_explanation}

"""
    
    # 4 & 5. CONSISTENCY + CONFIDENCE SCORE (FIXED - DYNAMIC)
    output += _generate_consistency_section(consistency_analysis, papers, result.confidence_score)
    
    # 6. REFERENCE PAPERS - REMOVED FROM HERE (will be added in app.py to avoid duplication)
    # The reference papers section is now handled in app.py to prevent duplication
    
    return output


def _generate_consistency_section(consistency_analysis: Dict, papers: List[Dict], confidence_score: float) -> str:
    """
    Generate consistency section with DYNAMIC assessment based on actual paper similarities.
    Score and text are now aligned.
    """
    agreement_level = consistency_analysis.get("agreement_level", "Unknown")
    consistency_score = consistency_analysis.get("consistency_score", 0.0)
    min_sim = consistency_analysis.get("min_similarity", 0.0)
    contradictions = consistency_analysis.get("contradictions", [])
    divergent_papers = consistency_analysis.get("divergent_papers", [])
    
    # NEW: Detect confidence-consistency misalignment
    confidence_consistency_gap = abs(confidence_score - consistency_score)
    alignment_warning = ""
    if confidence_consistency_gap > 0.15:
        alignment_warning = f"\n\n⚠️ **Note:** Confidence ({confidence_score:.2f}) and consistency ({consistency_score:.2f}) show significant divergence. This may indicate the evidence is semantically similar but limited in other quality metrics (citations, recency, or evidence grade)."
    
    # Determine status and description based on actual consistency score
    if agreement_level == "Very High":
        status_icon = "✅"
        status_text = "Strong Consensus"
        description = "All papers show strong semantic agreement with minimal divergence."
    elif agreement_level == "High":
        status_icon = "✅"
        status_text = "High Agreement"
        description = "Papers largely agree on main findings with minor variations."
    elif agreement_level == "Moderate":
        status_icon = "⚠️"
        status_text = "Moderate Agreement"
        description = "Most papers align, but some differences in emphasis or scope exist."
    elif agreement_level == "Partial":
        status_icon = "⚠️"
        status_text = "Partial Agreement"
        description = "Mixed evidence with some papers supporting different aspects or conclusions."
    else:
        status_icon = "🚫"
        status_text = "Low Agreement / Disagreement"
        description = "Significant divergence between papers. Results should be interpreted with caution."
    
    # Build agreement details dynamically
    agreement_details = []
    for detail in consistency_analysis.get("agreement_details", []):
        agreement_details.append(f"• {detail['title']}... - {detail['agreement']}")
    
    output = f"""---

## {status_icon} Consistency Assessment

**Status:** {status_text} (Score: {consistency_score:.2f})

**Description:** {description}
"""
    
    # Add alignment warning if detected
    output += alignment_warning
    
    # Add agreement details if available
    if agreement_details:
        output += "\n\n**Agreement Details:**\n"
        for detail in agreement_details[:3]:
            output += f"{detail}\n"
    
    # Add divergence warnings if applicable
    if divergent_papers:
        output += "\n**Divergent Sources:**\n"
        for div in divergent_papers[:2]:
            output += f"• {div['title']}... (similarity: {div['avg_similarity']:.2f})\n"
    
    # Add contradictions if found
    if contradictions:
        output += "\n**Contradictions Found:**\n"
        for i, c in enumerate(contradictions[:2], 1):
            output += f"• Paper pair shows low agreement (sim: {c['similarity']:.2f})\n"
    
    # Confidence score with context
    output += f"""

---

## 📊 Confidence Score

**{confidence_score:.2f}/1.0** - Based on {len(papers)} papers (consistency: {consistency_score:.2f}, min similarity: {min_sim:.2f})

"""
    
    return output

def _format_low_confidence_answer(result: GeneratedAnswer) -> str:
    """Format low confidence warning - MINIMAL VERSION"""
    
    output = f"""## ⚠️ Low Confidence Analysis

**Confidence Score:** {result.confidence_score:.2f}/1.0

---

## 📝 Available Information

{result.overall_conclusion}

---

## 📚 Papers Found (Low Relevance)

"""
    for i, paper in enumerate(result.key_papers[:3], 1):
        output += f"{i}. {paper['title'][:80]}... (Score: {paper['support']})\n"
    
    output += f"""

---

*⚠️ This answer has LOW CONFIDENCE. Use for exploratory purposes only.*
"""
    return output


def _extract_key_findings(mechanism_text: str, max_findings: int = 5) -> List[str]:
    """Extract bullet points from mechanistic explanation"""
    if not mechanism_text or mechanism_text == "Not provided":
        return ["Key findings not available"]
    
    sentences = mechanism_text.split('.')
    findings = []
    
    for s in sentences:
        s = s.strip()
        if len(s) > 20 and len(s) < 200:
            findings.append(s)
        if len(findings) >= max_findings:
            break
    
    return findings if findings else ["See mechanistic explanation for details"]


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
            "reject": "generate",
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
            "continue": "retrieve",
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

    def run(self, query: str, response_mode: str = "Detailed") -> Tuple[str, List[Dict]]:
        """Run the complete RAG pipeline with MODE support"""
        try:
            if not query or not isinstance(query, str):
                return "Invalid query provided.", []
            
            query = query.strip()
            log_info(f"🔬 Starting MedGuard pipeline for: '{query[:60]}...' (Mode: {response_mode})")
            
            initial_state = RAGState(
                query=query,
                original_query=query,
                response_mode=response_mode,
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