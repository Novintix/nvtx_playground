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
    should_answer: bool  # Whether confidence is sufficient to answer


class MedicalRAGGenerator:
    """
    Production-grade Medical RAG Generator
    - Structured output with uncertainty quantification
    - Evidence grading
    - Confidence-based refusal
    """

    def __init__(self):
        log_info("🧠 Initializing Groq API for Medical RAG...")

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY missing")

        self.model = "llama-3.1-8b-instant"
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
        retrieval_confidence: float
    ) -> GeneratedAnswer:
        """
        Generate structured answer with full uncertainty quantification
        """
        
        if not papers:
            return GeneratedAnswer(
                answer_text="No relevant papers found to answer this query.",
                mechanistic_explanation="No mechanistic explanation available.",
                overall_conclusion="Insufficient evidence available.",
                evidence_grade=EvidenceGrade.INSUFFICIENT,
                confidence_score=0.0,
                justification_rationale="No papers were retrieved for this query.",
                key_papers=[],
                uncertainty_flags=["NO_EVIDENCE"],
                limitations="No primary literature identified.",
                should_answer=False
            )
        
        # Calculate evidence statistics
        evidence_stats = self._calculate_evidence_stats(papers)
        
        # Determine evidence grade
        evidence_grade = self._determine_evidence_grade(evidence_stats, retrieval_confidence)
        
        # Prepare evidence text
        evidence_text = self._prepare_evidence_text(papers)
        
        # Generate answer with LLM
        llm_response = self._call_llm_for_answer(query, evidence_text, evidence_stats)
        
        # Calculate final confidence
        final_confidence = self._calculate_final_confidence(
            retrieval_confidence,
            evidence_stats,
            evidence_grade,
            llm_response.get("internal_consistency", 0.5)
        )
        
        # Determine if we should answer
        should_answer = final_confidence >= MIN_ANSWER_CONFIDENCE
        
        # Extract uncertainty flags
        uncertainty_flags = self._identify_uncertainty_flags(
            papers, evidence_stats, evidence_grade, llm_response
        )
        
        return GeneratedAnswer(
            answer_text=llm_response.get("title", "") + "\\n\\n" + llm_response.get("mechanism", ""),
            mechanistic_explanation=llm_response.get("mechanism", ""),
            overall_conclusion=llm_response.get("conclusion", ""),
            evidence_grade=evidence_grade,
            confidence_score=final_confidence,
            justification_rationale=llm_response.get("justification", ""),
            key_papers=[{
                "pmid": p.get("pmid"),
                "title": p.get("title"),
                "year": p.get("year"),
                "support": f"Score: {p.get('final_score', 0):.3f}"
            } for p in papers[:5]],
            uncertainty_flags=uncertainty_flags,
            limitations=self._generate_limitations(papers, evidence_stats),
            should_answer=should_answer
        )

    def _calculate_evidence_stats(self, papers: List[Dict]) -> Dict:
        """Calculate statistics about the evidence base"""
        
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

    def _determine_evidence_grade(
        self,
        stats: Dict,
        retrieval_confidence: float
    ) -> EvidenceGrade:
        """Determine evidence grade based on study quality and consistency"""
        
        # Score components
        quality_score = stats["mean_score"] * 100
        quantity_score = min(stats["n_papers"] * 10, 30)  # Max 30 points for quantity
        recency_score = min(stats["n_recent"] * 5, 20)    # Max 20 for recent papers
        
        # Check for high-impact journals
        impact_bonus = 10 if stats["has_high_impact"] else 0
        
        total_score = quality_score + quantity_score + recency_score + impact_bonus
        
        # Apply retrieval confidence threshold
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
        """Prepare evidence text for LLM context"""
        
        evidence_blocks = []
        for i, p in enumerate(papers[:6], 1):
            abstract = p.get("abstract", "")
            if isinstance(abstract, list):
                abstract = " ".join(str(x) for x in abstract)
            
            title = p.get("title", "Unknown Title")
            year = p.get("year", "Unknown")
            journal = p.get("journal", "Unknown Journal")
            
            evidence_blocks.append(
                f"--- Paper {i} ---\\n"
                f"Title: {title}\\n"
                f"Journal: {journal} ({year})\\n"
                f"PMID: {p.get('pmid', 'N/A')}\\n"
                f"Relevance Score: {p.get('final_score', 0):.3f}\\n"
                f"Abstract: {abstract[:800]}\\n"
            )
        
        return "\\n\\n".join(evidence_blocks)

    def _call_llm_for_answer(
        self,
        query: str,
        evidence_text: str,
        evidence_stats: Dict
    ) -> Dict:
        """Call LLM to generate structured answer"""
        
        system_prompt = """You are a rigorous biomedical research analyst.
Your task is to evaluate scientific evidence and provide structured, evidence-based answers.

CRITICAL RULES:
1. Use ONLY the provided evidence - do not use external knowledge
2. If evidence is insufficient or contradictory, explicitly state this
3. Provide mechanistic explanations when possible
4. Rate your confidence honestly
5. Flag any limitations or uncertainties

Respond in this exact format:

TITLE: <concise scientific title>

MECHANISM: <mechanistic explanation or "Mechanism not clearly established in evidence">

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
        
        response = self._call_groq(messages, temperature=0.3, max_tokens=800)
        
        if not response:
            return {
                "title": "Error in Analysis",
                "mechanism": "Unable to generate analysis.",
                "conclusion": "System error during answer generation.",
                "justification": "LLM API failure.",
                "internal_consistency": 0.0,
                "contradictions": "unknown"
            }
        
        # Parse structured response
        return self._parse_llm_response(response)

    def _parse_llm_response(self, response: str) -> Dict:
        """Parse structured LLM response"""
        
        result = {}
        
        # Extract sections using regex
        title_match = re.search(r'TITLE:\\s*(.+?)(?=\\n|$)', response, re.IGNORECASE)
        mechanism_match = re.search(r'MECHANISM:\\s*(.+?)(?=\\nCONCLUSION|\\nJUSTIFICATION|$)', response, re.DOTALL | re.IGNORECASE)
        conclusion_match = re.search(r'CONCLUSION:\\s*(.+?)(?=\\nJUSTIFICATION|$)', response, re.DOTALL | re.IGNORECASE)
        justification_match = re.search(r'JUSTIFICATION:\\s*(.+?)(?=\\nINTERNAL_CONSISTENCY|$)', response, re.DOTALL | re.IGNORECASE)
        consistency_match = re.search(r'INTERNAL_CONSISTENCY:\\s*([0-9.]+)', response, re.IGNORECASE)
        contradictions_match = re.search(r'CONTRADICTIONS_FOUND:\\s*(.+?)(?=\\n|$)', response, re.IGNORECASE)
        
        result["title"] = title_match.group(1).strip() if title_match else "Untitled Analysis"
        result["mechanism"] = mechanism_match.group(1).strip() if mechanism_match else "Not provided"
        result["conclusion"] = conclusion_match.group(1).strip() if conclusion_match else "Not provided"
        result["justification"] = justification_match.group(1).strip() if justification_match else "Not provided"
        result["internal_consistency"] = float(consistency_match.group(1)) if consistency_match else 0.5
        result["contradictions"] = contradictions_match.group(1).strip() if contradictions_match else "unknown"
        
        return result

    def _calculate_final_confidence(
        self,
        retrieval_confidence: float,
        evidence_stats: Dict,
        evidence_grade: EvidenceGrade,
        internal_consistency: float
    ) -> float:
        """Calculate final calibrated confidence score"""
        
        # Base confidence from retrieval
        base_conf = retrieval_confidence
        
        # Evidence quality factor
        quality_factor = evidence_stats["mean_score"]
        
        # Quantity factor (diminishing returns after 5 papers)
        quantity_factor = min(evidence_stats["n_papers"] / 5, 1.0)
        
        # Grade factor
        grade_factors = {
            EvidenceGrade.A: 1.0,
            EvidenceGrade.B: 0.85,
            EvidenceGrade.C: 0.70,
            EvidenceGrade.D: 0.55,
            EvidenceGrade.INSUFFICIENT: 0.30
        }
        grade_factor = grade_factors.get(evidence_grade, 0.5)
        
        # Consistency factor
        consistency_factor = internal_consistency
        
        # Weighted combination
        final_confidence = (
            0.30 * base_conf +
            0.25 * quality_factor +
            0.15 * quantity_factor +
            0.15 * grade_factor +
            0.15 * consistency_factor
        )
        
        return round(min(final_confidence, 1.0), 3)

    def _identify_uncertainty_flags(
        self,
        papers: List[Dict],
        stats: Dict,
        grade: EvidenceGrade,
        llm_response: Dict
    ) -> List[str]:
        """Identify specific uncertainty factors"""
        
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
            limitations.append(f"Wide publication span ({stats['year_range']} years) may affect comparability")
        
        if stats["n_recent"] < 2:
            limitations.append("Lack of recent studies (2020+)")
        
        if not any("RCT" in p.get("title", "") or "randomized" in p.get("title", "").lower() for p in papers):
            limitations.append("No randomized controlled trials identified")
        
        return "; ".join(limitations) if limitations else "No major limitations identified"

    # =================================================
    # LEGACY METHODS (Backward Compatibility)
    # =================================================
    
    def generate_answer(self, query: str, papers: List[Dict]) -> str:
        """Legacy method - returns simple string"""
        result = self.generate_structured_answer(query, papers, 0.7)
        
        if not result.should_answer:
            return f"⚠️ INSUFFICIENT CONFIDENCE ({result.confidence_score:.2f})\\n\\n{result.overall_conclusion}\\n\\nLimitations: {result.limitations}"
        
        output = f"""{result.answer_text}

Evidence Grade: {result.evidence_grade.value}
Confidence Score: {result.confidence_score:.2f}

Justification Rationale:
{result.justification_rationale}

Key Supporting Papers:"""
        
        for i, paper in enumerate(result.key_papers, 1):
            output += f"\\n{i}. **{paper['title']}** — {paper['support']}"
        
        if result.uncertainty_flags:
            output += f"\\n\\n⚠️ Uncertainty Flags: {', '.join(result.uncertainty_flags)}"
        
        output += f"\\n\\n📊 Limitations: {result.limitations}"
        
        return output

    def normalize_pubmed_query(self, user_query: str) -> str:
        """Convert user query to PubMed search query"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Convert to PubMed query. Extract biomedical concepts, use AND/OR, remove fluff. "
                    "Output ONLY the query."
                )
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
        text = re.sub(r'[^\\w\\sAND]', '', text.lower())
        text = re.sub(r'\\s+', ' ', text).strip()
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
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    log_warning(f"Groq API error {response.status_code}: {response.text}")
                    
            except Exception as e:
                log_warning(f"Groq API exception (attempt {attempt+1}): {e}")
                time.sleep(2)
        
        return ""
 
