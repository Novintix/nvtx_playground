from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Keywords that indicate a policy-only request
POLICY_ONLY_KEYWORDS = [
    "policy",
    "policies",
    "rule",
    "rules",
    "guideline",
    "guidelines",
    "allowed",
    "approval",
    "limit",
    "limits",
    "compliance"
]


def is_policy_only_query(query: str) -> bool:
    query = query.lower()
    return any(keyword in query for keyword in POLICY_ONLY_KEYWORDS)


def generate_explanation(financial_context, policy_context, query):
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2
    )

    # --------------------------------------------------
    # MODE 1: POLICY-ONLY RESPONSE (NO ANALYSIS)
    # --------------------------------------------------
    if is_policy_only_query(query):
        prompt = f"""
You are an enterprise policy assistant.

User Question:
{query}

Policy Context:
{policy_context}

Instructions:
- ONLY extract and list relevant policy points
- Do NOT analyze financial data
- Do NOT compare trends
- Do NOT calculate metrics
- Do NOT give recommendations
- Be factual, concise, and structured
"""

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    # --------------------------------------------------
    # MODE 2: FULL DECODX REASONING
    # --------------------------------------------------
    prompt = f"""
You are an enterprise financial analysis assistant.

User Question:
{query}

Financial Context:
{financial_context}

Policy Context:
{policy_context}

Instructions:
- Explain what is happening
- Highlight key observations
- Mention any policy impact
- Suggest possible improvements (do NOT make decisions)
- Be concise and business-friendly
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
