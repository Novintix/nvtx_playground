import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from requests import session
from requests import session

# ✅ Load .env from repo root
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DOCS_FOLDER = str(Path.home() / "Documents")


async def main():
    # ✅ Change this query to your file name
    user_query = "Summarize my file resume.pdf"

    # crude filename extraction
    filename = user_query.lower().replace("summarize", "").replace("my file", "").strip()

    if not filename:
        print("❌ Please mention the file name (example: notes.txt)")
        return

    print("\n📌 Local RAG Agent Started")
    print("📂 Searching in:", DOCS_FOLDER)
    print("🔎 Looking for file:", filename)

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "server/local_agent_server.py"],
    )

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # ✅ Step 1: Search file
            search_result = await session.call_tool(
                "search_files",
                {"folder": DOCS_FOLDER, "query": filename},
            )

            clean_matches = []
            for item in search_result.content:
                if hasattr(item, "text"):
                    clean_matches.append(item.text)
                else:
                    clean_matches.append(str(item))

            matches = clean_matches

            if not matches:
                print("\n❌ File not found in Documents.")
                return

            # ✅ Step 2: Choose file if multiple matches
            if len(matches) == 1:
                file_path = matches[0]
            else:
                print("\n🤔 Multiple files found. Choose one:\n")
                display_matches = matches[:10]
                for i, m in enumerate(display_matches, start=1):
                    print(f"{i}. {m}")

                choice = input("\nEnter number to read (1-10): ").strip()
                if not choice.isdigit():
                    print("❌ Invalid choice.")
                    return

                choice = int(choice)
                if choice < 1 or choice > len(display_matches):
                    print("❌ Choice out of range.")
                    return

                file_path = display_matches[choice - 1]

            print("\n✅ Selected file:", file_path)

            # ✅ Step 3: Read file content
            if file_path.lower().endswith(".pdf"):
                read_result = await session.call_tool("read_pdf_text", {"path": file_path})
            else:
                read_result = await session.call_tool("read_text_file", {"path": file_path})


            # read_result.content may contain TextContent objects
            file_text = ""
            if isinstance(read_result.content, list):
                for item in read_result.content:
                    if hasattr(item, "text"):
                        file_text += item.text
                    else:
                        file_text += str(item)
            else:
                file_text = str(read_result.content)

            if "❌" in file_text:
                print("\n❌ Error reading file:")
                print(file_text)
                return

    # ✅ Step 4: Summarize using Groq (LLM)
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Summarize the content in bullet points and list action items."},
            {"role": "user", "content": file_text[:12000]},  # avoid huge files
        ],
        temperature=0.2,
    )

    print("\n✅ SUMMARY OUTPUT:\n")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())
