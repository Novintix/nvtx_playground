@echo off
echo Starting Translation Frontend...
echo.
echo The frontend will run on http://localhost:8080
echo.
cd /d "%~dp0Translation_Module\frontend"
call bun install 2>nul
call bun run dev
