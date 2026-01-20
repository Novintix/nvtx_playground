import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "server/resources_server.py"],
    )

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # ✅ List resources
            resources = await session.list_resources()
            print("\n✅ AVAILABLE RESOURCES:\n")

            for r in resources.resources:
                print(f"- {r.uri}")
                if r.name:
                    print(f"  name: {r.name}")
                if r.description:
                    print(f"  desc: {r.description}")

            # ✅ Read one resource
            uri = "docs://mcp/intro"
            print(f"\n📌 Reading resource: {uri}\n")

            content_result = await session.read_resource(uri)

            for item in content_result.contents:
                # usually TextContent
                if hasattr(item, "text"):
                    print(item.text)
                else:
                    print(str(item))


if __name__ == "__main__":
    asyncio.run(main())
