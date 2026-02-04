import os
import json
import pandas as pd
from backend.config.settings import DATA_DIR, ROOT_DIR
from backend.services.intelligence_service import generate_response

# Retrieves financial data from CSV if authorized.
def get_financial_data(user_role: str):
    """Fetches financial data if authorized."""
    if user_role == "Guest":
        return "ERROR: Unauthorized access to financial records."
    
    csv_path = DATA_DIR / "sample_finance.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        return df.to_json(orient="records")
    return "ERROR: Financial data source not found."

# Reads the raw text of a policy file from disk.
def read_policy(policy_name: str) -> str:
    """Reads the full content of a policy file."""
    filename = f"{policy_name}.txt"
    policy_path = DATA_DIR / filename
    if policy_path.exists():
        with open(policy_path, "r") as f:
            return f.read()
    return f"ERROR: Policy '{policy_name}' not found."

# Updates a policy document and triggers re-indexing (Admin only).
def update_policy_document(policy_name: str, new_content: str, user_role: str):
    """Updates a policy document (Admin only)."""
    if user_role != "Admin":
        return "ERROR: Policy modifications require Admin privileges."
    
    filename = f"{policy_name}.txt"
    policy_path = DATA_DIR / filename
    
    try:
        with open(policy_path, "w") as f:
            f.write(new_content)
        
        # Trigger re-indexing
        from backend.services.vector_store_service import create_vector_store
        from langchain_core.documents import Document
        create_vector_store([Document(page_content=new_content, metadata={"source": filename})])
        
        return f"Success: {policy_name} has been updated and re-indexed."
    except Exception as e:
        return f"ERROR: Failed to update policy: {str(e)}"

# Uses AI to identify potential conflicts in proposed policy changes.
def identify_policy_hurdles(new_content: str):
    """Detects contradictions in proposed policy changes."""
    all_policies = ""
    for p in ["sales_policy", "hr_policy"]:
        all_policies += f"\n--- {p} ---\n" + read_policy(p)
    
    prompt = f"""
    Compare the following Proposed Change against our existing Policy Library.
    Proposed Change:
    {new_content}
    
    Library:
    {all_policies}
    
    Identify any contradictions, hurdles, or legal risks. 
    Return a list of hurdle strings. If none, return an empty list [].
    Format: JSON list only.
    """
    response = generate_response(prompt)
    try:
        cleaned = response.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except:
        return ["Potential contradiction detected. Manual review required."]

# Simulates external compliance research using the LLM.
def research_compliance_standards(query: str):
    """Simulates external compliance research."""
    prompt = f"Summarize current industry compliance standards for: {query}"
    return generate_response(prompt)

# Logs interaction events for corporate auditing.
def audit_event(event_type: str, user_id: str, user_role: str, query: str, details: str):
    """Logs interactions for governance auditing."""
    log_path = ROOT_DIR / "mcp_audit.log"
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {event_type} | User: {user_id} ({user_role}) | Query: {query} | Details: {details}\n"
    
    with open(log_path, "a") as f:
        f.write(log_entry)
    return "Logged."

# Validates if a user role is authorized to execute a specific query.
def authorize_request(query: str, user_role: str):
    """Core RBAC and Query Guard."""
    blocked_keywords = ["delete", "wipe", "drop", "update", "change", "revise"]
    if user_role == "Guest" and any(kw in query.lower() for kw in blocked_keywords):
        return {"allowed": False, "reason": "Guest accounts are restricted from initiating policy modifications."}
    
    return {"allowed": True, "reason": "Authorized."}

# Fetches relevant facts from policies and financial records for RAG.
def get_grounded_context(query: str, user_role: str = "Guest"):
    """Retrieves facts from the vector store."""
    from backend.services.vector_store_service import get_retriever
    retriever = get_retriever()
    if not retriever:
        return {"financial_context": [], "policy_context": []}
        
    docs = retriever.invoke(query)
    policy_context = [d.page_content for d in docs]
    
    financial_context = []
    # RBAC: Only Analyst or Admin can see financial data
    if user_role != "Guest" and any(kw in query.lower() for kw in ["sales", "revenue", "cost", "margin"]):
        csv_path = DATA_DIR / "sample_finance.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            financial_context = df.head(5).to_dict(orient="records")
            
    return {
        "financial_context": financial_context,
        "policy_context": policy_context
    }
