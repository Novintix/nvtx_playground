import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


# ✅ Load env
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ✅ Groq model
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
)

# ✅ Job Description (later: from DB)
JD_TEXT = """
Role: Senior HR Recruiter
Requirements:
- Communication skills
- Experience with ATS systems
- Interviewing skills
- Talent sourcing
Nice to have:
- Familiarity with HR software like Workday or BambooHR
- Knowledge of labor laws and compliance
- Experience in technical recruiting
"""

# ✅ Where to search + what to search
DOCS_FOLDER = str(Path.home() / "Documents")
RESUME_FILENAME = "resume.pdf"


async def mcp_find_resume_path(session: ClientSession, folder: str, filename: str) -> str | None:
    """
    Uses MCP tool: search_files
    Returns best match file path or None
    """
    search_result = await session.call_tool(
        "search_files",
        {"folder": folder, "query": filename},
    )

    matches = []
    for item in search_result.content:
        matches.append(item.text if hasattr(item, "text") else str(item))

    # If tool returned an error message
    if not matches:
        return None
    if len(matches) == 1 and matches[0].startswith("❌"):
        return None

    # Pick the first match (simple v1)
    return matches[0]


async def mcp_read_resume_text(session: ClientSession, pdf_path: str) -> str:
    """
    Uses MCP tool: read_pdf_text
    Returns extracted text
    """
    read_result = await session.call_tool("read_pdf_text", {"path": pdf_path})

    text = ""
    for item in read_result.content:
        text += item.text if hasattr(item, "text") else str(item)

    return text.strip()


async def main():
    print("\n📌 HR Screening Agent Started (MCP + Groq)")
    print("📂 Searching in:", DOCS_FOLDER)
    print("🔎 Looking for:", RESUME_FILENAME)

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "server/local_agent_server.py"],
    )

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # ✅ Step 1: Find resume path using MCP search tool
            resume_path = await mcp_find_resume_path(session, DOCS_FOLDER, RESUME_FILENAME)

            if not resume_path:
                print("\n❌ Resume not found.")
                return

            print("\n✅ Resume found:", resume_path)

            # ✅ Step 2: Read resume text using MCP PDF tool
            resume_text = await mcp_read_resume_text(session, resume_path)

            if resume_text.startswith("❌") or len(resume_text.strip()) == 0:
                print("\n❌ Could not extract resume text.")
                print(resume_text)
                return

    # ✅ Step 3: Run Groq screening (client-side sampling)
    prompt = f"""
You are an HR Screening Agent.

Compare the resume with the JD and return STRICT JSON only:

{{
  "match_score": 0,
  "decision": "SHORTLIST" | "REJECT" | "WAITLIST",
  "strengths": [],
  "missing_skills": [],
  "reasoning": "",
  "hr_questions": []
}}

Resume:
{resume_text}

Job Description:
{JD_TEXT}
"""

    result = llm.invoke(prompt)

    print("\n✅ FINAL OUTPUT (JSON):\n")
    print(result.content)


if __name__ == "__main__":
    asyncio.run(main())
