@echo off
echo Starting Translation Backend Server...
echo.
echo The backend will run on http://localhost:8000
echo.
cd /d "%~dp0backend"
call pip install -r requirements.txt 2>nul
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
