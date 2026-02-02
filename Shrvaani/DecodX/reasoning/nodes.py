from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

def llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2
    )

def analyze_performance(state):
    prompt = f"""
Analyze current financial performance:

{state['financial_context']}
"""
    state["analysis"] = llm().invoke(
        [HumanMessage(content=prompt)]
    ).content
    return state


def compare_history(state):
    prompt = f"""
Compare current performance with historical context:

{state['financial_context']}
"""
    state["comparison"] = llm().invoke(
        [HumanMessage(content=prompt)]
    ).content
    return state


def validate_policy(state):
    prompt = f"""
Identify policy constraints or impact:

{state['policy_context']}
"""
    state["policy_check"] = llm().invoke(
        [HumanMessage(content=prompt)]
    ).content
    return state


def recommend_actions(state):
    prompt = f"""
Based on:
Analysis: {state['analysis']}
Comparison: {state['comparison']}
Policy: {state['policy_check']}

Suggest improvement opportunities.
Do NOT make decisions.
"""
    state["recommendations"] = llm().invoke(
        [HumanMessage(content=prompt)]
    ).content
    return state


def explain(state):
    state["final_answer"] = f"""
### 🔍 Analysis
{state['analysis']}

### 📊 Historical Comparison
{state['comparison']}

### 📜 Policy Impact
{state['policy_check']}

### 💡 Recommendations
{state['recommendations']}
"""
    return state


def policy_only_response(state):
    prompt = f"""
You are an enterprise policy assistant.

User Question:
{state['query']}

Policy Context:
{state['policy_context']}

Instructions:
- Answer the user's question directly (e.g., "Yes, you can", "No, it is not allowed").
- Cite the specific policy section that supports your answer.
- If it is a "conditional" yes (e.g., "Yes, but requires approval"), state the condition clearly.
- Be concise.
"""
    response = llm().invoke([HumanMessage(content=prompt)])
    state["final_answer"] = response.content
    return state
