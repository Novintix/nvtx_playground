import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

@tool
def read_latest_email() -> dict:
    """Reads the latest email (mock)."""
    return {
        "from": "hr@company.com",
        "subject": "Interview Confirmation",
        "body": "Hi, can you confirm your availability for a 30-min interview this week?"
    }

@tool
def send_email(recipient: str, subject: str, body: str) -> str:
    """Sends an email (mock)."""
    return f"Email SENT to {recipient}"

model = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.1-8b-instant", temperature=0.7)

agent = create_agent(
    model=model,
    tools=[read_latest_email, send_email],
    checkpointer=MemorySaver(),
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
                "read_latest_email": False,
            }
        ),
    ],
)

config = {"configurable": {"thread_id": "1"}}

result = agent.invoke({
    "messages": [("user", """
Read the latest email from my inbox.
After reading it, write me a response email that says I'm available for the interview this week.
The response should be professional and different from the original email.
Then send this response to hr@company.com.
""")]
}, config)

# Show agent's summary/thinking before the interrupt
print("🤖 Reading email and composing reply...\n")

# Handle interrupt
if "__interrupt__" in result:
    interrupt = result["__interrupt__"][0]
    action = interrupt.value["action_requests"][0]
    
    print("="*60)
    print("📧 EMAIL READY TO SEND")
    print("="*60)
    print(f"To: {action['args']['recipient']}")
    print(f"Subject: {action['args']['subject']}")
    print(f"Body:\n{action['args']['body']}")
    print("="*60)
    
    decision = input("\nApprove? (yes/no): ").strip().lower()
    
    if decision == "yes":
        print("\n✅ Sending...\n")
        agent.invoke({"decision": "approve"}, config)
        print("✅ Sent!")
    else:
        print("\n❌ Cancelled")