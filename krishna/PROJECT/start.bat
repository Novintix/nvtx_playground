@echo off
echo ======================================
echo Multi-Agent MCP System - Quick Start
echo ======================================
echo.

echo [1/3] Checking Python dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo Error installing dependencies!
    pause
    exit /b 1
)

echo.
echo [2/3] Make sure your MCP servers are running:
echo   - Notion MCP: http://127.0.0.1:8001/mcp
echo   - Filesystem MCP: http://127.0.0.1:8002/mcp
echo   - Any dynamic MCPs in mcp_endpoints.json
echo.

echo [3/3] Starting Web UI Server...
echo.
echo ^>^> Opening browser at http://localhost:8000
echo.
start http://localhost:8000
python web_server.py
