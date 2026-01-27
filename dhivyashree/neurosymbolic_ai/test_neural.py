import requests
from datetime import datetime
import json
import time

url = "http://127.0.0.1:8000/analyze"

# Scenario: No clear rule match, just random noisy logs
payload = {
    "logs": [
        {"timestamp": "2023-10-27T10:00:00", "level": "INFO", "service": "auth-service", "message": "User login successful"},
        {"timestamp": "2023-10-27T10:01:00", "level": "WARN", "service": "auth-service", "message": "Token expiry warning"},
        {"timestamp": "2023-10-27T10:02:00", "level": "WARN", "service": "auth-service", "message": "Token expiry warning"},
        {"timestamp": "2023-10-27T10:03:00", "level": "INFO", "service": "payment-service", "message": "Transaction started"},
        {"timestamp": "2023-10-27T10:04:00", "level": "ERROR", "service": "payment-service", "message": "Payment gateway timeout 504"},
        {"timestamp": "2023-10-27T10:04:05", "level": "ERROR", "service": "payment-service", "message": "Payment gateway timeout 504"},
        {"timestamp": "2023-10-27T10:04:10", "level": "ERROR", "service": "payment-service", "message": "Payment gateway timeout 504"}
    ],
    "alerts": []
}

try:
    print(f"Sending Neural Fallback POST request to {url}...")
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Request failed: {e}")
