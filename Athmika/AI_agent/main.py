import os
import requests
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.agents import create_agent

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

# ---------------------------
# Weather function (deterministic)
# ---------------------------
def get_weather(city: str) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "OpenWeather API key not found."

    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric"
    )

    response = requests.get(url)
    if response.status_code != 200:
        return f"Could not retrieve weather data for {city}."

    data = response.json()
    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]

    return f"The weather in {city} appears to be {desc} with a temperature of {temp}°C and a humidity of {data['main']['humidity']}%"


# ---------------------------
# LLM (Groq)
# ---------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# ---------------------------
# System Prompt (Agent behavior)
# ---------------------------
SYSTEM_PROMPT = """
You are a Weather Reporting Agent.

Your job:
- Identify the city from the user's question.
- Respond ONLY in the format:

CITY:<city_name>

If no city is found, respond:
CITY:NONE

Do NOT answer with weather yourself.
"""

# ---------------------------
# Create Agent (MANDATORY)
# ---------------------------
agent = create_agent(
    model=llm,
    system_prompt=SYSTEM_PROMPT
)

# ---------------------------
# Run Agent
# ---------------------------
user_input = input("Ask about weather: ")

agent_response = agent.invoke({
    "messages": [
        {"role": "user", "content": user_input}
    ]
})

agent_text = agent_response["messages"][-1].content.strip()

# ---------------------------
# Execute weather lookup
# ---------------------------
if agent_text.startswith("CITY:"):
    city = agent_text.replace("CITY:", "").strip()

    if city.upper() == "NONE":
        print("Please specify a city name.")
    else:
        print(get_weather(city))
else:
    print("Agent could not understand the request.")
