import os
import requests
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langchain.tools import tool
from langchain.agents import create_agent

load_dotenv()

# ---------------------------
# Weather Tool
# ---------------------------
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "OpenWeather API key not found."

    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric"
    )

    response = requests.get(url)
    if response.status_code != 200:
        return "Could not retrieve weather data."

    data = response.json()
    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]

    return f"The current weather in {city} is {desc} with {temp}°C."


# ---------------------------
# LLM (Groq)
# ---------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)

# ---------------------------
# Tools
# ---------------------------
tools = [
    TavilySearch(),
    get_weather
]

# ---------------------------
# ReAct Agent
# ---------------------------
agent = create_agent(
    model="groq:llama-3.1-8b-instant",
    tools=tools
)


# ---------------------------
# Invoke Agent
# ---------------------------
messages = [
    {"role": "user", "content": "What is the current weather in New York?"}
]

response = agent.invoke({"messages": messages})

print(response["messages"][-1].content)