from workflow import create_discovery_graph
from state import DiscoveryState

def main():
    # 1. Standardized Complaint Data (Zero History)
    # This incident has never occurred before in the historical database.
    initial_state: DiscoveryState = {
        "complaint_data": {
            "incident_id": "C-999",
            "material": "Polypropylene",
            "failure_mode": "Discoloration",
            "observation": "Syringe cap turned a distinct purple/yellow hue after sterilization."
        },
        "lot_number": "B-90210",
        "severity": 8,
        "occurrence": 4,
        "detection": 5,
        "rpn": None,
        "is_rca_required": False,
        "physical_attributes": ["Purple hue", "Polypropylene material"],
        "hypotheses": [],
        "verified_evidence": [],
        "analysis_report": "",
        "status": "start"
    }

    print("\n" + "="*60)
    print("RCA DISCOVERY AGENT (Zero-History / First Principles)")
    print("="*60)
    print(f"INCIDENT: {initial_state['complaint_data']['observation']}")
    print(f"LOT NUMBER: {initial_state['lot_number']}")

    # 2. Execute Graph
    app = create_discovery_graph()
    final_output = app.invoke(initial_state)

    # 3. Final Result
    print("\n" + final_output["analysis_report"])
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
