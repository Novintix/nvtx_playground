import os
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from tools import retrieve_policy

# Load environment variables from .env file
load_dotenv()

# ---------------- LLM ----------------
# Allow overriding the model without code changes (e.g., if Groq deprecates a model).
# Groq currently supports newer Llama 3.1 models; keep a safe default.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
llm = ChatGroq(model=GROQ_MODEL, temperature=0)

# ---------------- State ----------------
class AgentState(TypedDict):
    question: str
    need_retrieval: str
    decision_reason: str
    context: str
    answer: str
    vectorstore: object

# ---------------- Nodes ----------------
def decide_retrieval(state: AgentState):
    prompt = f"""
You are a healthcare insurance assistant.

Question:
{state['question']}

Decide if answering this requires insurance policy documents.

Respond exactly in this format:
Decision: YES or NO
Reason: one short sentence
"""
    response = llm.invoke(prompt).content.strip()

    decision = response.split("Decision:")[1].split("\n")[0].strip()
    reason = response.split("Reason:")[1].strip()

    return {
        "need_retrieval": decision,
        "decision_reason": reason
    }

def retrieve_node(state: AgentState):
    context = retrieve_policy(
        state["question"],
        state["vectorstore"]
    )
    return {"context": context}

def answer_with_context(state: AgentState):
    prompt = f"""
Use the following insurance policy clauses to answer the question.

Policy Clauses:
{state['context']}

Question: {state['question']}

Answer in 1–2 short, clear sentences. Be concise and to the point.
"""
    answer = llm.invoke(prompt).content
    return {"answer": answer}

def direct_answer(state: AgentState):
    prompt = f"""
You are a healthcare insurance assistant.

Question: {state['question']}

Answer in 1–2 short, clear sentences. Be concise and to the point.
"""
    answer = llm.invoke(prompt).content
    return {"answer": answer}

# ---------------- Graph ----------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("decide", decide_retrieval)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("answer_context", answer_with_context)
    graph.add_node("direct", direct_answer)

    graph.set_entry_point("decide")

    graph.add_conditional_edges(
        "decide",
        lambda state: state["need_retrieval"],
        {
            "YES": "retrieve",
            "NO": "direct"
        }
    )

    graph.add_edge("retrieve", "answer_context")
    graph.add_edge("answer_context", END)
    graph.add_edge("direct", END)

    return graph.compile()
