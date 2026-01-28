import requests
from datetime import datetime
import json
import time

url = "http://127.0.0.1:8000/analyze"

# Scenario: User provided single log entry
payload = {
  "logs": [
    {
      "timestamp": "2026-01-27T12:42:58.684Z",
      "level": "INFO",
      "service": "test-service",
      "message": "This is a single log entry for testing clustering"
    }
  ],
  "alerts": []
}

try:
    print(f"Sending Single Log POST request to {url}...")
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Request failed: {e}")
