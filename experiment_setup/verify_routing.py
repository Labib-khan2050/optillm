
import threading
import time
import requests
from flask import Flask, request, jsonify
import sys
import os

# Add the parent directory to sys.path to import optillm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Upstream Provider (e.g. LiteLLM)
mock_app = Flask("mock_upstream")
received_auth = None

@mock_app.route("/v1/chat/completions", methods=["POST"])
def mock_completions():
    global received_auth
    received_auth = request.headers.get("Authorization")
    return jsonify({
        "choices": [{
            "message": {"role": "assistant", "content": "Mock Response"},
            "finish_reason": "stop",
            "index": 0
        }],
        "usage": {"completion_tokens": 10}
    })

def run_mock_server():
    mock_app.run(port=9000, use_reloader=False)

# Start Mock Server
mock_thread = threading.Thread(target=run_mock_server, daemon=True)
mock_thread.start()
print("Started Mock Server on port 9000")

# Import OptiLLM App
# We need to set some defaults since we aren't running main()
from optillm.server import app as optillm_app, server_config

server_config['model'] = 'gpt-3.5-turbo'
# Ensure no default base_url to prove dynamic routing works
server_config['base_url'] = "" 
server_config['optillm_api_key'] = "" 

def run_optillm_server():
    optillm_app.run(port=8001, use_reloader=False)

# Start OptiLLM Server
optillm_thread = threading.Thread(target=run_optillm_server, daemon=True)
optillm_thread.start()
print("Started OptiLLM Server on port 8001")

# Wait for servers to start
time.sleep(2)

# Test Case 1: Dynamic Routing
print("\n--- Test 1: Dynamic Routing (key|url) ---")
target_url = "http://localhost:9000/v1"
api_key = "test-key-123"
bearer_token = f"{api_key}|{target_url}"

try:
    response = requests.post(
        "http://localhost:8001/v1/chat/completions",
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}]
        },
        headers={"Authorization": f"Bearer {bearer_token}"}
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200 and received_auth == f"Bearer {api_key}":
        print("SUCCESS: Request routed correctly with clean API key.")
    else:
        print(f"FAILURE: Status {response.status_code}, Received Auth: {received_auth}")
        exit(1)

except Exception as e:
    print(f"EXCEPTION: {e}")
    exit(1)

print("\n--- Verification Complete ---")
