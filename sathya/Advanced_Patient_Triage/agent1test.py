import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"


async def start_triage(client: httpx.AsyncClient, user_input: str) -> dict:
    resp = await client.post(
        f"{BASE_URL}/triage/start",
        json={"user_input": user_input}
    )
    resp.raise_for_status()
    return resp.json()


async def continue_triage(client: httpx.AsyncClient, session_id: str, answers: dict) -> dict:
    resp = await client.post(
        f"{BASE_URL}/triage/continue",
        json={"session_id": session_id, "answers": answers}
    )
    resp.raise_for_status()
    return resp.json()


def ask_user_for_answers(follow_up_questions: list[dict]) -> dict:
    """
    Ask user in terminal to answer each follow-up question.
    We'll store answers in a dict.
    Keys can be generated from question text (simple),
    but for now we keep them numbered: q1, q2...
    """
    answers = {}
    print("\n🩺 Follow-up Questions:\n")

    for i, q in enumerate(follow_up_questions, start=1):
        question_text = q.get("question", f"Question {i}")
        reason = q.get("reason", "")

        print(f"{i}) {question_text}")
        if reason:
            print(f"   (reason: {reason})")

        user_ans = input("   Your answer: ").strip()
        answers[f"q{i}"] = user_ans

    return answers


async def main():
    print("\n" + "=" * 60)
    print("🧠 Advanced Patient Triage - Terminal Client")
    print("=" * 60)

    symptom_text = input("\nDescribe your symptoms: ").strip()
    if not symptom_text:
        print("❌ No input provided. Exiting.")
        return

    async with httpx.AsyncClient(timeout=60) as client:
        # 1) Start session
        start_result = await start_triage(client, symptom_text)

        session_id = start_result["session_id"]
        agent_output = start_result["agent_output"]

        print("\n✅ Session started:", session_id)
        print("\n--- Agent Output ---")
        print("Identified Symptoms:", agent_output.get("identified_symptoms", []))
        print("Triage Summary:", agent_output.get("clinical_notes", {}).get("triage_summary", ""))
        print("Ready for next agent:", agent_output.get("ready_for_next_agent"))

        # 2) Loop while agent needs clarification
        while True:
            followups = agent_output.get("follow_up_questions", [])

            if not followups:
                print("\n✅ No follow-up questions. Intake complete.")
                break

            # Ask user in terminal
            answers = ask_user_for_answers(followups)

            # Continue session
            cont_result = await continue_triage(client, session_id, answers)
            agent_output = cont_result["agent_output"]

            print("\n--- Updated Agent Output ---")
            print("Identified Symptoms:", agent_output.get("identified_symptoms", []))
            print("Triage Summary:", agent_output.get("clinical_notes", {}).get("triage_summary", ""))
            print("Ready for next agent:", agent_output.get("ready_for_next_agent"))

            # stop if ready
            if agent_output.get("ready_for_next_agent") is True:
                print("\n✅ Intake complete. Ready for Risk Agent.")
                break

    print("\n" + "=" * 60)
    print("👋 Done")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
