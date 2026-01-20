import asyncio
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# ✅ Always load .env from repo root (one level above /client)
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GROQ_API_KEY")

# ✅ Safe music folder path
MUSIC_FOLDER = str(Path.home() / "Music")


async def main():
    # ✅ SAFE PRINTS (before MCP stdio starts)
    print("✅ Loaded .env from:", ENV_PATH)
    print("✅ GROQ_API_KEY present:", bool(api_key))

    user_query = "Play the song 'Kannazhaga The Kiss Of Love' from my music folder"

    # ✅ Extract song name from user query (simple logic)
    song_query = user_query.lower()
    song_query = song_query.replace("play", "")
    song_query = song_query.replace("the song", "")
    song_query = song_query.replace("from my music folder", "")
    song_query = song_query.replace("'", "").replace('"', "").strip()

    if not song_query:
        print("❌ Could not extract song name from query.")
        return

    print("\n🎵 Mini Agent Pipeline Started")
    print("📌 Music folder:", MUSIC_FOLDER)
    print("🔎 Searching for:", song_query)

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "server/local_agent_server.py"],
    )

    best_match = None

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # ✅ Step 1: Search files using MCP tool
            search_result = await session.call_tool(
                "search_files",
                {"folder": MUSIC_FOLDER, "query": song_query},
            )

            # ✅ Convert MCP TextContent objects to plain strings
            clean_matches = []
            for item in search_result.content:
                if hasattr(item, "text"):
                    clean_matches.append(item.text)
                else:
                    clean_matches.append(str(item))

            matches = clean_matches

            if not matches:
                print("\n❌ No matches found.")
                return

            print("\n✅ Matches found:")
            for m in matches[:10]:
                print("-", m)

            # ✅ Step 2: If multiple matches, ask user to choose (elicitation)
            if len(matches) == 1:
                best_match = matches[0]
            else:
                print("\n🤔 Multiple matches found. Choose one:\n")

                display_matches = matches[:10]
                for i, m in enumerate(display_matches, start=1):
                    print(f"{i}. {m}")

                choice = input("\nEnter number to play (1-10): ").strip()

                if not choice.isdigit():
                    print("❌ Invalid choice. Please enter a number.")
                    return

                choice = int(choice)

                if choice < 1 or choice > len(display_matches):
                    print("❌ Choice out of range.")
                    return

                best_match = display_matches[choice - 1]

            print("\n🎯 Selected match:", best_match)

    # ✅ Step 3: Play AFTER MCP session closes (client-side)
    print("\n🎧 Playing locally (client-side)...")
    subprocess.Popen(["open", best_match])
    print("✅ Playing:", best_match)


if __name__ == "__main__":
    asyncio.run(main())
