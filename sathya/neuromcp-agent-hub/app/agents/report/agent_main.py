from typing import Dict, Any
from app.agents.report.agent import generate_final_report


def run_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final node in LangGraph
    """
    state["final_report"] = generate_final_report(state)

    state["logs"].append({"agent": "report", "msg": "Final report generated ✅"})
    return state
