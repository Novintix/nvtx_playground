import asyncio
from fastmcp import Client
from langchain.tools import tool

@tool
def mcp_get_weather(city: str) -> str:
    """
    Get the current weather for a given city.

    Args:
        city (str): Name of the city (for example: Coimbatore, Chennai, London)

    Returns:
        str: Weather description with temperature
    """

    async def _call():
        async with Client("http://127.0.0.1:8000/mcp") as client:
            result = await client.call_tool(
                "get_weather",
                {"city": city}
            )
            return result.data

    return asyncio.run(_call())
