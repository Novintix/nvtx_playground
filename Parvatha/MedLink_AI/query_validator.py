# query_validator.py 
"""
Intelligent Query Validator using LLM for domain classification
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import os
import json

import requests
from error_handler import log_info, log_warning


class ValidationStatus(Enum):
    VALID = "valid"
    INVALID_DOMAIN = "invalid_domain"
    INVALID_LOGIC = "invalid_logic"
    INVALID_SEMANTIC = "invalid_semantic"


@dataclass
class ValidationResult:
    is_valid: bool
    status: ValidationStatus
    relevance_score: float
    extracted_entities: List[Dict]
    coherence_score: float
    rejection_reason: str
    suggestion: str


class QueryValidator:
    """
    LLM-Based Domain Validator
    Uses Groq LLM for intelligent domain classification
    with few-shot prompting
    """
    
    # Only minimal patterns for obvious garbage (not domain-specific)
    GARBAGE_PATTERNS = [
        r'(.)\1{4,}',  # Repeated characters (aaaaa)
        r'[^a-zA-Z0-9\s\-\,\.\?\!\(\)\[\]\{\}\:\;]{3,}',  # Excessive special chars
    ]
    
    # Logical impossibilities (medical facts, not keywords)
    IMPOSSIBLE_FACTS = [
        (r'obesity\s+(?:rate|percentage|%)\s*(?:of\s*)?(?:10[5-9]|[2-9]\d{2,})%', 
         "Obesity rate cannot exceed 100%"),
        (r'survival\s+(?:rate|percentage|%)\s*(?:of\s*)?(?:10[5-9]|[2-9]\d{2,})%', 
         "Survival rate cannot exceed 100%"),
        (r'(?:age|weight|height|bmi|dose)\s*(?:of\s*)?-\d+', 
         "Negative values for physical measurements are impossible"),
    ]
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"
        
        if not self.groq_api_key:
            log_warning("⚠️ GROQ_API_KEY not found. Validation will be limited.")
        
        log_info("🧠 LLM-Based Query Validator initialized")
    
    def validate(self, query: str) -> ValidationResult:
        """Main validation pipeline using LLM"""
        
        # Step 1: Basic sanity checks
        if not query or not isinstance(query, str) or len(query.strip()) < 5:
            return self._create_rejection(
                ValidationStatus.INVALID_SEMANTIC,
                "Query too short or empty",
                "Please provide a detailed medical research question."
            )
        
        query = query.strip()
        
        # Step 2: Check for garbage/ spam (minimal hardcoding)
        if self._is_garbage(query):
            return self._create_rejection(
                ValidationStatus.INVALID_SEMANTIC,
                "Query appears to be random text or spam",
                "Please provide a coherent question."
            )
        
        # Step 3: Check logical impossibilities (medical facts only)
        logic_issue = self._check_logical_impossibility(query)
        if logic_issue:
            return self._create_rejection(
                ValidationStatus.INVALID_LOGIC,
                logic_issue,
                "Please correct the impossible values in your query."
            )
        
        # Step 4: LLM-based domain classification (THE SMART PART)
        llm_result = self._llm_validate(query)
        
        if not llm_result:
            # LLM failed, fail-open (allow query but log warning)
            log_warning("LLM validation failed, allowing query to proceed")
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.VALID,
                relevance_score=0.5,
                extracted_entities=[],
                coherence_score=0.5,
                rejection_reason="",
                suggestion=""
            )
        
        # Step 5: Parse LLM result
        is_valid = llm_result.get("is_biomedical", False)
        score = llm_result.get("confidence", 0.0)
        reason = llm_result.get("reasoning", "")
        entities = llm_result.get("entities_found", [])
        suggestion = llm_result.get("suggestion", "")
        
        from config import MIN_DOMAIN_RELEVANCE
        
        if not is_valid or score < MIN_DOMAIN_RELEVANCE:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID_DOMAIN,
                relevance_score=score,
                extracted_entities=[{"text": e, "label": "ENTITY"} for e in entities],
                coherence_score=1.0,  # No logic issues
                rejection_reason=f"Not a biomedical research query. {reason}",
                suggestion=suggestion
            )
        
        return ValidationResult(
            is_valid=True,
            status=ValidationStatus.VALID,
            relevance_score=score,
            extracted_entities=[{"text": e, "label": "ENTITY"} for e in entities],
            coherence_score=1.0,
            rejection_reason="",
            suggestion=""
        )
    
    def _is_garbage(self, query: str) -> bool:
        """Check for obvious spam/gibberish"""
        for pattern in self.GARBAGE_PATTERNS:
            if re.search(pattern, query):
                return True
        
        # Check for excessive repetition
        words = query.lower().split()
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # >70% repeated words
                return True
        
        return False
    
    def _check_logical_impossibility(self, query: str) -> Optional[str]:
        """Check for physically impossible medical facts"""
        query_lower = query.lower()
        for pattern, message in self.IMPOSSIBLE_FACTS:
            if re.search(pattern, query_lower):
                return message
        return None
    
    def _create_rejection(self, status: ValidationStatus, reason: str, suggestion: str) -> ValidationResult:
        """Helper to create rejection result"""
        return ValidationResult(
            is_valid=False,
            status=status,
            relevance_score=0.0,
            extracted_entities=[],
            coherence_score=0.0,
            rejection_reason=reason,
            suggestion=suggestion
        )
    
    def _llm_validate(self, query: str) -> Optional[Dict]:
        """
        Use LLM for intelligent domain validation
        Returns structured classification
        """
        if not self.groq_api_key:
            return None
        
        system_prompt = """You are a biomedical research query classifier for MedGuard Evidence, a medical literature search system.

Your task: Determine if a query is appropriate for PubMed biomedical research database.

CLASSIFICATION RULES:
1. ACCEPT (is_biomedical: true): 
   - Medical conditions, diseases, treatments
   - Biological mechanisms, molecular pathways
   - Clinical research, epidemiology, diagnostics
   - Drug effects, pharmacology, therapeutics
   - Physiology, anatomy, genetics
   - Public health, healthcare outcomes

2. REJECT (is_biomedical: false):
   - Historical facts (Taj Mahal, ancient history)
   - Geography, travel, landmarks
   - Sports, entertainment, celebrities
   - Technology, gadgets, software (unless medical devices)
   - General trivia, non-medical facts
   - Mixed domains without medical relevance

OUTPUT FORMAT (JSON):
{
    "is_biomedical": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "entities_found": ["list", "of", "medical", "entities"],
    "suggestion": "Alternative query if rejected"
}

EXAMPLES:

Query: "What is the relationship between obesity and cardiovascular disease?"
Output: {
    "is_biomedical": true,
    "confidence": 0.95,
    "reasoning": "Direct medical research question about disease mechanisms",
    "entities_found": ["obesity", "cardiovascular disease"],
    "suggestion": ""
}

Query: "When was Taj Mahal built?"
Output: {
    "is_biomedical": false,
    "confidence": 0.98,
    "reasoning": "Historical question about architecture, no medical content",
    "entities_found": [],
    "suggestion": "What is the relationship between air pollution and respiratory disease?"
}

Query: "Who won the FIFA World Cup 2022?"
Output: {
    "is_biomedical": false,
    "confidence": 0.99,
    "reasoning": "Sports question, no medical relevance",
    "entities_found": [],
    "suggestion": "How does competitive sports affect cardiovascular health?"
}

Query: "How does insulin resistance develop in type 2 diabetes?"
Output: {
    "is_biomedical": true,
    "confidence": 0.96,
    "reasoning": "Clinical mechanism question about disease pathophysiology",
    "entities_found": ["insulin resistance", "type 2 diabetes"],
    "suggestion": ""
}

Query: "Taj Mahal obesity rate 105"
Output: {
    "is_biomedical": false,
    "confidence": 0.92,
    "reasoning": "Mixes historical landmark with impossible medical statistic (obesity rate >100%)",
    "entities_found": [],
    "suggestion": "What is the prevalence of obesity in Indian population?"
}"""
        
        try:
            response = requests.post(
                self.groq_url,
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f'Query: "{query}"\n\nOutput only the JSON:'}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300
                },
                timeout=15
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                
                # Extract JSON
                try:
                    # Try to parse entire content as JSON
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown
                    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(1))
                    else:
                        # Try to find JSON object
                        json_match = re.search(r'({.*?})', content, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group(1))
                        else:
                            return None
                
                log_info(f"LLM validation: biomedical={result.get('is_biomedical')}, confidence={result.get('confidence')}")
                return result
            
            else:
                log_warning(f"LLM API error: {response.status_code}")
                return None
                
        except Exception as e:
            log_warning(f"LLM validation error: {e}")
            return None