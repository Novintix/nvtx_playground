"""
Start all MCP servers in background.
"""

import subprocess
import sys
import time
from pathlib import Path

def start_server(script_name, port):
    """Start an MCP server."""
    script_path = Path("mcp_servers") / script_name
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1)
    return process

if __name__ == "__main__":
    servers = [
        ("ingestion_server.py", 8001),
        ("ocr_server.py", 8002),
        ("structuring_server.py", 8003),
        ("validation_server.py", 8004)
    ]
    
    processes = []
    
    for script, port in servers:
        process = start_server(script, port)
        processes.append(process)
    print('connected')
    try:
        for process in processes:
            process.wait()
        print('sucess')
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
