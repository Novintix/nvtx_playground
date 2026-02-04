# main.py

from risk import calculate_rpn, requires_rca
from fishbone import create_empty_fishbone
from agent import build_ranked_fishbone

AUTO_MODE = True   # learning mode


def auto_approval(ranked):
    top = ranked[0]
    print("\n" + "="*50)
    print("--- AUTO-APPROVED ROOT CAUSE (LEARNING MODE) ---")
    print("="*50)
    print(f"IDENTIFIED CAUSE : {top['cause']}")
    print(f"6M CATEGORY      : {top['category']}")
    print(f"SUPPORT SCORE    : {top['support_score']}")
    
    print("\n[FISHBONE ANALYSIS (6M)]")
    for k, v in top["why"].items():
        if k != "6M_mapping":
            print(f" - {k.replace('_', ' ').capitalize()}: {v}")
    
    print("\n[5-WHY DRILL DOWN]")
    for i, step in enumerate(top["five_why"], 1):
        print(f"  {step}")
        
    print("="*50)
    return top


def main():
    event = "Syringe barrel broken during injection"
    print(f"\nINCIDENT: {event}")

    # Risk gate
    rpn = calculate_rpn(9, 7, 2)  # High severity, high occurrence
    print(f"Calculated RPN: {rpn}")

    if not requires_rca(rpn):
        print("RCA not required.")
        return

    print("STRICT RCA INITIATED (Safety Critical)")

    # Candidate causes
    candidate_causes = [
        "Supplier material defect in barrel plastic",
        "Excessive plunger force from filling machine",
        "Dropped during hospital transport",
        "Improper aseptic handling by nurse",
        "Incorrect test method for brittle strength",
        "Thermal stress during sterilization"
    ]

    ranked = build_ranked_fishbone(candidate_causes, event)

    if AUTO_MODE:
        auto_approval(ranked)


if __name__ == "__main__":
    main()
