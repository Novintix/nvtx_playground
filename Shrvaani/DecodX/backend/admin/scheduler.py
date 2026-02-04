import sys
import os
from datetime import datetime
from pathlib import Path
import time
from dotenv import load_dotenv

# Corporate Pathing
ADMIN_DIR = Path(__file__).resolve().parent
ROOT_DIR = ADMIN_DIR.parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services.governance_service import get_grounded_context, audit_event
from backend.services.reasoning_service import build_graph

# Load env
load_dotenv(ROOT_DIR / ".env")

def run_scheduler():
    print("⏰ Starting Corporate Scheduled Audit...")
    
    # 1. Audit Entry
    audit_event(
        event_type="ENTRY",
        user_id="SYSTEM_SCHEDULER",
        user_role="System",
        query="Monthly Financial Compliance Audit (Automated)",
        details="Triggered by corporate scheduler"
    )

    # 2. Define Audit Scope
    query = "Compare revenue and costs for across all regions. Are there any policy breaches?"
    
    # 3. Retrieve Context via Services
    context = get_grounded_context(query)
    
    # 4. Agent Reasoning
    graph = build_graph()
    state = {
        "query": query,
        "user_role": "Admin",
        "user_id": "SYSTEM_SCHEDULER",
        "financial_context": context.get("financial_context", []),
        "policy_context": context.get("policy_context", []),
        "analysis": "",
        "comparison": "",
        "policy_check": "",
        "recommendations": "",
        "final_answer": ""
    }
    
    print("🧠 Running Agent reasoning for automated report...")
    result = graph.invoke(state)
    
    # 5. Generate Physical Report
    reports_dir = ROOT_DIR / "reports"
    if not reports_dir.exists():
        os.makedirs(reports_dir)
        
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = reports_dir / f"monthly_financial_review_{timestamp}.md"
    
    report_content = f"""# DecodX Automated Compliance Report
**Generated On:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Trigger:** Corporate Schedule (v2.0)

## 📊 Performance Analysis
{result.get('analysis', 'No analysis generated.')}

## 🛡️ Governance & Policy Audit
{result.get('policy_check', 'No policy check performed.')}

## 💡 Strategic Recommendations
{result.get('recommendations', 'No recommendations provided.')}

---
**Status:** Audit Complete | **Signed:** DecodX Reasoning Engine (Corporate Protocol)
"""
    
    with open(report_path, "w") as f:
        f.write(report_content)
    
    print(f"✅ Report generated: {report_path}")

    # 6. Audit Exit
    audit_event(
        event_type="EXIT",
        user_id="SYSTEM_SCHEDULER",
        user_role="System",
        query=query,
        details=f"Generated report: {report_path.name}"
    )

if __name__ == "__main__":
    run_scheduler()
