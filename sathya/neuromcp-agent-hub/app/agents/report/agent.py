from typing import Dict, Any


def generate_final_report(state: Dict[str, Any]) -> str:
    """
    Produces user-facing final summary
    """

    goal = state["plan"]["goal"]
    results = state.get("execution_results", {})

    report = []
    report.append("✅ FINAL EXECUTION REPORT")
    report.append(f"Goal: {goal}\n")

    for step_id, info in results.items():
        report.append(f"Step {step_id}: {info['status']}")
        report.append(f"Tool: {info['tool']}")
        report.append(f"Output: {info['output']}\n")

    return "\n".join(report)
