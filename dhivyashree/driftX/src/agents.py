from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

# --- Data Models ---

class KeyStatement(BaseModel):
    speaker: str = Field(description="Name of the speaker")
    text: str = Field(description="The statement content")

class DiscussionAnalysis(BaseModel):
    summary: str = Field(description="Summary of the discussion focus")
    primary_focus: List[str] = Field(description="List of primary focus areas")
    deprioritized: List[str] = Field(description="List of deprioritized concerns")
    key_statements: List[KeyStatement] = Field(description="List of key decision statements")

class RequirementIntent(BaseModel):
    goals: List[str] = Field(description="List of extracted goals")
    constraints: List[str] = Field(description="List of extracted constraints")
    priority_order: List[str] = Field(description="Extracted priority order (e.g., 'security > speed')")

class DriftAnalysis(BaseModel):
    drift_detected: bool = Field(description="Whether requirement drift was detected")
    drift_type: List[str] = Field(description="list of drift types detected (e.g., 'Constraint Drift')")
    explanation: str = Field(description="Natural language explanation of the drift")
    evidence: List[str] = Field(description="Evidence snippets from the discussion")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")

# --- Agents ---

class DiscussionFocusAgent:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=DiscussionAnalysis)

    def analyze(self, chat_transcript: str) -> DiscussionAnalysis:
        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert project manager analyzing a group discussion.
            Your task is to summarize the discussion and extract the primary focus, 
            deprioritized items, and key decision statements.

            Chat Transcript:
            {chat_transcript}

            {format_instructions}
            """
        )
        chain = prompt | self.llm | self.parser
        return chain.invoke({
            "chat_transcript": chat_transcript,
            "format_instructions": self.parser.get_format_instructions()
        })

class RequirementIntentAgent:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=RequirementIntent)

    def analyze(self, requirement_text: str) -> RequirementIntent:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a requirements engineer. extracting the original intent, 
            constraints, and priorities from a requirement document.

            Requirement Document:
            {requirement_text}

            {format_instructions}
            """
        )
        chain = prompt | self.llm | self.parser
        return chain.invoke({
            "requirement_text": requirement_text,
            "format_instructions": self.parser.get_format_instructions()
        })

class DriftAnalyzerAgent:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=DriftAnalysis)

    def analyze(self, discussion_analysis: DiscussionAnalysis, requirement_intent: RequirementIntent, additional_context: str = "") -> DriftAnalysis:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a QA Auditor. detection requirement drift.
            Compare the discussion focus with the original requirement intent.
            
            Determine if the team has deviated from the original goals or constraints.
            Provide evidence and an explanation.

            Discussion Analysis:
            {discussion_analysis}

            Requirement Intent:
            {requirement_intent}

            Additional Requirement Details (Retrieved via RAG):
            {additional_context}

            {format_instructions}
            """
        )
        chain = prompt | self.llm | self.parser
        return chain.invoke({
            "discussion_analysis": discussion_analysis.model_dump_json(),
            "requirement_intent": requirement_intent.model_dump_json(),
            "additional_context": additional_context,
            "format_instructions": self.parser.get_format_instructions()
        })
class CodeDriftAnalysis(BaseModel):
    compliance_score: float = Field(description="0.0 to 1.0 (1.0 = fully compliant)")
    missing_features: List[str] = Field(description="Features in requirements but missing in code")
    unexpected_features: List[str] = Field(description="Features in code but not in requirements")
    evidence_files: List[str] = Field(description="Files checked")
    verdict: str = Field(description="Short summary verdict")

# ... (Previous agents)

class CodeComplianceAgent:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=CodeDriftAnalysis)

    def analyze(self, requirement_intent: RequirementIntent, code_summary: str) -> CodeDriftAnalysis:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a Senior Code Auditor. 
            Verify if the provided code structure and content matches the requirement intent.

            Requirement Intent:
            {requirement_intent}

            Codebase Summary (Files & Key Content):
            {code_summary}

            Identify missing features, unexpected additions, and give a compliance score.
            {format_instructions}
            """
        )
        chain = prompt | self.llm | self.parser
        return chain.invoke({
            "requirement_intent": requirement_intent.model_dump_json(),
            "code_summary": code_summary,
            "format_instructions": self.parser.get_format_instructions()
        })
