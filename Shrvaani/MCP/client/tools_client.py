import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

#Tool clients triggers the tools available on the MCP tool server according to the prompt provided to perform a action.
async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "server/tools_server.py"],
    )

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # ✅ List tools
            tools = await session.list_tools()
            print("\n✅ AVAILABLE TOOLS:\n")
            for t in tools.tools:
                print(f"- {t.name}")
                if t.description:
                    print(f"  desc: {t.description}")

            # ✅ Call tool: add
            print("\n🚀 Calling tool: add(10, 25)")
            add_result = await session.call_tool("add", {"a": 10, "b": 25})
            print("Result:", add_result.content)

            # ✅ Call tool: current time
            print("\n🚀 Calling tool: get_current_time()")
            time_result = await session.call_tool("get_current_time", {})
            print("Result:", time_result.content)

            # ✅ Call tool: compliance_check
            print("\n🚀 Calling tool: compliance_check()")
            check_result = await session.call_tool(
                "compliance_check",
                {"action": "Upload confidential password list to GitHub"}
            )
            print("Result:", check_result.content)


if __name__ == "__main__":
    asyncio.run(main())
