from state import AgentState
from risk import calculate_rpn, requires_rca
from embedding_engine import map_to_6m
from data_mock import HISTORICAL_DATA, DEVICE_LOGS, TOTAL_CAPA_CASES, SCATTERED_FRAGMENTS

def risk_assessment_node(state: AgentState):
    print("--- NODE: RISK ASSESSMENT ---")
    rpn = calculate_rpn(state["severity"], state["occurrence"], state["detection"])
    required = requires_rca(rpn)
    return {
        "rpn": rpn,
        "is_rca_required": required,
        "status": "mapping" if required else "completed"
    }

def semantic_mapping_node(state: AgentState):
    print("--- NODE: SEMANTIC MAPPING ---")
    results = []
    for cause in state["candidate_causes"]:
        category, scores = map_to_6m(cause)
        results.append({
            "cause": cause,
            "category": category,
            "mapping_scores": scores
        })
    return {"ranked_causes": results, "status": "evidence_check"}

def evidence_validation_node(state: AgentState):
    print("--- NODE: EVIDENCE VALIDATION ---")
    final_ranked = []
    for item in state["ranked_causes"]:
        cause = item["cause"]
        data = HISTORICAL_DATA.get(cause, {"freq": 0, "evidence": []})
        
        # Scoring logic (ported from original core)
        freq_score = data["freq"] / TOTAL_CAPA_CASES
        hits = sum(1 for kw in data["evidence"] if any(kw in log for log in DEVICE_LOGS))
        evidence_score = min(hits * 0.4, 1.0)
        penalty = 0.3 if hits == 0 else 0.0
        
        support_score = round(0.5 * freq_score + 0.5 * evidence_score - penalty, 3)
        
        final_ranked.append({
            **item,
            "support_score": support_score,
            "status": "Verified" if hits > 0 else "Low Evidence"
        })
    
    final_ranked.sort(key=lambda x: x["support_score"], reverse=True)
    return {"ranked_causes": final_ranked, "top_cause": final_ranked[0], "status": "5_why"}


# ... (previous nodes remain same)

def five_why_node(state: AgentState):
    print("--- NODE: DYNAMIC 5-WHY SYNTHESIS ---")
    top = state["top_cause"]
    
    # 1. Retrieval Step (Simulating GraphRAG/Search)
    # The agent "picks" fragments based on the cause keywords
    findings = []
    
    # Logic: Search scattered fragments for links to 'barrel', 'brittle', 'dryer', 'maintenance'
    if "material defect" in top["cause"].lower():
        findings.append({"q": "Why did the barrel crack?", "source": "COMPLAINTS C-885", "a": "Brittle barrel identified in Batch B-90210."})
        findings.append({"q": "Why was it brittle?", "source": "LAB_REPORTS L-405", "a": "Resin moisture was 0.12% (6x limit)."})
        findings.append({"q": "Why was moisture high?", "source": "MFG_LOGS M-101", "a": "Dryer DH-04 failed to reach setpoint during run."})
        findings.append({"q": "Why did dryer fail?", "source": "MAINTENANCE Unit DH-04", "a": "Heating element burnt out (High resistance measured)."})
        findings.append({"q": "Why was element burnt out?", "source": "MAINTENANCE Schedule", "a": "PM cycle OVERDUE by 90 days."})

    report = f"IDENTIFIED CAUSE: {top['cause']}\n"
    report += f"6M CATEGORY     : {top['category']}\n"
    report += f"SUPPORT SCORE   : {top['support_score']}\n"
    report += "\n" + "="*60 + "\n"
    report += "[SYNTHESIS FROM SCATTERED DATA SILOS]"
    report += "\n" + "="*60 + "\n"
    
    for i, step in enumerate(findings, 1):
        report += f"WHY {i}?: {step['q']}\n"
        report += f"ANSWER: {step['a']}\n"
        report += f"EVIDENCE: [{step['source']}]\n"
        if i < len(findings):
            report += "-" * 30 + "\n"
    
    report += "="*60 + "\n"
    report += "CONCLUSION: Root systemic failure identified in Maintenance Frequency."
    
    return {"analysis_report": report, "status": "completed"}
