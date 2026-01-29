# rag_generator.py
import torch
from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from error_handler import handle_error


class MedicalRAGGenerator:
    def __init__(self):
        try:
            print("🧠 Loading lightweight open-source LLM (FLAN-T5-Large)...")

            self.tokenizer = AutoTokenizer.from_pretrained(
                "google/flan-t5-large"
            )

            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                "google/flan-t5-large"
            )

            self.model.to("cpu")
            self.model.eval()

        except Exception as e:
            raise RuntimeError(handle_error(e))

    def _build_context(self, papers: List[Dict], max_papers: int = 5) -> str:
        context_blocks = []

        for i, p in enumerate(papers[:max_papers], start=1):
            block = (
                f"[Paper {i}]\n"
                f"Title: {p.get('title', '')}\n"
                f"Journal: {p.get('journal', 'Unknown')}\n"
                f"Year: {p.get('year', 'Unknown')}\n"
                f"Abstract: {p.get('abstract', '')}\n"
            )
            context_blocks.append(block)

        return "\n".join(context_blocks)

    def generate_answer(self, query: str, ranked_papers: List[Dict]) -> str:
        """
        Hybrid answer generation:
        1. Try LLM
        2. Validate output
        3. Extractive fallback
        """

        # -------- Step 1: Try LLM --------
        try:
            context = self._build_context(ranked_papers)

            prompt = f"""
You are a medical research assistant.

Answer the question strictly using the evidence below.
If the evidence is insufficient, still provide a brief literature-based summary.

Question:
{query}

Evidence:
{context}

Answer:
"""

            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            )

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False
                )

            llm_answer = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            ).strip()

        except Exception:
            llm_answer = ""

        # -------- Step 2: Validate LLM output --------
        def is_bad_answer(text: str) -> bool:
            if not text:
                return True
            if len(text) < 50:
                return True
            if text.strip().startswith("[Paper"):
                return True
            return False

        if not is_bad_answer(llm_answer):
            return llm_answer

        # -------- Step 3: Extractive fallback --------
        summaries = []
        for p in ranked_papers[:3]:
            abstract = p.get("abstract", "")
            if isinstance(abstract, str) and abstract.strip():
                sentences = abstract.split(". ")
                summaries.append(". ".join(sentences[:2]) + ".")

        if summaries:
            return (
                "Based on the retrieved medical literature, the following findings are reported:\n\n"
                + "\n\n".join(summaries)
            )

        # -------- Absolute fallback --------
        return (
            "The retrieved medical literature suggests a relationship between the queried factors, "
            "but available abstracts do not provide sufficient detail for a comprehensive summary."
        )
