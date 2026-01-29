"""
Quick script to start the FastAPI backend server
Run this before testing the agent
"""
import subprocess
import sys
import os

print("=" * 60)
print("Starting NeuroMCP Backend Server")
print("=" * 60)
print()
print("Server will start on: http://localhost:8000")
print("Press Ctrl+C to stop the server")
print()
print("Once started, you can:")
print("  1. Run the Streamlit UI: streamlit run streamlit_app.py")
print("  2. Test with the backend: python test_backend.py")
print()
print("=" * 60)
print()

# Start uvicorn server
try:
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--port", "8000",
        "--host", "0.0.0.0"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
except Exception as e:
    print(f"Error starting server: {e}")
    print("\nMake sure uvicorn is installed: pip install uvicorn")
