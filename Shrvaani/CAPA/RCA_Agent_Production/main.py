from workflow import create_rca_graph
from state import AgentState

def main():
    # 1. Initialize State with Incident Data
    initial_state: AgentState = {
        "incident": "Syringe barrel broken during injection",
        "severity": 9,
        "occurrence": 7,
        "detection": 2,
        "rpn": None,
        "is_rca_required": False,
        "candidate_causes": [
            "Supplier material defect in barrel plastic",
            "Excessive plunger force from filling machine",
            "Dropped during hospital transport",
            "Improper aseptic handling by nurse",
            "Incorrect test method for brittle strength",
            "Thermal stress during sterilization"
        ],
        "ranked_causes": [],
        "top_cause": None,
        "analysis_report": "",
        "status": "start"
    }

    print("\n" + "="*50)
    print("PRO-GRADE RCA AGENT (LangGraph Powered)")
    print("="*50)
    print(f"INCIDENT: {initial_state['incident']}")

    # 2. Execute Graph
    app = create_rca_graph()
    final_output = app.invoke(initial_state)

    # 3. Final Display
    print("\n" + "="*50)
    print("FINAL RCA REPORT")
    print("="*50)
    if final_output["is_rca_required"]:
        print(f"RPN Score: {final_output['rpn']} (MANDATORY RCA)")
        print("\n" + final_output["analysis_report"])
    else:
        print(f"RPN Score: {final_output['rpn']} (RCA NOT MANDATORY)")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
