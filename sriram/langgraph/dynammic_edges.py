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
    """Plans what to do based on user query"""
    prompt = f"""
    User question: {state['user_query']}
    Decide what steps are needed.
    """
    plan = llm.invoke(prompt).content
    return {"plan": plan}

# 2️⃣ Weather Agent
def weather_agent(state: AgentState):
    """Fetches weather information"""
    weather = get_weather.invoke({"city": "Chennai"})
    return {"weather_info": weather}

# 3️⃣ Reviewer Agent
def reviewer_agent(state: AgentState):
    """Produces final response"""
    if state.get("weather_info"):
        prompt = f"""
        Weather data:
        {state['weather_info']}

        Based on this, give travel advice.
        """
    else:
        prompt = f"""
        User question:
        {state['user_query']}

        Respond politely even without weather data.
        """

    final = llm.invoke(prompt).content
    return {"final_answer": final}

# ---------------- CONDITIONAL EDGE ---------------- #

def route_after_planner(state: AgentState) -> str:
    """
    Decides next node after planner.
    If user asked about weather → weather node
    Else → reviewer directly
    """
    query = state["user_query"].lower()
    if "weather" in query:
        return "weather"
    return "reviewer"

# ---------------- GRAPH ---------------- #
graph = StateGraph(AgentState)

graph.add_node("planner", planner_agent)
graph.add_node("weather", weather_agent)
graph.add_node("reviewer", reviewer_agent)

graph.set_entry_point("planner")

# 🔀 Conditional edge
graph.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "weather": "weather",
        "reviewer": "reviewer"
    }
)

# Normal edges
graph.add_edge("weather", "reviewer")
graph.add_edge("reviewer", END)

app = graph.compile()

# ---------------- RUN ---------------- #
result = app.invoke(
    {"user_query": "Is Chennai good for travel??"}
)

print("\nFINAL ANSWER:\n", result["final_answer"])

