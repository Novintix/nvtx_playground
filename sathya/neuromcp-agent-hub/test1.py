import asyncio
from app.langgraph.graph import build_graph

graph = build_graph()

async def main():
    state = {"user_request": "Schedule meeting tomorrow at 4pm and post in Slack", "logs": []}
    out = await graph.ainvoke(state)

    print("\nSTATUS:", out.get("status"))
    print("\nPLAN:", out.get("plan"))
    print("\nPENDING_APPROVALS:", out.get("pending_approvals"))
    print("\nLOGS:", out.get("logs"))

asyncio.run(main())
