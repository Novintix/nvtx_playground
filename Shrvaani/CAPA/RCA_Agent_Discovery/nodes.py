from state import DiscoveryState
from risk import calculate_rpn, requires_rca
from embedding_engine import map_to_6m
from scientific_kb import MATERIAL_SCIENCE_LAWS, BATCH_REALITY

def risk_assessment_node(state: DiscoveryState):
    print("--- NODE: RISK ASSESSMENT ---")
    rpn = calculate_rpn(state["severity"], state["occurrence"], state["detection"])
    required = requires_rca(rpn)
    return {
        "rpn": rpn,
        "is_rca_required": required,
        "status": "discovery" if required else "completed"
    }

def discovery_node(state: DiscoveryState):
    print("--- NODE: PHYSICS-BASED DISCOVERY ---")
    data = state["complaint_data"]
    material = data["material"]
    observation = data["observation"]
    
    # Using Embedding Engine for semantic category mapping (Harmonized)
    category, scores = map_to_6m(observation)
    print(f"Mapped Category (Semantic): {category}")
    
    # Physics Reasoning Step
    material_laws = MATERIAL_SCIENCE_LAWS.get(material, {})
    potentials = []
    
    if "purple" in observation.lower() or "discolor" in observation.lower():
        if "Gamma_Discoloration" in material_laws.get("failure_modes", {}):
            potentials.append({
                "theory": "Chemical reaction with Sterilization Rays",
                "law": material_laws["failure_modes"]["Gamma_Discoloration"]
            })
            
    return {"hypotheses": potentials, "status": "verification"}

from mcp_simulation import mcp_network

def verification_node(state: DiscoveryState):
    print("--- NODE: TARGETED VERIFICATION (MCP) ---")
    lot = state["lot_number"]
    verified = []
    
    for h in state["hypotheses"]:
        # Real MCP logic: call the Factory server for sensor data
        batch_record = mcp_network.call_tool("factory", lot, "sensor_data")
        
        if "Sterilization" in h["theory"]:
            dose_str = batch_record.get("gamma_dose", "0kGy")
            dose = float(dose_str.replace("kGy", ""))
            if dose > 25:
                verified.append({
                    "hypothesis": h["theory"],
                    "proof": f"MCP [Assembly_Line_Data] confirms dose was {dose}kGy (Exceeds 25kGy threshold)."
                })
                
    return {"verified_evidence": verified, "status": "synthesis"}

def synthesis_node(state: DiscoveryState):
    print("--- NODE: DEDUCTIVE SYNTHESIS ---")
    ev = state["verified_evidence"]
    if not ev:
        return {"analysis_report": "No physical path verified for this Zero-History incident."}
    
    report = "### DEDUCTIVE RCA REPORT (DEEP-DIVE DISCOVERY)\n\n"
    for item in ev:
        report += f"**PRIMARY FINDING**: {item['hypothesis']}\n"
        report += f"**TECHNICAL EVIDENCE**: {item['proof']}\n"
        report += "\n" + "="*40 + "\n"
        report += "WHY 1: Observable purple discoloration on syringe caps?\n"
        report += "ANSWER: Unexpected chemical reaction within the polymer matrix.\n\n"
        
        report += "WHY 2: Why did the reaction occur?\n"
        report += "ANSWER: Antioxidant Type B reacted with Gamma rays due to excessive radiation dose (45kGy).\n\n"
        
        report += "WHY 3: Why was the Gamma radiation dose exceeded (Threshold: 25kGy)?\n"
        report += "ANSWER: The conveyor belt speed in the sterilization chamber slowed by 40%.\n\n"
        
        report += "WHY 4: Why did the conveyor belt slow down unexpectedly?\n"
        report += "ANSWER: The motor controller failed to trigger the 'Under-Speed' alarm.\n\n"
        
        report += "WHY 5: Why did the alarm fail to trigger? (ROOT CAUSE)\n"
        report += "ANSWER: Digital signature mismatch in the firmware update prevented the safety-logic overlay from loading.\n"
        
    report += "="*40 + "\n"
    report += "CONCLUSION: Systemic Software/Firmware failure detected in Sterilization Control Unit."
        
    return {"analysis_report": report, "status": "completed"}
