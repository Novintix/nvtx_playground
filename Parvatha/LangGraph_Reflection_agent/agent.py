import os
import operator
from typing import TypedDict, Annotated, Sequence

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END

# ===============================
# Load environment variables
# ===============================
load_dotenv()

# ===============================
# Initialize LLM
# ===============================
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5
)

# ===============================
# Define State
# ===============================
class ReflectionState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    question: str
    current_response: str
    critique: str
    iteration: int
    max_iterations: int

# ===============================
# Node 1: Generate Response
# ===============================
def generate_node(state: ReflectionState) -> dict:
    print(f"\n{'='*70}")
    print(f"🔵 GENERATE NODE - Iteration {state['iteration']}")
    print(f"{'='*70}")

    if state["iteration"] == 0:
        messages = [
            SystemMessage(content="You are a helpful AI assistant. Provide a clear, detailed answer."),
            HumanMessage(content=state["question"])
        ]
    else:
        improvement_prompt = f"""
Improve your previous response based on the critique.

Question:
{state['question']}

Previous Response:
{state['current_response']}

Critique:
{state['critique']}

Generate an improved response addressing all issues.
"""
        messages = [
            SystemMessage(content="You are an AI assistant focused on continuous improvement."),
            HumanMessage(content=improvement_prompt)
        ]

    response = llm.invoke(messages)

    # ✅ PRINT FULL GENERATED RESPONSE
    print("\n📄 Response Generated:")
    print(response.content)

    return {
        "messages": [response],
        "current_response": response.content
    }

# ===============================
# Node 2: Reflect on Response
# ===============================
def reflect_node(state: ReflectionState) -> dict:
    print(f"\n{'='*70}")
    print(f"🟡 REFLECT NODE - Iteration {state['iteration']}")
    print(f"{'='*70}")

    reflection_prompt = f"""
Critically evaluate the response below.

Question:
{state['question']}

Response:
{state['current_response']}

Provide critique on:
- Accuracy
- Completeness
- Clarity
- Structure
- Depth
"""

    messages = [
        SystemMessage(content="You are a critical expert reviewer."),
        HumanMessage(content=reflection_prompt)
    ]

    critique_response = llm.invoke(messages)

    # ✅ PRINT FULL CRITIQUE
    print("\n📋 Critique Generated:")
    print(critique_response.content)

    return {
        "messages": [critique_response],
        "critique": critique_response.content,
        "iteration": state["iteration"] + 1
    }

# ===============================
# Conditional Routing (Decision)
# ===============================
def should_continue(state: ReflectionState) -> str:
    print(f"\n{'='*70}")
    print("🔀 ROUTING DECISION")
    print(f"{'='*70}")
    print(f"Iteration: {state['iteration']} / {state['max_iterations']}")

    if state["iteration"] >= state["max_iterations"]:
        print("✅ STOPPING")
        return END
    else:
        print("🔄 CONTINUING")
        return "reflect"

# ===============================
# Build LangGraph
# ===============================
def create_reflection_graph():
    print("\n🏗️ Building LangGraph Reflection Agent...")

    workflow = StateGraph(ReflectionState)

    # Add nodes
    workflow.add_node("generate", generate_node)
    workflow.add_node("reflect", reflect_node)

    # Entry point
    workflow.set_entry_point("generate")

    # reflect always loops back to generate
    workflow.add_edge("reflect", "generate")

    # generate acts as conditional decision node
    workflow.add_conditional_edges(
        "generate",
        should_continue,
        {
            "reflect": "reflect",
            END: END
        }
    )

    # Compile graph
    app = workflow.compile()

    print("✅ Graph compiled successfully!")

    # Visualization
    print("\n🧩 MERMAID GRAPH:")
    print(app.get_graph().draw_mermaid())

    print("\n🧩 ASCII GRAPH:")
    app.get_graph().print_ascii()

    return app

# ===============================
# Run Agent
# ===============================
def run_reflection_agent(question: str, max_iterations: int = 2):
    print("\n🤖 LANGGRAPH REFLECTION AGENT")
    print("="*70)
    print(f"Question: {question}")
    print(f"Max Iterations: {max_iterations}")
    print("="*70)

    app = create_reflection_graph()

    initial_state: ReflectionState = {
        "messages": [],
        "question": question,
        "current_response": "",
        "critique": "",
        "iteration": 0,
        "max_iterations": max_iterations
    }

    final_state = app.invoke(initial_state)

    print("\n🎯 FINAL ANSWER")
    print("="*70)
    print(final_state["current_response"])
    print("="*70)

# ===============================
# Interactive Main
# ===============================
def main():
    print("\n🔄 LANGGRAPH REFLECTION AGENT - INTERACTIVE MODE")
    print("="*70)

    while True:
        user_input = input("\nEnter a question (or 'quit'): ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("👋 Exiting.")
            break

        iterations = input("Number of reflection cycles: ").strip()
        max_iterations = int(iterations) if iterations.isdigit() else 2

        run_reflection_agent(user_input, max_iterations)

# ===============================
# Entry Point
# ===============================
if __name__ == "__main__":
    main()
