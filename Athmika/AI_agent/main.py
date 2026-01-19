import os
import requests
from dotenv import load_dotenv

from langchain_groq import ChatGroq

# ---------------------------
# Load env
# ---------------------------
load_dotenv()

# ---------------------------
# Weather function (pure Python)
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
        return "Could not retrieve weather data."

    data = response.json()
    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]

    return f"The weather in {city} appears to be {desc} with a temperature of {temp}°C."


# ---------------------------
# LLM
# ---------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# ---------------------------
# Step 1: Ask model what to do
# ---------------------------
decision = llm.invoke(
    "You are a router. If the user asks about weather, reply ONLY with: WEATHER:<city>\n\n"
    "User: What is the current weather in New York?"
)

content = decision.content.strip()

# ---------------------------
# Step 2: Execute tool deterministically
# ---------------------------
if content.startswith("WEATHER:"):
    city = content.split("WEATHER:")[1].strip()
    result = get_weather(city)
    print(result)
else:
    print(decision.content)
