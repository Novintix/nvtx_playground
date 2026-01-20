from typing import List, TypedDict
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import END, StateGraph

from chains import generation_chain, reflection_chain


# -------- STATE --------
class State(TypedDict):
    messages: List[BaseMessage]
    step: int


# -------- GRAPH --------
graph = StateGraph(State)

GENERATE = "generate"
REFLECT = "reflect"


# -------- GENERATE NODE --------
def generate_node(state: State):
    filtered_messages = []

    # Always keep the first Human prompt
    filtered_messages.append(state["messages"][0])

    # Add last critique if exists
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage) and "Critique" in msg.content:
            filtered_messages.append(msg)
            break

    # Add last generated tweet if exists
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            filtered_messages.append(msg)
            break

    response = generation_chain.invoke({
        "messages": filtered_messages
    })

    return {
        "messages": state["messages"] + [response],
        "step": state["step"]
    }




# -------- REFLECT NODE --------
def reflect_node(state: State):
    last_tweet = next(
        msg.content for msg in reversed(state["messages"])
        if isinstance(msg, AIMessage)
    )

    response = reflection_chain.invoke({
        "messages": [
            HumanMessage(content=last_tweet)
        ]
    })

    return {
        "messages": state["messages"] + [
            HumanMessage(content=f"Critique:\n{response.content}")
        ],
        "step": state["step"] + 1
    }



# -------- ADD NODES --------
graph.add_node(GENERATE, generate_node)
graph.add_node(REFLECT, reflect_node)

graph.set_entry_point(GENERATE)


# -------- CONTROL FLOW --------
def should_continue(state: State):
    # 2 reflections → final generation
    if state["step"] >= 2:
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


# -------- COMPILE --------
app = graph.compile()


# -------- INPUT --------
title = input("\n📝 Enter tweet title/topic: ")

initial_message = HumanMessage(
    content=(
        f"Tweet title/topic:\n{title}\n\n"
        "Generate an engaging Twitter post based on this topic."
    )
)

result = app.invoke({
    "messages": [initial_message],
    "step": 0
})


# -------- OUTPUT --------
messages = result["messages"]

print("\n🧵 TWITTER AGENT EXECUTION\n")
print("📝 TITLE:")
print(title)
print("\n")

gen_count = 1
ref_count = 1

for msg in messages:
    if isinstance(msg, AIMessage):
        print(f"🐦 GENERATION {gen_count}:")
        print(msg.content)
        print("-" * 70)
        gen_count += 1

    elif isinstance(msg, HumanMessage) and msg.content.strip():
        print(f"🧐 REFLECTION {ref_count}:")
        print(msg.content)
        print("-" * 70)
        ref_count += 1


# -------- FINAL TWEET --------
final_tweet = next(
    msg.content for msg in reversed(messages)
    if isinstance(msg, AIMessage)
)

print("\n✅ FINAL TWEET OUTPUT:\n")
print(final_tweet)
