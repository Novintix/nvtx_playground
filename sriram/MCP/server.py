import os
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

mcp = FastMCP("Utility Server")

@mcp.tool()
def get_weather(city: str) -> str:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    data = requests.get(url).json()

    if data.get("cod") != 200:
        return f"Weather not found for {city}"

    return f"{city}: {data['weather'][0]['description']}, {data['main']['temp']}°C"

@mcp.tool()
def planner_prompt(task: str) -> str:
    return f"Plan this task step-by-step:\n{task}"

@mcp.tool()
def summary_prompt(text: str) -> str:
    return f"Summary:\n{text[:100]}..."

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",   # IMPORTANT
        port=8000
    )
