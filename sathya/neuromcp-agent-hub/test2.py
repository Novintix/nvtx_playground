import asyncio
from app.langgraph.graph import build_graph

graph = build_graph()

async def main():
    state = {"user_request": "Schedule meeting tomorrow at 4pm and post in Slack", "logs": []}

    # RUN 1
    out = await graph.ainvoke(state)

    pending = out.get("pending_approvals") or []
    approved = [p["step_id"] for p in pending]

    # RUN 2
    out["approved_step_ids"] = approved
    out["status"] = "READY_TO_EXECUTE"  # optional

    out2 = await graph.ainvoke(out)

    print("\nFINAL STATUS:", out2.get("status"))
    print("\nEXECUTION_RESULTS:", out2.get("execution_results"))
    print("\nFINAL_REPORT:", out2.get("final_report"))
    print("\nLOGS:", out2.get("logs"))

asyncio.run(main())
