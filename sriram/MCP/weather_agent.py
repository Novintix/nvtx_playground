import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from mcp_weather_tool import mcp_get_weather

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=GOOGLE_API_KEY
)

tools = [mcp_get_weather]

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=(
        "You are a weather assistant.\n"
        "When a user asks about weather or temperature, "
        "you MUST call the mcp_get_weather tool.\n"
        "Extract the city name from the user's question "
        "and pass it as the 'city' argument."
    )
)

result = agent.invoke(
    {"messages": [("user", "What is the weather in Coimbatore?")]}
)

print("\nFinal Answer:", result["messages"][-1].content)
