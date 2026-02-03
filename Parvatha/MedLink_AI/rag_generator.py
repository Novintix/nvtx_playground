# rag_generator.py
import os
import time
import re
import requests
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

from error_handler import log_info, log_warning
from config import MIN_ANSWER_CONFIDENCE

load_dotenv()


class EvidenceGrade(Enum):
    A = "A: Strong Evidence (Systematic Review/Multiple RCTs)"
    B = "B: Good Evidence (Single RCT/Strong Cohort)"
    C = "C: Moderate Evidence (Cohort/Case-Control)"
    D = "D: Weak Evidence (Expert Opinion/Limited Data)"
    INSUFFICIENT = "Insufficient Evidence"


@dataclass
class GeneratedAnswer:
    answer_text: str
    mechanistic_explanation: str
    overall_conclusion: str
    evidence_grade: EvidenceGrade
    confidence_score: float
    justification_rationale: str
    key_papers: List[Dict]
    uncertainty_flags: List[str]
    limitations: str
    should_answer: bool


class MedicalRAGGenerator:
    def __init__(self):
        log_info("🧠 Initializing Groq API for Medical RAG...")

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY missing")

        self.model = "llama-3.1-8b-instant"
        # FIXED: No trailing space
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        log_info(f"✅ Groq ready with model: {self.model}")

    def generate_structured_answer(
        self,
        query: str,
        papers: List[Dict],
        retrieval_confidence: float,
        response_mode: str = "Detailed"
    ) -> GeneratedAnswer:
        
        if not papers:
            return GeneratedAnswer(
                answer_text="No relevant papers found to answer this query.",
                mechanistic_explanation="No mechanistic explanation available.",
                overall_conclusion="Insufficient evidence available.",
                evidence_grade=EvidenceGrade.INSUFFICIENT,
                confidence_score=0.0,
                justification_rationale="No papers were retrieved for this query.",
                key_papers=[],
                uncertainty_flags=[],
                limitations="No primary literature identified.",
                should_answer=False
            )
        
        evidence_stats = self._calculate_evidence_stats(papers)
        evidence_grade = self._determine_evidence_grade(evidence_stats, retrieval_confidence)
        evidence_text = self._prepare_evidence_text(papers)
        
        # Generate answer with LLM - PASS MODE
        llm_response = self._call_llm_for_answer(
            query, 
            evidence_text, 
            evidence_stats,
            response_mode
        )
        
        final_confidence = self._calculate_final_confidence(
            retrieval_confidence,
            evidence_stats,
            evidence_grade,
            llm_response.get("internal_consistency", 0.5)
        )
        
        should_answer = final_confidence >= MIN_ANSWER_CONFIDENCE
        
        # Keep uncertainty_flags for internal use but don't show in output
        uncertainty_flags = self._identify_uncertainty_flags(
            papers, evidence_stats, evidence_grade, llm_response
        )
        
        return GeneratedAnswer(
            answer_text=llm_response.get("title", "") + "\n\n" + llm_response.get("mechanism", ""),
            mechanistic_explanation=llm_response.get("mechanism", ""),
            overall_conclusion=llm_response.get("conclusion", ""),
            evidence_grade=evidence_grade,
            confidence_score=final_confidence,
            justification_rationale=llm_response.get("justification", ""),
            key_papers=[{
                "pmid": p.get("pmid"),
                "title": p.get("title"),
                "year": p.get("year"),
                "support": f"{p.get('final_score', 0):.3f}"
            } for p in papers[:5]],
            uncertainty_flags=uncertainty_flags,  # Keep for internal but don't display
            limitations=self._generate_limitations(papers, evidence_stats),
            should_answer=should_answer
        )

    def _calculate_evidence_stats(self, papers: List[Dict]) -> Dict:
        years = [p.get("year", 0) for p in papers if p.get("year", 0) > 0]
        citations = [p.get("citations", 0) for p in papers]
        scores = [p.get("final_score", 0) for p in papers]
        
        return {
            "n_papers": len(papers),
            "mean_year": sum(years) / len(years) if years else 0,
            "year_range": max(years) - min(years) if len(years) > 1 else 0,
            "mean_citations": sum(citations) / len(citations) if citations else 0,
            "total_citations": sum(citations),
            "mean_score": sum(scores) / len(scores) if scores else 0,
            "top_score": max(scores) if scores else 0,
            "score_std": (sum((x - sum(scores)/len(scores))**2 for x in scores) / len(scores))**0.5 if scores else 0,
            "n_recent": len([y for y in years if y >= 2020]),
            "has_high_impact": any(p.get("final_score", 0) > 0.8 for p in papers)
        }

    def _determine_evidence_grade(self, stats: Dict, retrieval_confidence: float) -> EvidenceGrade:
        quality_score = stats["mean_score"] * 100
        quantity_score = min(stats["n_papers"] * 10, 30)
        recency_score = min(stats["n_recent"] * 5, 20)
        impact_bonus = 10 if stats["has_high_impact"] else 0
        
        total_score = quality_score + quantity_score + recency_score + impact_bonus
        
        if retrieval_confidence < 0.5:
            return EvidenceGrade.INSUFFICIENT
        
        if total_score >= 85:
            return EvidenceGrade.A
        elif total_score >= 70:
            return EvidenceGrade.B
        elif total_score >= 55:
            return EvidenceGrade.C
        elif total_score >= 40:
            return EvidenceGrade.D
        else:
            return EvidenceGrade.INSUFFICIENT

    def _prepare_evidence_text(self, papers: List[Dict]) -> str:
        evidence_blocks = []
        for i, p in enumerate(papers[:6], 1):
            abstract = p.get("abstract", "")
            if isinstance(abstract, list):
                abstract = " ".join(str(x) for x in abstract)
            
            title = p.get("title", "Unknown Title")
            year = p.get("year", "Unknown")
            journal = p.get("journal", "Unknown Journal")
            
            evidence_blocks.append(
                f"--- Paper {i} ---\n"
                f"Title: {title}\n"
                f"Journal: {journal} ({year})\n"
                f"PMID: {p.get('pmid', 'N/A')}\n"
                f"Relevance Score: {p.get('final_score', 0):.3f}\n"
                f"Abstract: {abstract[:800]}\n"
            )
        
        return "\n\n".join(evidence_blocks)

    def _call_llm_for_answer(
        self,
        query: str,
        evidence_text: str,
        evidence_stats: Dict,
        response_mode: str = "Detailed"
    ) -> Dict:
        """Call LLM to generate structured answer with MODE-SPECIFIC instructions"""
        
        # MODE-SPECIFIC instructions
        mode_instructions = {
            "Concise": """You are a rigorous biomedical research analyst.
Provide a BRIEF, FOCUSED answer:
- Maximum 2-3 sentences per section
- Focus ONLY on the most important finding
- No examples, no deep mechanisms
- Executive Summary: 1-2 sentences only
- Be direct and concise""",
            
            "Detailed": """You are a rigorous biomedical research analyst.
Provide a COMPLETE, BALANCED answer:
- Explain mechanisms clearly but concisely
- Include key supporting evidence
- Moderate depth in all sections
- Balance breadth and depth
- 3-5 sentences per section""",
            
            "Comprehensive": """You are a rigorous biomedical research analyst.
Provide an IN-DEPTH, THOROUGH analysis:
- Deep mechanistic explanations with specific examples
- Discuss nuanced findings and caveats
- Maximum detail in all sections
- 5-8 sentences per section, with specific molecular/cellular details where possible"""
        }
        
        system_prompt = f"""{mode_instructions.get(response_mode, mode_instructions["Detailed"])}

CRITICAL RULES:
1. Use ONLY the provided evidence - do not use external knowledge
2. If evidence is insufficient or contradictory, explicitly state this
3. Provide mechanistic explanations when possible
4. Rate your confidence honestly
5. Flag any limitations or uncertainties

Respond in this exact format:

TITLE: <concise scientific title>

MECHANISM: <mechanistic explanation>

CONCLUSION: <2-3 sentence synthesis>

JUSTIFICATION: <why this evidence supports this conclusion>

INTERNAL_CONSISTENCY: <number 0-1 indicating how well papers agree>

CONTRADICTIONS_FOUND: <yes/no and brief description if yes>"""

        user_prompt = f"""Based on the following {evidence_stats['n_papers']} research papers, answer this question:

Question: {query}

Evidence Statistics:
- Average Paper Score: {evidence_stats['mean_score']:.3f}
- Papers from 2020+: {evidence_stats['n_recent']}
- Publication Year Range: {evidence_stats['year_range']} years

Evidence:
{evidence_text}

Provide your analysis in the requested format."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Mode-specific token limits
        token_limits = {
            "Concise": 400,
            "Detailed": 700,
            "Comprehensive": 1200
        }
        max_tokens = token_limits.get(response_mode, 700)
        
        response = self._call_groq(messages, temperature=0.3, max_tokens=max_tokens)
        
        if not response:
            log_warning("⚠️ LLM returned empty response - API might have failed")
            return {
                "title": "Error in Analysis",
                "mechanism": "Unable to generate analysis - API failure.",
                "conclusion": "System error during answer generation.",
                "justification": "LLM API failure.",
                "internal_consistency": 0.0,
                "contradictions": "unknown"
            }
        
        return self._parse_llm_response(response)

    def _parse_llm_response(self, response: str) -> Dict:
        """Parse structured LLM response"""
        result = {}
        
        title_match = re.search(r'TITLE:\s*(.+?)(?=\n|$)', response, re.IGNORECASE)
        mechanism_match = re.search(r'MECHANISM:\s*(.+?)(?=\nCONCLUSION|\nJUSTIFICATION|$)', response, re.DOTALL | re.IGNORECASE)
        conclusion_match = re.search(r'CONCLUSION:\s*(.+?)(?=\nJUSTIFICATION|$)', response, re.DOTALL | re.IGNORECASE)
        justification_match = re.search(r'JUSTIFICATION:\s*(.+?)(?=\nINTERNAL_CONSISTENCY|$)', response, re.DOTALL | re.IGNORECASE)
        consistency_match = re.search(r'INTERNAL_CONSISTENCY:\s*([0-9.]+)', response, re.IGNORECASE)
        contradictions_match = re.search(r'CONTRADICTIONS_FOUND:\s*(.+?)(?=\n|$)', response, re.IGNORECASE)
        
        result["title"] = title_match.group(1).strip() if title_match else "Research Analysis"
        result["mechanism"] = mechanism_match.group(1).strip() if mechanism_match else "Mechanism not clearly established in evidence."
        result["conclusion"] = conclusion_match.group(1).strip() if conclusion_match else "Based on the available evidence, further research is needed."
        result["justification"] = justification_match.group(1).strip() if justification_match else "Evidence base is limited."
        result["internal_consistency"] = float(consistency_match.group(1)) if consistency_match else 0.5
        result["contradictions"] = contradictions_match.group(1).strip() if contradictions_match else "unknown"
        
        log_info(f"Parsed LLM response: title='{result['title'][:50]}...', mechanism='{result['mechanism'][:50]}...'")
        
        return result

    def _calculate_final_confidence(
        self, 
        retrieval_confidence: float, 
        evidence_stats: Dict, 
        evidence_grade: EvidenceGrade, 
        internal_consistency: float
    ) -> float:
        """
        Calculate final calibrated confidence score.
        FIXED: Properly weights consistency to avoid contradiction with consistency score.
        """
        # Base components
        base_conf = retrieval_confidence
        quality_factor = evidence_stats["mean_score"]
        quantity_factor = min(evidence_stats["n_papers"] / 5, 1.0)
        
        grade_factors = {
            EvidenceGrade.A: 1.0, EvidenceGrade.B: 0.90, EvidenceGrade.C: 0.78,
            EvidenceGrade.D: 0.65, EvidenceGrade.INSUFFICIENT: 0.40
        }
        grade_factor = grade_factors.get(evidence_grade, 0.5)
        
        # INTERNAL_CONSISTENCY is the key - this should dominate if high
        # If papers agree strongly (0.98), confidence should reflect that
        
        # NEW: Consistency-weighted calculation
        # High consistency (>0.85) should pull confidence up significantly
        # Low consistency (<0.50) should pull confidence down significantly
        
        consistency_boost = 0.0
        if internal_consistency >= 0.90:
            consistency_boost = 0.15  # Boost for very high consistency
        elif internal_consistency >= 0.75:
            consistency_boost = 0.05  # Small boost for good consistency
        elif internal_consistency < 0.50:
            consistency_boost = -0.20  # Heavy penalty for inconsistency
        
        # Calculate weighted base
        base_calculation = (
            0.25 * base_conf + 
            0.20 * quality_factor + 
            0.10 * quantity_factor +
            0.15 * grade_factor +
            0.30 * internal_consistency  # INCREASED weight on consistency
        )
        
        # Apply consistency boost/penalty
        final_confidence = base_calculation + consistency_boost
        
        # Hard floor/ceiling based on consistency extremes
        if internal_consistency >= 0.95:
            final_confidence = max(final_confidence, 0.88)  # Very high consistency = high confidence floor
        elif internal_consistency >= 0.85:
            final_confidence = max(final_confidence, 0.75)  # High consistency = good confidence floor
        elif internal_consistency < 0.40:
            final_confidence = min(final_confidence, 0.50)  # Low consistency = cap confidence
        
        return round(min(max(final_confidence, 0.0), 1.0), 3)

    def _identify_uncertainty_flags(
        self,
        papers: List[Dict],
        stats: Dict,
        grade: EvidenceGrade,
        llm_response: Dict
    ) -> List[str]:
        """Identify specific uncertainty factors (internal use only)"""
        
        flags = []
        
        if stats["n_papers"] < 3:
            flags.append("LIMITED_LITERATURE")
        
        if stats["year_range"] > 15:
            flags.append("TEMPORAL_HETEROGENEITY")
        
        if stats["mean_score"] < 0.6:
            flags.append("LOW_RELEVANCE_MATCH")
        
        if llm_response.get("contradictions", "").lower().startswith("yes"):
            flags.append("CONTRADICTORY_FINDINGS")
        
        if grade in [EvidenceGrade.D, EvidenceGrade.INSUFFICIENT]:
            flags.append("WEAK_EVIDENCE_BASE")
        
        if stats["n_recent"] == 0:
            flags.append("NO_RECENT_STUDIES")
        
        return flags

    def _generate_limitations(self, papers: List[Dict], stats: Dict) -> str:
        """Generate limitations statement"""
        
        limitations = []
        
        if stats["n_papers"] < 5:
            limitations.append(f"Limited evidence base ({stats['n_papers']} papers)")
        
        if stats["year_range"] > 10:
            limitations.append(f"Wide publication span ({stats['year_range']} years)")
        
        if stats["n_recent"] < 2:
            limitations.append("Lack of recent studies (2020+)")
        
        if not any("RCT" in p.get("title", "") or "randomized" in p.get("title", "").lower() for p in papers):
            limitations.append("No randomized controlled trials identified")
        
        return "; ".join(limitations) if limitations else "No major limitations identified"

    def normalize_pubmed_query(self, user_query: str) -> str:
        """Convert user query to PubMed search query"""
        messages = [
            {
                "role": "system",
                "content": "Convert to PubMed query. Extract biomedical concepts, use AND/OR, remove fluff. Output ONLY the query."
            },
            {"role": "user", "content": user_query}
        ]
        
        response = self._call_groq(messages, max_tokens=64, temperature=0.0)
        
        if response:
            cleaned = self._sanitize_query(response)
            if cleaned:
                return cleaned
        
        return user_query

    def _sanitize_query(self, text: str) -> str:
        text = re.sub(r'[^\w\sAND]', '', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        return text if len(text.split()) >= 2 else ""

    def _call_groq(
        self,
        messages: List[Dict],
        max_tokens: int = 512,
        temperature: float = 0.2
    ) -> str:
        """Call Groq API with retry logic"""
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        for attempt in range(3):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    log_info(f"Groq API success: {len(content)} chars returned")
                    return content
                else:
                    log_warning(f"Groq API error {response.status_code}: {response.text}")
                    
            except Exception as e:
                log_warning(f"Groq API exception (attempt {attempt+1}): {e}")
                time.sleep(2)
        
        return ""