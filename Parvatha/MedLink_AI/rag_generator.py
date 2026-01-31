# rag_generator.py
import torch
from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForCausalLM

from config import GENERATION_MAX_TOKENS
from error_handler import handle_error, log_info, log_warning


class MedicalRAGGenerator:
    """Enhanced RAG generator with BioMistral-7B for medical synthesis"""
    
    def __init__(self):
        try:
            log_info("🧠 Loading BioMistral-7B for medical answer generation...")
            
            model_name = "BioMistral/BioMistral-7B"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,  # Use FP16 for efficiency
                device_map="auto",  # Auto device placement
                low_cpu_mem_usage=True
            )
            
            self.model.eval()
            
            log_info("✅ BioMistral-7B loaded successfully")
            
        except Exception as e:
            log_warning("⚠️ BioMistral-7B failed to load, trying fallback...")
            try:
                # Fallback to Mistral-7B-Instruct
                model_name = "mistralai/Mistral-7B-Instruct-v0.2"
                log_info("🔄 Loading Mistral-7B-Instruct as fallback...")
                
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    low_cpu_mem_usage=True
                )
                self.model.eval()
                
                log_info("✅ Mistral-7B-Instruct loaded successfully")
                
            except Exception as e2:
                raise RuntimeError(handle_error(e2, "MedicalRAGGenerator init"))
    
    def _build_context(self, papers: List[Dict], max_papers: int = 5) -> str:
        """Build concise context from papers"""
        if not papers:
            return "No medical literature available."
        
        context_blocks = []
        
        for i, paper in enumerate(papers[:max_papers], start=1):
            title = paper.get("title", "Unknown")
            abstract = paper.get("abstract", "")
            
            # Get first 3 sentences for conciseness
            if abstract:
                sentences = abstract.split(". ")
                summary = ". ".join(sentences[:3])
                if not summary.endswith("."):
                    summary += "."
            else:
                summary = "No abstract available."
            
            block = f"[{i}] {title}\n{summary}"
            context_blocks.append(block)
        
        return "\n\n".join(context_blocks)
    
    def _create_synthesis_prompt(self, query: str, context: str) -> str:
        """Create prompt optimized for medical synthesis"""
        
        prompt = f"""<s>[INST] You are a medical research expert synthesizing scientific literature.

Question: {query}

Medical Literature:
{context}

Instructions:
1. SYNTHESIZE the information - do not just copy abstracts
2. Explain HOW and WHY mechanisms work
3. Connect findings across papers
4. Be specific about pathways, molecules, and mechanisms
5. If papers disagree, explain the differences
6. Keep answer concise but comprehensive
7. Use medical terminology appropriately

Provide a clear, synthesized answer: [/INST]

"""
        return prompt
    
    def generate_answer(
        self, 
        query: str, 
        ranked_papers: List[Dict],
        max_papers: int = 5,
        max_length: int = 512
    ) -> str:
        """
        Generate synthesized answer using BioMistral
        
        Args:
            query: User's medical question
            ranked_papers: Re-ranked papers
            max_papers: Max papers to use in context
            max_length: Max tokens in answer
            
        Returns:
            Synthesized answer
        """
        
        try:
            if not ranked_papers:
                return "No relevant medical literature found for this query."
            
            # Build context
            context = self._build_context(ranked_papers, max_papers)
            
            # Create prompt
            prompt = self._create_synthesis_prompt(query, context)
            
            log_info(f"🤖 Generating synthesized answer (prompt: {len(prompt)} chars)...")
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            ).to(self.model.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract answer (after [/INST])
            if "[/INST]" in full_output:
                answer = full_output.split("[/INST]")[-1].strip()
            else:
                answer = full_output.strip()
            
            # Validate
            if self._is_valid_answer(answer, query):
                log_info(f"✅ Generated valid synthesized answer ({len(answer)} chars)")
                return answer
            else:
                log_warning("⚠️ Generated answer failed validation, using smart fallback")
                return self._smart_extractive_fallback(query, ranked_papers)
            
        except Exception as e:
            log_warning(f"⚠️ Generation error: {e}")
            return self._smart_extractive_fallback(query, ranked_papers)
    
    def _is_valid_answer(self, answer: str, query: str) -> bool:
        """
        Validate that answer is actually answering the query
        """
        if not answer or not isinstance(answer, str):
            return False
        
        answer_lower = answer.lower()
        
        # Too short
        if len(answer) < 100:
            return False
        
        # Starts with citation markers (not synthesized)
        if answer.startswith(("[1]", "[2]", "[Paper", "Title:", "Abstract:")):
            return False
        
        # Check if answer addresses query terms
        query_terms = query.lower().split()
        important_terms = [t for t in query_terms if len(t) > 4]  # Skip short words
        
        if important_terms:
            # At least 50% of important terms should be in answer
            matches = sum(1 for term in important_terms if term in answer_lower)
            if matches / len(important_terms) < 0.5:
                return False
        
        # Check for synthesis indicators
        synthesis_indicators = [
            "mechanism", "pathway", "through", "by activating",
            "leads to", "results in", "contributes to", "associated with",
            "evidence shows", "studies indicate", "research suggests"
        ]
        
        has_synthesis = any(indicator in answer_lower for indicator in synthesis_indicators)
        
        return has_synthesis
    
    def _smart_extractive_fallback(self, query: str, papers: List[Dict]) -> str:
        """
        Smart extractive fallback that tries to answer HOW/WHY
        """
        
        if not papers:
            return "No relevant medical literature found for this query."
        
        # Identify query type
        query_lower = query.lower()
        is_how_query = any(word in query_lower for word in ["how", "mechanism", "pathway"])
        is_why_query = "why" in query_lower
        is_what_query = "what" in query_lower
        
        # Extract relevant sentences
        relevant_sentences = []
        
        for paper in papers[:3]:
            abstract = paper.get("abstract", "")
            if not abstract:
                continue
            
            sentences = abstract.split(". ")
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                
                # Look for mechanism/pathway sentences
                if is_how_query or is_why_query:
                    if any(word in sentence_lower for word in [
                        "mechanism", "pathway", "through", "by activating",
                        "leads to", "results in", "contributes to", "via",
                        "mediated by", "regulated by"
                    ]):
                        relevant_sentences.append(sentence.strip() + ".")
                
                # Look for definition sentences
                elif is_what_query:
                    if any(word in sentence_lower for word in [
                        "defined as", "refers to", "characterized by", "is a"
                    ]):
                        relevant_sentences.append(sentence.strip() + ".")
                
                # Generic relevance
                else:
                    query_terms = [t for t in query_lower.split() if len(t) > 4]
                    if sum(1 for term in query_terms if term in sentence_lower) >= 2:
                        relevant_sentences.append(sentence.strip() + ".")
        
        if relevant_sentences:
            # Build answer from relevant sentences
            answer = "Based on the medical literature:\n\n"
            answer += " ".join(relevant_sentences[:5])  # Max 5 sentences
            return answer
        
        # Absolute fallback
        return self._basic_extractive_fallback(papers)
    
    def _basic_extractive_fallback(self, papers: List[Dict]) -> str:
        """Basic extractive fallback (last resort)"""
        
        summaries = []
        
        for i, paper in enumerate(papers[:3], start=1):
            title = paper.get("title", "Unknown")
            abstract = paper.get("abstract", "")
            journal = paper.get("journal", "Unknown")
            year = paper.get("year", "N/A")
            
            if abstract:
                sentences = abstract.split(". ")
                summary = ". ".join(sentences[:2])
                if not summary.endswith("."):
                    summary += "."
                
                summaries.append(
                    f"**Study {i}** ({journal}, {year}): {summary}"
                )
        
        if summaries:
            intro = "Based on retrieved medical literature:\n\n"
            return intro + "\n\n".join(summaries)
        
        return "Insufficient information in retrieved abstracts to answer this query comprehensively."