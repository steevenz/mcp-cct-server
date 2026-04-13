
import asyncio
import json
import requests
import time

def test_thinking():
    print("Testing 'thinking' tool...")
    url = "http://localhost:8001/messages" # Updated to port 8001

    payload = {
        "method": "tools/call",
        "params": {
            "name": "thinking",
            "arguments": {
                "problem_statement": "How to design a sustainable city on Mars?",
                "profile": "creative"
            }
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Note: This requires the server to be running in SSE mode
    # python -m src.main --transport sse
    test_thinking()
