import asyncio, json
from dotenv import load_dotenv
load_dotenv()
import json
from fastapi.encoders import jsonable_encoder

from app.langgraph.graph import build_graph

graph = build_graph()

async def main():
    state = {"user_request": "Schedule meeting tomorrow at 4pm and post in Slack", "logs": []}
    out = await graph.ainvoke(state)

    print("\nSTATUS:", out.get("status"))
    print("\nPLAN:", out.get("plan"))
    print("\nPENDING_APPROVALS:", out.get("pending_approvals"))
    print("\nLOGS:", out.get("logs"))

    # ✅ save for step2
    with open("run_state.json", "w", encoding="utf-8") as f:
        json.dump(jsonable_encoder(out), f, indent=2)

    print("\n✅ Saved: run_state.json")

asyncio.run(main())
