from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from graph import build_graph
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters

app = FastAPI(title="HRMS Resume Uploader")

TMP_DIR = Path("tmp_uploads")
TMP_DIR.mkdir(exist_ok=True)

graph = build_graph()

SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
)


@app.post("/resumes/upload")
async def upload_resumes(files: list[UploadFile] = File(...)):
    uploaded = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue

        temp_name = f"{uuid.uuid4()}_{file.filename}"
        temp_path = TMP_DIR / temp_name

        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        uploaded.append(str(temp_path))

    if not uploaded:
        return JSONResponse(
            status_code=400,
            content={"error": "No valid PDF files uploaded"},
        )

    async with stdio_client(SERVER_PARAMS) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            result = await graph.ainvoke({
                "root_path": str(TMP_DIR),
                "mcp_session": session,
            })

    return {
        "uploaded": uploaded,
        "routed": result.get("results", []),
        "skipped": result.get("skipped", []),
    }
