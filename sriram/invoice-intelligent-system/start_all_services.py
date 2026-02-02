"""
Start All Services Script
Launches MCP Server, Ingestion Service, and Query Service
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_port(port):
    """Check if a port is available."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0  # True if port is available

def main():
    print("=" * 70)
    print("🚀 Starting Invoice Intelligence System")
    print("=" * 70)
    
    # Check if .env exists
    if not Path(".env").exists():
        print("\n❌ ERROR: .env file not found!")
        print("Please create .env file with required configuration:")
        print("  GOOGLE_API_KEY=your_key_here")
        print("  MONGODB_URI=your_mongodb_uri (optional)")
        sys.exit(1)
    
    # Check ports
    ports = {
        8000: "MCP Server",
        8001: "Ingestion Service",
        8002: "Query Service"
    }
    
    print("\n📊 Checking ports...")
    for port, service in ports.items():
        if not check_port(port):
            print(f"❌ Port {port} ({service}) is already in use!")
            print(f"   Please stop the service or change the port in config.py")
            sys.exit(1)
        else:
            print(f"✅ Port {port} ({service}) is available")
    
    processes = []
    
    try:
        # Start MCP Server
        print("\n🔧 Starting MCP Server (Port 8000)...")
        mcp_process = subprocess.Popen(
            [sys.executable, "mcp_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(("MCP Server", mcp_process))
        time.sleep(3)
        
        # Start Ingestion Service
        print("📤 Starting Ingestion Service (Port 8001)...")
        api_process = subprocess.Popen(
            [sys.executable, "api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(("Ingestion Service", api_process))
        time.sleep(3)
        
        # Start Query Service
        print("🔍 Starting Query Service (Port 8002)...")
        query_process = subprocess.Popen(
            [sys.executable, "query_service.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(("Query Service", query_process))
        time.sleep(3)
        
        print("\n" + "=" * 70)
        print("✅ All Services Started Successfully!")
        print("=" * 70)
        print("\n📍 Service URLs:")
        print("   • MCP Server:        http://localhost:8000")
        print("   • Ingestion Service: http://localhost:8001")
        print("   • Query Service:     http://localhost:8002")
        print("\n📖 Usage:")
        print("   1. Upload documents at http://localhost:8001")
        print("   2. Query all data at http://localhost:8002")
        print("\n⚠️  Press Ctrl+C to stop all services")
        print("=" * 70)
        
        # Keep running
        while True:
            time.sleep(1)
            # Check if any process died
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\n❌ {name} stopped unexpectedly!")
                    raise KeyboardInterrupt
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all services...")
        for name, proc in processes:
            print(f"   Stopping {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("✅ All services stopped")
        print("=" * 70)

if __name__ == "__main__":
    main()
