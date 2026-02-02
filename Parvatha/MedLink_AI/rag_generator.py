# rag_generator.py
import os
import time
import re
import requests
from typing import List, Dict
from dotenv import load_dotenv

from error_handler import log_info, log_warning

load_dotenv()


class MedicalRAGGenerator:
    """
    Groq API + LLaMA 3.1
    Production-grade Medical RAG Generator
    - Dynamic PubMed query normalization
    - Mechanistic biomedical synthesis
    - NO chain-of-thought leakage
    """

    def __init__(self):
        log_info("🧠 Initializing Groq API for Medical RAG...")

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY missing")

        # ✅ Supported Groq model
        self.model = "llama-3.1-8b-instant"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        log_info(f"✅ Groq ready with model: {self.model}")

    # =================================================
    # SAFE ABSTRACT HANDLING
    # =================================================
    def _safe_abstract(self, abstract) -> str:
        if isinstance(abstract, list):
            return " ".join(str(x) for x in abstract)
        if isinstance(abstract, str):
            return abstract
        return ""

    # =================================================
    # PUBMED QUERY NORMALIZATION (DYNAMIC)
    # =================================================
    def normalize_pubmed_query(self, user_query: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a biomedical literature search expert.\n"
                    "Convert the user query into a PubMed search query.\n\n"
                    "Rules:\n"
                    "- Extract core biomedical concepts only\n"
                    "- Use AND between concepts\n"
                    "- Remove conversational words\n"
                    "- No explanations\n"
                    "- Output ONLY the query"
                )
            },
            {
                "role": "user",
                "content": user_query
            }
        ]

        response = self._call_groq(messages, max_tokens=64, temperature=0.0)

        if response:
            cleaned = self._sanitize_query(response)
            if cleaned:
                log_info(f"✅ PubMed query (Groq): {cleaned}")
                return cleaned

        log_warning("⚠️ PubMed normalization fallback → using original query")
        return user_query

    def _sanitize_query(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\sAND]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text if len(text.split()) >= 2 else ""

    # =================================================
    # 🔥 MECHANISTIC ANSWER GENERATION
    # =================================================
    def generate_answer(self, query: str, papers: List[Dict]) -> str:
        if not papers:
            return "No relevant biomedical literature found."

        # ---- Prepare evidence ----
        evidence_blocks = []

        for i, p in enumerate(papers[:6], 1):
            abstract = self._safe_abstract(p.get("abstract", ""))
            title = p.get("title", "Unknown Title")
            if abstract:
                evidence_blocks.append(
                    f"[Paper {i}] {title}\n{abstract[:800]}"
                )

        evidence_text = "\n\n".join(evidence_blocks)

        # ---- STRONG STRUCTURED PROMPT ----
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a biomedical researcher evaluating scientific evidence.\n\n"
                    "STRICT RULES:\n"
                    "- Use ONLY the provided evidence\n"
                    "- Do NOT hallucinate\n"
                    "- Do NOT summarize papers individually\n"
                    "- Reason mechanistically\n"
                    "- Output MUST follow the exact format requested"
                )
            },
            {
                "role": "user",
                "content": f"""
Answer the question using ONLY the evidence below.

OUTPUT FORMAT (MANDATORY):

Title:
<concise scientific title>
<br>

Mechanistic Explanation:
<clear cause–effect biological explanation>
<br>

Overall Conclusion:
<2–3 sentence synthesis grounded in evidence>
<br>

Evidence Justification Score:
<number between 0 and 100>
<br>

Justification Rationale:
<why the score was assigned based on evidence strength>
<br>

Key Supporting Papers:
1. **<Paper title>** — <how it supports the mechanism>
<br>

2. **<Paper title>** — <how it supports the mechanism>
<br>

Evidence:
{evidence_text}

Question:
{query}
"""
            }
        ]

        answer = self._call_groq(messages, temperature=0.2)

        return (
            answer.strip()
            if answer
            else "Unable to generate a reliable answer from the available evidence."
        )

    # =================================================
    # GROQ API CALL
    # =================================================
    def _call_groq(self, messages, max_tokens=512, temperature=0.2) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        for _ in range(3):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]

                else:
                    log_warning(
                        f"Groq API error {response.status_code}: {response.text}"
                    )

            except Exception as e:
                log_warning(f"Groq API exception: {e}")
                time.sleep(2)

        return ""
