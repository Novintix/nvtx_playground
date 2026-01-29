import requests
import json

# Test the backend endpoints
BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Testing NeuroMCP Agent Backend")
print("=" * 60)

# Test 1: Root endpoint
print("\n1. Testing root endpoint...")
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"✅ Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Agent run endpoint
print("\n2. Testing /agent/run endpoint...")
try:
    payload = {
        "user_request": "Create a calendar event for team meeting tomorrow at 2pm"
    }
    response = requests.post(f"{BASE_URL}/agent/run", json=payload)
    print(f"✅ Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Google OAuth status
print("\n3. Checking Google OAuth status...")
try:
    with open(".tokens.json", "r") as f:
        tokens = json.load(f)
        if "google" in tokens:
            print("✅ Google OAuth connected")
            print(f"   Access token: {tokens['google']['access_token'][:30]}...")
        else:
            print("❌ Google OAuth not connected")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Backend test complete!")
print("=" * 60)
