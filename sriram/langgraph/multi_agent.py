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
    plan: str
    weather_info: str
    final_answer: str

# ---------------- TOOL ---------------- #
@tool
def get_weather(city: str) -> str:
    """Get current weather for a city"""
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    data = requests.get(url).json()

    if data.get("cod") != 200:
        return f"Weather not available for {city}"

    return f"{city}: {data['main']['temp']}°C, {data['weather'][0]['description']}"

# ---------------- LLM ---------------- #
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=GOOGLE_API_KEY
)

# ---------------- AGENTS ---------------- #

# 1️⃣ Planner Agent
def planner_agent(state: AgentState):
    prompt = f"""
    User question: {state['user_query']}
    Decide what steps are needed.
    """
    plan = llm.invoke(prompt).content
    return {"plan": plan}

# 2️⃣ Weather Agent
def weather_agent(state: AgentState):
    # Simple extraction for demo
    weather_chennai = get_weather.invoke({"city": "Chennai"})
    weather_info = weather_chennai
    return {"weather_info": weather_info}

# 3️⃣ Reviewer Agent
def reviewer_agent(state: AgentState):
    prompt = f"""
    Weather data:
    {state['weather_info']}

    Based on this, give travel advice.
    """
    final = llm.invoke(prompt).content
    return {"final_answer": final}

# ---------------- GRAPH ---------------- #
graph = StateGraph(AgentState)

graph.add_node("planner", planner_agent)
graph.add_node("weather", weather_agent)
graph.add_node("reviewer", reviewer_agent)

graph.set_entry_point("planner")

graph.add_edge("planner", "weather")
graph.add_edge("weather", "reviewer")
graph.add_edge("reviewer", END)

app = graph.compile()

# ---------------- RUN ---------------- #
result = app.invoke(
    {"user_query": "What is the weather in Chennai and is it suitable for travel?"}
)
mermaid = app.get_graph().draw_mermaid()
print(mermaid)

print("\nFINAL ANSWER:\n", result["final_answer"])
