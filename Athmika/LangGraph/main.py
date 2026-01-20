from typing import List, TypedDict
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import END, StateGraph

from chains import generation_chain, reflection_chain

# -------- State Definition --------
class State(TypedDict):
    messages: List[BaseMessage]
    critique: str

# -------- Graph Setup --------
graph = StateGraph(State)

GENERATE = "generate"
REFLECT = "reflect"

# -------- Nodes --------
def generate_node(state: State):
    response = generation_chain.invoke({
        "messages": state["messages"]
    })
    return {
        "messages": state["messages"] + [response]
    }

def reflect_node(state: State):
    response = reflection_chain.invoke({
        "messages": state["messages"]
    })
    return {
        "messages": state["messages"] + [
            HumanMessage(content=f"CRITIQUE:\n{response.content}")
        ]
    }

# -------- Add Nodes --------
graph.add_node(GENERATE, generate_node)
graph.add_node(REFLECT, reflect_node)

graph.set_entry_point(GENERATE)

# -------- Conditional Logic --------
def should_continue(state: State):
    # Stop after Generate → Critique → Generate
    if len(state["messages"]) > 4:
        return END
    return REFLECT

graph.add_conditional_edges(
    GENERATE,
    should_continue,
    {
        REFLECT: REFLECT,
        END: END
    }
)

graph.add_edge(REFLECT, GENERATE)

# -------- Compile --------
app = graph.compile()

# -------- Visualize Graph --------
print(app.get_graph().draw_mermaid())
app.get_graph().print_ascii()

# -------- Terminal Input --------
title = input("\n📝 Enter tweet title/topic: ")

# -------- Invoke Agent --------
response = app.invoke({
    "messages": [
        HumanMessage(
            content=(
                f"Tweet title/topic:\n"
                f"{title}\n\n"
                "Generate an engaging Twitter post based on this title. "
            )
        )
    ]
})

# -------- Human-Readable Output --------
messages = response["messages"]

print("\n🧵 TWITTER AGENT EXECUTION\n")
print("📝 TITLE:")
print(title)
print("\n")

for msg in messages:
    if isinstance(msg, AIMessage):
        print("🐦 GENERATED TWEET:")
        print(msg.content)
        print("-" * 70)
    elif isinstance(msg, HumanMessage) and msg.content.startswith("Critique"):
        print("🧐 CRITIQUE:\n")
        print(msg.content)
        print("-" * 70)

# -------- Final Tweet Only --------
final_tweet = next(
    msg.content for msg in messages[::-1]
    if isinstance(msg, AIMessage)
)

print("\n✅ FINAL TWEET OUTPUT:\n")
print(final_tweet)
