import asyncio
import os
import json
import re
from dotenv import load_dotenv
from fastmcp import Client
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def extract_json(text: str) -> dict:
    """
    Safely extract JSON object from LLM output
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Invalid JSON from LLM:\n{text}")

async def main():
    async with Client("http://127.0.0.1:8000/mcp") as client:

        user_question = "what is temperature in tenkasi"

        # 1️⃣ List tools
        tools = await client.list_tools()
        tool_list = "\n".join(
            f"- {t.name}: {t.description}" for t in tools
        )

        # 2️⃣ Decide tool
        tool_decision_prompt = f"""
You are a tool selector.

Available tools:
{tool_list}

User question:
{user_question}

Reply with ONLY the tool name.
"""
        selected_tool = llm.invoke(tool_decision_prompt).content.strip()
        print("Selected tool:", selected_tool)

        # 3️⃣ Extract arguments (STRICT)
        argument_prompt = f"""
You are extracting arguments for a tool call.

Tool name: {selected_tool}
User question: {user_question}

RULES:
- Return ONLY valid JSON
- No explanation
- No markdown
- No extra text

JSON format examples:
Weather → {{ "city": "Coimbatore" }}
Planner → {{ "task": "Investigate motor overheating" }}
Summary → {{ "text": "..." }}

JSON:
"""
        args_text = llm.invoke(argument_prompt).content.strip()
        print("Raw args from LLM:", args_text)

        tool_args = extract_json(args_text)
        print("Parsed args:", tool_args)

        # 4️⃣ Call MCP tool
        result = await client.call_tool(selected_tool, tool_args)

        print("\nFinal Result:")
        print(result.data)

asyncio.run(main())
