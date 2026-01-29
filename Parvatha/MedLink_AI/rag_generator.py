# rag_generator.py
import torch
from typing import List, Dict, Optional
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from langchain_core.prompts import PromptTemplate   
from langchain_core.output_parsers import StrOutputParser   
from langchain_core.language_models.llms import LLM   

from config import LLM_MODEL, GENERATION_MAX_TOKENS
from error_handler import handle_error, log_info, log_warning


class FLANT5LLM(LLM):
    """LangChain-compatible FLAN-T5 wrapper"""
    
    tokenizer: AutoTokenizer = None
    model: AutoModelForSeq2SeqLM = None
    
    def __init__(self):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(LLM_MODEL)
        self.model.eval()
    
    @property
    def _llm_type(self) -> str:
        return "flan-t5"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Generate text from prompt"""
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        )
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=GENERATION_MAX_TOKENS,
                do_sample=False,
                num_beams=4,
                early_stopping=True
            )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    
    @property
    def _identifying_params(self) -> Dict:
        return {"model": LLM_MODEL}


class MedicalRAGGenerator:
    """Enhanced RAG generator with LangChain integration (v1.0+ compatible)"""
    
    def __init__(self):
        try:
            log_info("🧠 Loading FLAN-T5 for answer generation...")
            
            # Initialize LLM
            self.llm = FLANT5LLM()
            
            # Define prompt template
            self.prompt_template = PromptTemplate(
                input_variables=["query", "context"],
                template="""You are a medical research assistant providing evidence-based answers.

Question: {query}

Medical Literature Evidence:
{context}

Instructions:
- Answer the question using ONLY the evidence provided
- Be concise and factual
- If evidence is insufficient, state what is known and what is unclear
- Use medical terminology appropriately

Answer:"""
            )
            
            # Create chain using modern LangChain syntax (v1.0+)
            # Old: LLMChain(llm=llm, prompt=prompt) ❌ DEPRECATED
            # New: prompt | llm | parser ✅ MODERN
            self.chain = self.prompt_template | self.llm | StrOutputParser()
            
            log_info("✅ RAG generator initialized with LangChain v1.0+")
            
        except Exception as e:
            raise RuntimeError(handle_error(e, "MedicalRAGGenerator init"))
    
    def _build_context(self, papers: List[Dict], max_papers: int = 5) -> str:
        """Build context from papers"""
        if not papers:
            return "No medical literature available."
        
        context_blocks = []
        
        for i, p in enumerate(papers[:max_papers], start=1):
            title = p.get("title", "Unknown")
            journal = p.get("journal", "Unknown")
            year = p.get("year", "N/A")
            abstract = p.get("abstract", "")
            
            # Truncate long abstracts
            if len(abstract) > 500:
                abstract = abstract[:500] + "..."
            
            block = (
                f"[Paper {i}]\n"
                f"Title: {title}\n"
                f"Journal: {journal} ({year})\n"
                f"Abstract: {abstract}\n"
            )
            context_blocks.append(block)
        
        return "\n".join(context_blocks)
    
    def generate_answer(
        self, 
        query: str, 
        ranked_papers: List[Dict],
        max_papers: int = 5
    ) -> str:
        """
        Generate answer using modern LangChain with fallback strategies
        
        Strategy:
        1. Try LLM generation with LangChain v1.0+ syntax
        2. Validate output quality
        3. Extractive fallback if needed
        """
        
        try:
            # Build context
            context = self._build_context(ranked_papers, max_papers)
            
            # Generate with LangChain (modern syntax)
            log_info("🤖 Generating answer with LLM...")
            
            # Old: chain.run(query=query, context=context) ❌ DEPRECATED
            # New: chain.invoke({"query": query, "context": context}) ✅ MODERN
            llm_answer = self.chain.invoke({
                "query": query,
                "context": context
            })
            
            # Validate answer
            if self._is_valid_answer(llm_answer):
                log_info("✅ LLM generated valid answer")
                return llm_answer
            else:
                log_warning("⚠️ LLM answer invalid, using fallback")
                return self._extractive_fallback(query, ranked_papers)
            
        except Exception as e:
            log_warning(f"⚠️ Generation error: {e}")
            return self._extractive_fallback(query, ranked_papers)
    
    def _is_valid_answer(self, answer: str) -> bool:
        """Check if LLM answer is valid"""
        if not answer or not isinstance(answer, str):
            return False
        
        answer = answer.strip()
        
        # Too short
        if len(answer) < 50:
            return False
        
        # Starts with evidence markers (likely malformed)
        if answer.startswith(("[Paper", "Title:", "Journal:")):
            return False
        
        # Contains too many brackets (unparsed context)
        if answer.count("[") > 2:
            return False
        
        return True
    
    def _extractive_fallback(self, query: str, papers: List[Dict]) -> str:
        """Extractive summarization fallback"""
        
        if not papers:
            return "No relevant medical literature found for this query."
        
        summaries = []
        
        for i, paper in enumerate(papers[:3], start=1):
            title = paper.get("title", "Unknown")
            abstract = paper.get("abstract", "")
            journal = paper.get("journal", "Unknown")
            year = paper.get("year", "N/A")
            
            if abstract:
                # Extract first 2-3 sentences
                sentences = abstract.split(". ")
                summary = ". ".join(sentences[:2]) + "."
                
                summaries.append(
                    f"**{i}. {title}** ({journal}, {year})\n{summary}"
                )
        
        if summaries:
            intro = "Based on the retrieved medical literature:\n\n"
            return intro + "\n\n".join(summaries)
        
        return (
            "The retrieved medical literature suggests relevance to your query, "
            "but available abstracts do not provide sufficient detail for a comprehensive answer."
        )
    
    def generate_summary(self, papers: List[Dict], max_papers: int = 10) -> str:
        """Generate overall summary of papers"""
        
        if not papers:
            return "No papers to summarize."
        
        summary_parts = []
        summary_parts.append(f"**Summary of {len(papers[:max_papers])} papers:**\n")
        
        for i, paper in enumerate(papers[:max_papers], start=1):
            summary_parts.append(
                f"{i}. {paper.get('title', 'Unknown')} "
                f"({paper.get('journal', 'Unknown')}, {paper.get('year', 'N/A')})"
            )
        
        return "\n".join(summary_parts)