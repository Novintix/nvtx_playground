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
        """
        Build grounded medical context from top-ranked papers
        """
        context_blocks = []

        for i, p in enumerate(papers[:max_papers], start=1):
            block = (
                f"[Paper {i}]\n"
                f"Title: {p['title']}\n"
                f"Journal: {p.get('journal', 'Unknown')}\n"
                f"Year: {p.get('year', 'Unknown')}\n"
                f"Abstract: {p.get('abstract', '')}\n"
            )
            context_blocks.append(block)

        return "\n".join(context_blocks)

    def generate_answer(
        self,
        query: str,
        ranked_papers: List[Dict]
    ) -> str:
        try:
            context = self._build_context(ranked_papers)

            prompt = f"""
You are a medical research assistant.

Answer the question STRICTLY using the evidence below.
If the evidence is insufficient or conflicting, say so clearly.
Do NOT hallucinate or add external knowledge.

Question:
{query}

Evidence:
{context}

Answer (cite paper numbers like [Paper 1], [Paper 2]):
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
                    temperature=0.2,
                    do_sample=False
                )

            answer = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )

            return answer.strip()

        except Exception as e:
            raise RuntimeError(handle_error(e))
