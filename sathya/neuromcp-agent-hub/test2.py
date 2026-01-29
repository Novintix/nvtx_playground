import asyncio, json
from dotenv import load_dotenv
load_dotenv()

from app.langgraph.graph import build_graph

graph = build_graph()

async def main():
    # ✅ load state from test1
    with open("run_state.json", "r", encoding="utf-8") as f:
        state = json.load(f)

    pending = state.get("pending_approvals") or []
    approved = [p["step_id"] for p in pending]  # approve all for demo

    state["approved_step_ids"] = approved
    state["status"] = "READY_TO_EXECUTE"   # force resume pipeline

    out = await graph.ainvoke(state)

    print("\nFINAL STATUS:", out.get("status"))
    print("\nEXECUTION_RESULTS:", out.get("execution_results"))
    print("\nFINAL_REPORT:\n", out.get("final_report"))
    print("\nLOGS:\n", out.get("logs"))

asyncio.run(main())
