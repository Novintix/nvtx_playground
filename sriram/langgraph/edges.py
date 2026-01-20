import os
import requests
from dotenv import load_dotenv
from typing import TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langgraph.graph import StateGraph, END

# ---------------- ENV ---------------- #
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# ---------------- STATE ---------------- #
class AgentState(TypedDict):
    user_query: str
    city: str
    plan: str
    weather_info: str
    risk_info: str
    final_answer: str


# ---------------- TOOL ---------------- #
@tool
def get_weather(city: str) -> str:
    """Fetch real-time weather information for a given city."""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    data = requests.get(url).json()

    if data.get("cod") != 200:
        return f"Weather not available for {city}"

    return f"{city}: {data['main']['temp']}°C, {data['weather'][0]['description']}"


# ---------------- LLM ---------------- #
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3
)

# ---------------- JSON HELPER ---------------- #
def extract_and_parse_json(text: str):
    """
    Extract JSON from markdown and parse it.
    Repairs if invalid.
    """
    import json

    text = text.strip()

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = llm.invoke(f"Fix this JSON:\n{text}").content
        repaired = repaired.replace("```json", "").replace("```", "")
        return json.loads(repaired)


# ---------------- AGENTS ---------------- #

# 1️⃣ Planner Agent
def planner_agent(state: AgentState):
    """Extract city and steps from user query."""
    prompt = f"""
You are a planning agent.

User query: "{state['user_query']}"

Return only JSON:
{{"city":"<city>","plan":"<steps>"}}
"""

    raw = llm.invoke(prompt).content
    parsed = extract_and_parse_json(raw)

    plan = parsed["plan"]
    if isinstance(plan, list):
        plan = "\n".join(plan)

    return {"city": parsed["city"], "plan": plan}


# 2️⃣ Weather Agent
def weather_agent(state: AgentState):
    """Fetch weather details for selected city."""
    weather = get_weather.invoke({"city": state["city"]})
    return {"weather_info": weather}


# 3️⃣ Risk Analysis Agent
def risk_agent(state: AgentState):
    """Analyze travel safety based on weather."""
    prompt = f"""
You are a travel safety evaluator.

Weather Data: {state['weather_info']}

Provide short travel safety advice.
"""
    risk = llm.invoke(prompt).content
    return {"risk_info": risk}


# 4️⃣ Reviewer Agent
def reviewer_agent(state: AgentState):
    """Generate final travel recommendation."""
    prompt = f"""
You are the final travel advisor.

User Question: {state['user_query']}

Weather: {state['weather_info']}
Risk: {state['risk_info']}

Give a clear final recommendation.
"""
    final = llm.invoke(prompt).content
    return {"final_answer": final}


# ---------------- GRAPH ---------------- #
graph = StateGraph(AgentState)

graph.add_node("planner", planner_agent)
graph.add_node("weather", weather_agent)
graph.add_node("risk", risk_agent)
graph.add_node("reviewer", reviewer_agent)

graph.set_entry_point("planner")

graph.add_edge("planner", "weather")
graph.add_edge("weather", "risk")
graph.add_edge("risk", "reviewer")
graph.add_edge("reviewer", END)

app = graph.compile()


# ---------------- CHATBOT LOOP ---------------- #
if __name__ == "__main__":
    print("\n🤖 Agentic Travel Planner Chatbot")
    print("Type 'bye' to exit\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["bye", "exit", "quit"]:
            print("Bot: Bye 👋")
            break

        result = app.invoke({"user_query": user_input})
        print("\nBot:", result["final_answer"])
        print("-" * 50)
