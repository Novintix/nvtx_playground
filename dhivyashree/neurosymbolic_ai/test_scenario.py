import requests
from datetime import datetime
import json
import time

# Wait for server to start
print("Waiting for server to start...")
time.sleep(3)

url = "http://127.0.0.1:8000/analyze"

# Scenario: Database goes down, causing API failures 2 minutes later
payload = {
    "logs": [
        {"timestamp": "2023-10-27T10:00:00", "level": "INFO", "service": "db-service", "message": "Database connection initiated"},
        {"timestamp": "2023-10-27T10:05:00", "level": "ERROR", "service": "db-service", "message": "Database Connection Failed: Timeout"},
        {"timestamp": "2023-10-27T10:07:00", "level": "ERROR", "service": "api-service", "message": "API Error 500: Unable to fetch user data"}
    ],
    "alerts": []
}

try:
    print(f"Sending POST request to {url}...")
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Request failed: {e}")
