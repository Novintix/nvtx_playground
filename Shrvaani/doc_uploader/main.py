import asyncio
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from graph import build_graph


async def main():
    root_path = input("Enter folder path to scan for resume PDFs: ").strip()
    root_path = str(Path(root_path).expanduser())

    # MCP server params (run your local MCP server file)
    server_params = StdioServerParameters(
        command="python",
        args=["doc_uploader/mcp_server.py"],
    )

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:

            # Must initialize session
            await session.initialize()

            graph = build_graph()

            result = await graph.ainvoke(
                {
                    "root_path": root_path,
                    "mcp_session": session,   # ✅ MCP injected into graph state
                }
            )

            print("\n=== ✅ RESUMES ROUTED ===\n")
            for item in result.get("results", []):
                print(f"File: {item['file']}")
                print(f"Moved To: {item['moved_to']}")
                print(f"Category: {item['category']} ({item['confidence']})")
                print(f"Reason: {item['reason']}")
                print(f"Target Folder: {item['target_folder']}")
                print(f"Email: {item.get('email','')}")
                print("-" * 60)

            print("\n=== ❌ SKIPPED PDFs (Not Resumes / Duplicates) ===")
            for fp, reason in result.get("skipped", []):
                print(f"- {fp} | {reason}")


if __name__ == "__main__":
    asyncio.run(main())