import asyncio
import httpx

BASE = "http://127.0.0.1:8000"


def print_agent1(agent_output: dict, title: str = "AGENT 1"):
    notes = agent_output.get("clinical_notes", {})
    followups = agent_output.get("follow_up_questions", [])

    print("\n" + "-" * 75)
    print(f"🩺 {title}: Symptom Interpretation")
    print("-" * 75)
    print("Identified Symptoms:", agent_output.get("identified_symptoms", []))
    print("Ready for next agent:", agent_output.get("ready_for_next_agent"))
    print("Triage Summary:", notes.get("triage_summary", ""))

    # If your backend stores these in notes, they may not always show here
    round_count = notes.get("_round_count", None)
    if round_count is not None:
        print("Round Count (server):", round_count)

    print("Follow-ups:", len(followups))
    if followups:
        print("\nFollow-up Questions:")
        for i, q in enumerate(followups, 1):
            print(f"  {i}) [{q.get('answer_key')}] {q.get('question')}")
            if q.get("reason"):
                print(f"      reason: {q.get('reason')}")


def collect_answers(followups: list[dict]) -> dict:
    """
    Ask the user each follow-up question and collect answers using answer_key.
    """
    answers = {}
    print("\n✍️ Type your answers (press Enter -> 'unknown'):\n")

    for q in followups:
        key = (q.get("answer_key") or "").strip()
        question = (q.get("question") or "").strip()

        if not key or not question:
            continue

        ans = input(f"- {question}\n  ({key}) = ").strip()
        if not ans:
            ans = "unknown"

        answers[key] = ans

    return answers


def print_agent2(risk: dict):
    print("\n" + "=" * 75)
    print("✅ AGENT 2: Risk Hypothesis OUTPUT")
    print("=" * 75)
    print("Risk Level:", risk.get("risk_level"))
    print("Triage Action:", risk.get("triage_action"))
    print("Confidence:", risk.get("confidence"))
    print("Red Flags:", risk.get("red_flags", []))
    print("Risk Reasons:", risk.get("risk_reasons", []))
    print("Handoff Summary:", risk.get("handoff_summary", ""))
    print("=" * 75 + "\n")


async def main():
    print("\n" + "=" * 75)
    print("FULL FLOW TERMINAL TEST: Agent 1 asks -> you answer -> Agent 2 output")
    print("=" * 75)

    initial_symptoms = input("\nDescribe symptoms: ").strip()
    if not initial_symptoms:
        print("❌ No symptoms entered. Exiting.")
        return

    async with httpx.AsyncClient(timeout=60) as client:
        # 1) Start session
        start_res = await client.post(
            f"{BASE}/triage/start",
            json={"user_input": initial_symptoms}
        )
        start_res.raise_for_status()
        start_data = start_res.json()

        session_id = start_data["session_id"]
        agent_output = start_data["agent_output"]

        print(f"\n✅ Session started: {session_id}")
        print_agent1(agent_output, title="AGENT 1 (START)")

        # 2) Loop: ask follow-ups -> continue until Agent 2 triggers
        while True:
            followups = agent_output.get("follow_up_questions", [])

            # If no followups, still call continue once (it might trigger Agent 2)
            if not followups:
                print("\n✅ No follow-up questions left. Checking for Agent 2...")
                cont_res = await client.post(
                    f"{BASE}/triage/continue",
                    json={"session_id": session_id, "answers": {}}
                )
            else:
                answers = collect_answers(followups)
                cont_res = await client.post(
                    f"{BASE}/triage/continue",
                    json={"session_id": session_id, "answers": answers}
                )

            cont_res.raise_for_status()
            cont_data = cont_res.json()

            # If Agent 2 triggered
            if cont_data.get("passed_to_agent2") is True:
                print("\n🚀 PASSED TO AGENT 2 ✅")
                symptom_agent_final = cont_data.get("symptom_agent", {})
                print_agent1(symptom_agent_final, title="AGENT 1 (FINAL)")
                print_agent2(cont_data.get("risk_agent", {}))
                break

            # Else continue Agent 1 loop
            print("\n🔁 Still Agent 1 loop...")
            agent_output = cont_data["agent_output"]
            print_agent1(agent_output, title="AGENT 1 (CONTINUE)")


if __name__ == "__main__":
    asyncio.run(main())
