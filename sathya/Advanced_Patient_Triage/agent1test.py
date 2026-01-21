import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"


def _print_agent1(agent_output: dict, label: str) -> None:
    notes = agent_output.get("clinical_notes", {}) or {}
    followups = agent_output.get("follow_up_questions", []) or []

    print("\n" + "-" * 75)
    print(f"🩺 {label}: Symptom Interpretation (Agent 1)")
    print("-" * 75)
    print("Identified Symptoms:", agent_output.get("identified_symptoms", []))
    print("Ready for next agent:", agent_output.get("ready_for_next_agent"))
    print("Triage Summary:", notes.get("triage_summary", ""))
    print("Red Flags:", notes.get("red_flags", ""))
    print("Confidence:", notes.get("confidence", ""))
    print("Follow-ups:", len(followups))

    if followups:
        print("\nFollow-up Questions:")
        for i, q in enumerate(followups, 1):
            print(f"  {i}) [{q.get('answer_key')}] {q.get('question')}")
            if q.get("reason"):
                print(f"      reason: {q.get('reason')}")


def _collect_answers(followups: list[dict]) -> dict:
    """
    You answer follow-up questions. Uses answer_key for backend storage.
    Press Enter to send "unknown".
    """
    answers = {}
    print("\n✍️ Type your answers (press Enter -> 'unknown'):\n")

    for q in followups:
        key = (q.get("answer_key") or "").strip()
        question = (q.get("question") or "").strip()

        if not key or not question:
            continue

        user_ans = input(f"- {question}\n  ({key}) = ").strip()
        if not user_ans:
            user_ans = "unknown"

        answers[key] = user_ans

    return answers


def _print_agent2(risk_agent: dict) -> None:
    print("\n" + "=" * 75)
    print("✅ Agent 2: Risk Hypothesis OUTPUT")
    print("=" * 75)
    print("Risk Level:", risk_agent.get("risk_level"))
    print("Triage Action:", risk_agent.get("triage_action"))
    print("Confidence:", risk_agent.get("confidence"))
    print("Red Flags:", risk_agent.get("red_flags", []))
    print("Risk Reasons:", risk_agent.get("risk_reasons", []))
    print("Handoff Summary:", risk_agent.get("handoff_summary", ""))
    print("=" * 75)


def _print_agent3(risk_scoring: dict, next_step: str) -> None:
    print("\n" + "=" * 75)
    print("🛡️ Agent 3: Risk Scoring & Safety OUTPUT")
    print("=" * 75)
    print("Risk Score:", risk_scoring.get("risk_score"))
    print("Risk Level:", risk_scoring.get("risk_level"))
    print("Safety Flags:", risk_scoring.get("safety_flags", []))
    print("Next Step:", next_step)
    print("=" * 75 + "\n")


async def main():
    print("\n" + "=" * 75)
    print("FULL FLOW TERMINAL TEST: Agent 1 -> Agent 2 -> Agent 3")
    print("=" * 75)

    symptom_text = input("\nDescribe symptoms: ").strip()
    if not symptom_text:
        print("❌ No symptoms entered.")
        return

    async with httpx.AsyncClient(timeout=120) as client:
        # 1) Start triage session -> Agent 1
        start_resp = await client.post(f"{BASE_URL}/triage/start", json={"user_input": symptom_text})
        start_resp.raise_for_status()
        start_data = start_resp.json()

        session_id = start_data["session_id"]
        agent1_output = start_data["agent_output"]

        print(f"\n✅ Session started: {session_id}")
        _print_agent1(agent1_output, "AGENT 1 (START)")

        # 2) Continue loop until passed_to_agent2 True
        while True:
            followups = agent1_output.get("follow_up_questions", []) or []

            # If no follow-ups, still call continue once to trigger agent2+3 path
            if not followups:
                cont_payload = {"session_id": session_id, "answers": {}}
            else:
                answers = _collect_answers(followups)
                cont_payload = {"session_id": session_id, "answers": answers}

            cont_resp = await client.post(f"{BASE_URL}/triage/continue", json=cont_payload)
            cont_resp.raise_for_status()
            cont_data = cont_resp.json()

            # If Agent2+Agent3 triggered
            if cont_data.get("passed_to_agent2") is True:
                print("\n🚀 PASSED TO AGENT 2 ✅")

                symptom_agent = cont_data.get("symptom_agent", {}) or {}
                risk_agent = cont_data.get("risk_agent", {}) or {}
                risk_scoring = cont_data.get("risk_scoring_agent", {}) or {}
                next_step = cont_data.get("next_step", "unknown")

                _print_agent1(symptom_agent, "AGENT 1 (FINAL)")
                _print_agent2(risk_agent)
                _print_agent3(risk_scoring, next_step)
                break

            # Otherwise continue with Agent1
            print("\n🔁 Still Agent 1 loop...")
            agent1_output = cont_data.get("agent_output", {}) or {}
            _print_agent1(agent1_output, "AGENT 1 (CONTINUE)")


if __name__ == "__main__":
    asyncio.run(main())
