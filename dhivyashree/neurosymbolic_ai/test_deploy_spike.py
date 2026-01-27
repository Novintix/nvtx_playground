import requests
from datetime import datetime
import json
import time

url = "http://127.0.0.1:8000/analyze"

# Scenario: Deployment triggers CPU spike
payload = {
    "logs": [
        {"timestamp": "2023-11-01T14:00:00", "level": "INFO", "service": "deploy-service", "message": "Starting rolling update for version v2.5"},
        {"timestamp": "2023-11-01T14:02:00", "level": "WARN", "service": "compute-service", "message": "CPU utilization reached 85%"},
        {"timestamp": "2023-11-01T14:03:00", "level": "ERROR", "service": "compute-service", "message": "High CPU usage spike detected: 99%"}
    ],
    "alerts": []
}

try:
    print(f"Sending Deployment Spike POST request to {url}...")
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Request failed: {e}")
