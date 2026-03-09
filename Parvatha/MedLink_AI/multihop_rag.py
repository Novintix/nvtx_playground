"""
Enhanced Multi-Hop RAG with Domain Validation and Uncertainty Quantification
LangGraph-based agent workflow for MedGuard Evidence
"""

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
    query: str
    original_query: str
    response_mode: str 
    validation_result: Optional[ValidationResult]
    is_validated: bool
    hop: int
    papers: List[Dict]
    similarities: List[float]
    uncertainties: List[float]
    ranked_papers: List[Dict]
    retrieval_confidence: float
    contradictions: List[Dict]
    generated_answer: Optional[GeneratedAnswer]
    final_answer: str
    should_answer: bool
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
        
        pubmed_query = generator.normalize_pubmed_query(query)
        log_info(f"🔎 Normalized query: '{pubmed_query}'")
        
        response_mode = state.get("response_mode", "Detailed")
        mode_config = {"Concise": 8, "Detailed": 15, "Comprehensive": 25}
        max_results = mode_config.get(response_mode, 15)
        
        papers = fetcher.fetch_papers(pubmed_query, max_results=max_results)
        
        if not papers:
            log_warning("⚠️ No papers fetched from NCBI")
            state["papers"] = []
            state["error"] = "NO_PAPERS: No relevant papers found in PubMed"
            return state
        
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
        
        ranked, confidence = reranker.rerank(query, papers, similarities)
        contradictions = reranker.detect_contradictions(ranked[:5])
        
        log_info(f"✅ Re-ranked (confidence: {confidence:.3f}, contradictions: {len(contradictions)})")
        
        state["ranked_papers"] = ranked
        state["retrieval_confidence"] = confidence
        state["contradictions"] = contradictions
        
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
        
        state["hop"] = hop + 1
        
        if ranked_papers and hop < MAX_HOPS:
            expansion_terms = []
            top_titles = [p["title"] for p in ranked_papers[:2]]
            
            for title in top_titles:
                words = title.split()
                key_terms = [w for w in words if len(w) > 5 and w.isalpha()]
                expansion_terms.extend(key_terms[:3])
            
            expansion_terms = list(set(expansion_terms))[:5]
            
            if expansion_terms:
                expanded = f"{original_query} {' '.join(expansion_terms)}"
                state["query"] = expanded
                log_info(f"   Expanded with: {', '.join(expansion_terms)}")
        
    except Exception as e:
        error_msg = handle_error(e, "expand_query_node")
        log_warning(error_msg)
    
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
    
    if state.get("retrieval_confidence", 0) > 0.8 and state.get("hop", 1) > 1:
        log_info("✅ High confidence achieved, stopping early")
        return "generate"
    
    log_info(f"➡️ Continue to hop {hop + 1}")
    return "continue"


# ==================================================
# NEW: Dynamic Consistency Calculator
# ==================================================
def calculate_dynamic_consistency(papers: List[Dict]) -> Dict:
    """Calculate consistency metrics based on actual semantic similarity between papers."""
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
    
    store = get_component("store")
    
    paper_embeddings = []
    valid_papers = []
    
    for p in papers:
        emb = store.get_embedding(p["pmid"])
        if emb is not None:
            paper_embeddings.append(emb)
            valid_papers.append(p)
    
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
    
    upper_tri_indices = np.triu_indices(len(paper_embeddings), k=1)
    pairwise_sims = similarity_matrix[upper_tri_indices]
    
    avg_sim = float(np.mean(pairwise_sims))
    min_sim = float(np.min(pairwise_sims))
    std_sim = float(np.std(pairwise_sims))
    
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
    
    divergent_papers = []
    contradictions = []
    
    for i, paper in enumerate(valid_papers):
        avg_to_others = np.mean([similarity_matrix[i][j] for j in range(len(paper_embeddings)) if i != j])
        
        if avg_to_others < 0.5:
            divergent_papers.append({
                "title": paper.get("title", "Unknown")[:60],
                "pmid": paper.get("pmid"),
                "avg_similarity": float(avg_to_others)
            })
        
        for j in range(i + 1, len(valid_papers)):
            if similarity_matrix[i][j] < 0.4:
                contradictions.append({
                    "paper_a": valid_papers[i].get("title", "Unknown")[:50],
                    "paper_b": valid_papers[j].get("title", "Unknown")[:50],
                    "similarity": float(similarity_matrix[i][j])
                })
    
    agreement_details = []
    for i, paper in enumerate(valid_papers[:3]):
        label = "Strong support" if i == 0 else "Supports findings" if i == 1 else "Consistent with mechanism"
        agreement_details.append({
            "title": paper.get("title", "Unknown"),
            "agreement": label
        })
    
    return {
        "consistency_score": round(avg_sim, 3),
        "agreement_level": agreement_level,
        "agreement_details": agreement_details,
        "contradictions": contradictions,
        "avg_similarity": round(avg_sim, 3),
        "min_similarity": round(min_sim, 3),
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
        
        result = generator.generate_structured_answer(
            query=original_query,
            papers=papers,
            retrieval_confidence=confidence,
            response_mode=response_mode
        )
        
        state["generated_answer"] = result
        state["should_answer"] = result.should_answer
        
        consistency_analysis = calculate_dynamic_consistency(papers)
        
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
# FORMATTING - PROFESSIONAL STRUCTURED OUTPUT
# ==================================================

def _format_success_answer(result: GeneratedAnswer, consistency_analysis: Dict, papers: List[Dict], mode: str = "Detailed") -> str:
    """Format successful answer with professional structure and dropdowns"""
    
    # Mode-based answer length
    mode_config = {
        "Concise": {"sentences": 2, "detail": "brief"},
        "Detailed": {"sentences": 4, "detail": "standard"},
        "Comprehensive": {"sentences": 8, "detail": "in-depth"}
    }
    config = mode_config.get(mode, mode_config["Detailed"])
    
    # 1. MAIN ANSWER (varies by mode)
    main_answer = _format_main_answer(result.mechanistic_explanation, config["sentences"])
    
    output = f"""## 📋 Answer

{main_answer}

---

## 🔬 Key Findings

"""
    
    # 2. KEY FINDINGS (Discoveries made during research)
    key_findings = _extract_key_findings(papers, result)
    for finding in key_findings:
        output += f"{finding}\n\n"
    
    # 3. MECHANISTIC EXPLANATION (Point-wise)
    mechanism_points = _format_mechanism_points(result.mechanistic_explanation)
    
    output += f"""---

## 🧬 Mechanistic Explanation

{mechanism_points}

---

## ✅ Consistency Assessment

**Status:** {consistency_analysis['agreement_level']} Consensus (Score: {consistency_analysis['consistency_score']:.2f})

**Supporting Papers:**
"""
    
    # Supporting papers - full titles, not truncated
    for i, detail in enumerate(consistency_analysis.get("agreement_details", [])[:3], 1):
        output += f"\n{i}. **{detail['title']}**  \n   *{detail['agreement']}*"
    
    # Check gap
    gap = abs(result.confidence_score - consistency_analysis['consistency_score'])
    if gap > 0.15:
        output += f"\n\n> ⚠️ **Note:** Confidence ({result.confidence_score:.2f}) and consistency ({consistency_analysis['consistency_score']:.2f}) diverge. Evidence is semantically similar but may lack citations/recency."
    
    # DIVERGENT PAPERS (if any)
    if consistency_analysis.get("divergent_papers"):
        output += "\n\n**⚠️ Divergent Sources:**\n\n"
        for div in consistency_analysis["divergent_papers"][:2]:
            output += f"• {div['title']}... (similarity: {div['avg_similarity']:.2f})\n"
    
    output += f"""

---

## 📊 Confidence & Evidence Summary

| Metric | Value | Definition |
|--------|-------|------------|
| **Confidence Score** | {result.confidence_score:.2f}/1.0 | Overall reliability based on evidence quality, quantity, and agreement |
| **Consistency Score** | {consistency_analysis['consistency_score']:.2f}/1.0 | Semantic agreement between papers (0=disagree, 1=identical) |
| **Papers Reviewed** | {len(papers)} | Number of peer-reviewed articles analyzed |
| **Recent Papers** | {len([p for p in papers if p.get('year', 0) >= 2020])} | Papers published from 2020 onwards |

"""
    
    # DROPDOWN SECTIONS FOR DETAILED INFO
    output += _create_dropdown_sections(result, papers, consistency_analysis)
    
    return output


def _format_main_answer(mechanism_text: str, sentence_count: int) -> str:
    """Format main answer with appropriate length based on mode"""
    if not mechanism_text or mechanism_text == "Not provided":
        return "Answer not available."
    
    import re
    sentences = re.split(r'(?<=[.!?])\s+', mechanism_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    # Take required number of sentences
    selected = sentences[:sentence_count]
    
    return " ".join(selected)


def _extract_key_findings(papers: List[Dict], result: GeneratedAnswer) -> List[str]:
    """Extract key discoveries made during research"""
    findings = []
    
    # Finding 1: Main mechanism discovered
    if result.mechanistic_explanation and result.mechanistic_explanation != "Not provided":
        import re
        sentences = re.split(r'(?<=[.!?])\s+', result.mechanistic_explanation)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        if sentences:
            first_key = sentences[0]
            if len(first_key) > 150:
                first_key = first_key[:147] + "..."
            findings.append(f"• **Primary Discovery:** {first_key}")
    
    # Finding 2: Evidence strength
    high_quality = len([p for p in papers if p.get('final_score', 0) > 0.8])
    findings.append(f"• **Evidence Strength:** {high_quality} high-quality papers identified (score >0.8)")
    
    # Finding 3: Temporal coverage
    years = [p.get('year', 0) for p in papers if p.get('year', 0) > 0]
    if years:
        year_range = max(years) - min(years) if len(years) > 1 else 0
        findings.append(f"• **Research Span:** Evidence spans {year_range} years ({min(years)}-{max(years)})")
    
    # Finding 4: Top source
    if papers and papers[0].get('journal'):
        findings.append(f"• **Leading Source:** {papers[0].get('journal')} (Score: {papers[0].get('final_score', 0):.3f})")
    
    # Finding 5: Consistency finding
    if result.confidence_score >= 0.8:
        findings.append(f"• **Agreement Level:** Strong consensus across all reviewed papers")
    elif result.confidence_score >= 0.6:
        findings.append(f"• **Agreement Level:** Moderate consensus with minor variations")
    else:
        findings.append(f"• **Agreement Level:** Mixed evidence requiring further validation")
    
    return findings


def _format_mechanism_points(mechanism_text: str) -> str:
    """Format mechanism as clean bullet points"""
    if not mechanism_text or mechanism_text == "Not provided":
        return "• Mechanistic explanation not available."
    
    import re
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', mechanism_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if len(sentences) <= 3:
        return "\n\n".join([f"• {s}" for s in sentences])
    
    # Categorize into logical groups
    problem = []
    mechanism = []
    outcome = []
    
    for sent in sentences:
        sent_lower = sent.lower()
        
        if any(w in sent_lower for w in ['develops', 'impaired', 'dysfunction', 'defect', 'resistance', 'associated with']):
            if 'mechanism' not in sent_lower and 'treatment' not in sent_lower:
                problem.append(sent)
                continue
        
        if any(w in sent_lower for w in ['mechanism', 'pathway', 'signaling', 'activation', 'modulates', 'regulates', 'through', 'via']):
            mechanism.append(sent)
            continue
        
        if any(w in sent_lower for w in ['improves', 'restores', 'promotes', 'treatment', 'drug', 'therapeutic']):
            outcome.append(sent)
            continue
        
        mechanism.append(sent)
    
    output = []
    
    if problem:
        output.append("**Pathophysiology:**")
        for s in problem[:2]:
            output.append(f"• {s}")
        output.append("")
    
    if mechanism:
        output.append("**Cellular Mechanism:**")
        for s in mechanism[:4]:
            output.append(f"• {s}")
        output.append("")
    
    if outcome:
        output.append("**Clinical Implications:**")
        for s in outcome[:2]:
            output.append(f"• {s}")
    
    return "\n\n".join(output) if output else "\n\n".join([f"• {s}" for s in sentences[:5]])


def _create_dropdown_sections(result: GeneratedAnswer, papers: List[Dict], consistency_analysis: Dict) -> str:
    """Create collapsible dropdown sections for detailed info"""
    
    # Justification content
    justification = result.justification_rationale if result.justification_rationale else "Based on systematic review of retrieved literature."
    
    # Limitations content
    limitations = result.limitations if result.limitations else "Standard limitations apply to observational studies."
    
    # Internal consistency explanation
    internal_consistency = f"{consistency_analysis['consistency_score']:.2f} - " + {
        "Very High": "Papers show near-identical conclusions",
        "High": "Strong agreement across all sources",
        "Moderate": "General agreement with minor differences",
        "Partial": "Some agreement, some divergence",
        "Low": "Significant disagreement between sources"
    }.get(consistency_analysis['agreement_level'], "Agreement level unclear")
    
    # Paper-specific findings
    paper_findings = ""
    for i, p in enumerate(papers[:5], 1):
        paper_findings += f"**Paper {i}:** {p.get('title', 'Unknown')[:100]}...  \n"
        paper_findings += f"→ Relevance: {p.get('final_score', 0):.3f} | Year: {p.get('year', 'N/A')} | Citations: {p.get('citations', 'N/A')}\n\n"
    
    # Paper-specific limitations
    paper_limits = ""
    for i, p in enumerate(papers[:5], 1):
        # Generate limitation based on paper characteristics
        limits = []
        if p.get('year', 0) < 2020:
            limits.append("Older study")
        if p.get('citations', 0) < 50:
            limits.append("Limited citations")
        if p.get('final_score', 0) < 0.7:
            limits.append("Lower relevance")
        
        if limits:
            paper_limits += f"**Paper {i}:** {', '.join(limits)}\n\n"
    
    # Build dropdown HTML
    output = f"""
<details>
<summary>📄 <b>Justification</b> (Click to expand)</summary>

{justification}

</details>

<details>
<summary>⚠️ <b>Limitations</b> (Click to expand)</summary>

{limitations}

</details>

<details>
<summary>🔍 <b>Internal Consistency</b> (Click to expand)</summary>

**Score:** {internal_consistency}

*Definition: Measures how semantically similar the papers are (0=completely disagree, 1=completely agree)*

</details>

<details>
<summary>📝 <b>Paper-Specific Findings</b> (Click to expand)</summary>

{paper_findings}

</details>

<details>
<summary>⚡ <b>Paper-Specific Limitations</b> (Click to expand)</summary>

{paper_limits if paper_limits else "No specific limitations noted for top papers."}

</details>
"""
    
    return output


def _format_low_confidence_answer(result: GeneratedAnswer) -> str:
    """Format low confidence warning"""
    
    output = f"""## ⚠️ Low Confidence Analysis

**Confidence Score:** {result.confidence_score:.2f}/1.0

---

## 📝 Available Information

{result.overall_conclusion}

---

## 📚 Papers Found (Low Relevance)

"""
    for i, paper in enumerate(result.key_papers[:3], 1):
        output += f"{i}. {paper['title'][:80]}...  \n   Score: {paper['support']}\n\n"
    
    output += """

---

_⚠️ This answer has LOW CONFIDENCE. Use for exploratory purposes only._
"""
    return output


# ==================================================
# Build Enhanced LangGraph
# ==================================================
def build_multihop_graph() -> StateGraph:
    """Build the enhanced multi-hop RAG workflow"""
    
    workflow = StateGraph(RAGState)
    
    workflow.add_node("validate", validate_query_node)
    workflow.add_node("fetch", fetch_papers_node)
    workflow.add_node("retrieve", retrieve_papers_node)
    workflow.add_node("rerank", rerank_papers_node)
    workflow.add_node("expand", expand_query_node)
    workflow.add_node("generate", generate_answer_node)
    
    workflow.set_entry_point("validate")
    
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {"reject": "generate", "retrieve": "fetch"}
    )
    
    workflow.add_edge("fetch", "retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "expand")
    
    workflow.add_conditional_edges(
        "expand",
        should_continue,
        {"continue": "retrieve", "generate": "generate"}
    )
    
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
            
            final_state = self.graph.invoke(initial_state)
            
            answer = final_state.get("final_answer", "No answer generated.")
            papers = final_state.get("ranked_papers", [])
            
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