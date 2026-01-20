import asyncio
import httpx

BASE = "http://127.0.0.1:8000"


def print_agent1(agent_output: dict):
    notes = agent_output.get("clinical_notes", {})
    followups = agent_output.get("follow_up_questions", [])

    print("\n" + "-" * 65)
    print("🩺 Agent 1: Symptom Interpretation")
    print("-" * 65)
    print("Identified Symptoms:", agent_output.get("identified_symptoms", []))
    print("Ready for next agent:", agent_output.get("ready_for_next_agent"))
    print("Triage Summary:", notes.get("triage_summary", ""))
    print("Follow-ups:", len(followups))

    if followups:
        print("\nFollow-up Questions:")
        for i, q in enumerate(followups, 1):
            print(f"  {i}) [{q.get('answer_key')}] {q.get('question')}")
            if q.get("reason"):
                print(f"     reason: {q.get('reason')}")


def collect_answers(followups: list[dict]) -> dict:
    answers = {}
    print("\n✍️ Enter your answers:")

    for q in followups:
        key = (q.get("answer_key") or "").strip()
        question = q.get("question", "")

        if not key:
            continue

        user_ans = input(f"- {question}\n  ({key}) = ").strip()
        if not user_ans:
            user_ans = "unknown"  # safe fallback

        answers[key] = user_ans

    return answers


def print_agent2(risk: dict):
    print("\n" + "=" * 65)
    print("✅ Agent 2: Risk Hypothesis OUTPUT")
    print("=" * 65)
    print("Risk Level:", risk.get("risk_level"))
    print("Triage Action:", risk.get("triage_action"))
    print("Confidence:", risk.get("confidence"))
    print("Red Flags:", risk.get("red_flags", []))
    print("Risk Reasons:", risk.get("risk_reasons", []))
    print("Handoff Summary:", risk.get("handoff_summary", ""))
    print("=" * 65 + "\n")


async def main():
    print("\n" + "=" * 65)
    print("FULL INTERACTIVE FLOW TEST (Agent 1 -> Agent 2)")
    print("=" * 65)

    initial_input = input("\nDescribe symptoms (example: fever + headache): ").strip()
    if not initial_input:
        print("❌ No symptoms entered. Exiting.")
        return

    async with httpx.AsyncClient(timeout=60) as client:
        # START
        start_res = await client.post(f"{BASE}/triage/start", json={"user_input": initial_input})
        start_res.raise_for_status()
        start_data = start_res.json()

        session_id = start_data["session_id"]
        agent_output = start_data["agent_output"]

        print(f"\n✅ Session started: {session_id}")
        print_agent1(agent_output)

        # LOOP
        while True:
            followups = agent_output.get("follow_up_questions", [])

            # If no followups, try continue with empty answers (might trigger agent 2)
            if not followups:
                print("\n✅ No follow-ups. Sending continue to check Agent 2...")
                cont_res = await client.post(
                    f"{BASE}/triage/continue",
                    json={"session_id": session_id, "answers": {}}
                )
                cont_res.raise_for_status()
                cont_data = cont_res.json()

                if cont_data.get("passed_to_agent2") is True:
                    print("\n🚀 Passed to Agent 2!")
                    print_agent2(cont_data["risk_agent"])
                    return

                agent_output = cont_data["agent_output"]
                print_agent1(agent_output)
                continue

            # Otherwise, ask user answers in terminal
            answers = collect_answers(followups)

            cont_res = await client.post(
                f"{BASE}/triage/continue",
                json={"session_id": session_id, "answers": answers}
            )
            cont_res.raise_for_status()
            cont_data = cont_res.json()

            # If agent2 triggered
            if cont_data.get("passed_to_agent2") is True:
                print("\n🚀 Passed to Agent 2!")
                # show final symptom agent state also
                print_agent1(cont_data.get("symptom_agent", {}))
                print_agent2(cont_data["risk_agent"])
                return

            # Still agent1
            agent_output = cont_data["agent_output"]
            print("\n🔁 Still Agent 1 clarification loop.")
            print_agent1(agent_output)


if __name__ == "__main__":
    asyncio.run(main())
