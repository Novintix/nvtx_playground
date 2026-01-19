import asyncio
from fastmcp import Client

async def main():
    # ✅ Base URL ONLY
    async with Client("http://127.0.0.1:8000/mcp") as client:

        weather = await client.call_tool(
            "get_weather",
            {"city": "Coimbatore"}
        )
        print("\nWeather:", weather)

        plan = await client.call_tool(
            "planner_prompt",
            {"task": "Investigate motor overheating issue"}
        )
        print("\nPlan:", plan)

        summary = await client.call_tool(
            "summary_prompt",
            {"text": "Motor overheating occurs frequently during peak load hours."}
        )
        print("\nSummary:", summary)

asyncio.run(main())
