import asyncio
import os

from dotenv import load_dotenv
from groq import Groq

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def convert_mcp_messages_to_chat(messages):
    """
    Convert MCP messages into Groq/OpenAI-style chat messages:
    [{"role": "user"/"assistant"/"system", "content": "..."}]
    """
    chat_messages = []
    for msg in messages:
        role = msg.role

        # MCP FastMCP usually returns TextContent
        if hasattr(msg.content, "text"):
            content = msg.content.text
        else:
            content = str(msg.content)

        # Groq supports user/assistant/system
        if role not in ["user", "assistant", "system"]:
            role = "user"

        chat_messages.append({"role": role, "content": content})

    return chat_messages


async def main():
    # ✅ Start MCP server via stdio
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "server/prompts_server.py"],
    )

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # ✅ Get prompt template from MCP server
            prompt_result = await session.get_prompt(
                "summarize",
                arguments={
                    "text": """MCP is a protocol that connects AI clients with AI servers.
Prompts are reusable instruction templates hosted by servers.
Resources are fetchable knowledge objects like docs and policies.
Tools are executable actions like browser automation, APIs, or database queries."""
                },
            )

            chat_messages = convert_mcp_messages_to_chat(prompt_result.messages)

            # ✅ Call Groq LLM to ACTUALLY summarize in bullets
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # fast + free-friendly
                messages=chat_messages,
                temperature=0.2,
            )

            print("\n✅ FINAL BULLET SUMMARY (Groq Output):\n")
            print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())
