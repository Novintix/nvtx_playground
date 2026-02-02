"""
Test script to verify improved error handling for API quota errors.
"""

import requests
import json

API_URL = "http://localhost:8002/query"

def test_query(query_text):
    """Test a query and display the response."""
    print(f"\n{'='*60}")
    print(f"Testing Query: {query_text}")
    print('='*60)
    
    try:
        response = requests.post(
            API_URL,
            json={"query": query_text},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Status: {data.get('status', 'unknown')}")
            print(f"📊 Source: {data.get('source', 'unknown')}")
            print(f"\n💬 Answer:\n{data.get('answer', 'No answer')}")
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to query service")
        print("Make sure the service is running: python query_service.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    print("\n🧪 Testing Invoice Intelligence System")
    print("=" * 60)
    
    # Test MongoDB query
    test_query("How many candidates know Python?")
    
    # Wait for user input before next query
    input("\n\nPress Enter to test another query (or Ctrl+C to exit)...")
    
    # Test RAG query
    test_query("What is the total invoice amount?")
    
    print("\n\n✅ Testing complete!")
    print("\nNote: If you see quota errors, wait 30 seconds and try again.")
