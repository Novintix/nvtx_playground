import sys
import os
from datetime import datetime
from pathlib import Path
import time
from dotenv import load_dotenv

# Add root directory to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from ingestion.ingest import load_financial_data, load_policy_data
from vector_store.store import create_vector_store, retrieve_context
from reasoning.graph import build_graph
from MCP.guard import authorize, audit_log

# Load env
load_dotenv()

def run_scheduler():
    print("⏰ Starting Logic for Scheduled Triggers...")
    
    # 1. Initialize Agent (Background)
    print("🔹 Initializing Agent Context...")
    finance_docs = load_financial_data("data/sample_finance.csv")
    policy_docs = load_policy_data("data/sales_policy.txt")
    vectordb = create_vector_store(finance_docs + policy_docs)
    agent = build_graph()
    
    # 2. Define Triggered Queries
    triggers = [
        {
            "trigger_name": "Monthly Financial Review",
            "query": "Perform a monthly financial review. Compare this year's sales to last year's and check for policy alignment."
        }
    ]

    for trigger in triggers:
        query = trigger["query"]
        print(f"\n🚀 Trigger Fired: {trigger['trigger_name']}")
        print(f"❓ Query: {query}")

        # 3. Governance Check (System/Admin Context)
        # Scheduled tasks run as "System" or "Admin" typically
        if not authorize(query, user_role="Admin"):
            print("❌ Blocked by Governance.")
            continue
        
        audit_log(query, user="SYSTEM_SCHEDULER", role="System", outcome="Allowed")

        # 4. Agent Execution
        print("⚙️  Running Agent Reasoning...")
        context = retrieve_context(vectordb, query)
        
        state = {
            "query": query,
            "financial_context": context["financial_context"],
            "policy_context": context["policy_context"],
            "analysis": "",
            "comparison": "",
            "policy_check": "",
            "recommendations": "",
            "final_answer": ""
        }

        result = agent.invoke(state)
        
        # 5. Save Report to Disk
        output_dir = ROOT_DIR / "reports"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_trigger_name = trigger["trigger_name"].replace(" ", "_").lower()
        filename = output_dir / f"{safe_trigger_name}_{timestamp}.md"
        
        with open(filename, "w") as f:
            f.write(f"# {trigger['trigger_name']}\n")
            f.write(f"**Date:** {datetime.now()}\n")
            f.write(f"**Query:** {query}\n")
            f.write("---\n\n")
            f.write(result["final_answer"])
            
        print(f"\n✅ Insights Generated and Saved to: {filename}")
        print("="*40)
        print(result["final_answer"])
        print("="*40)

if __name__ == "__main__":
    run_scheduler()
