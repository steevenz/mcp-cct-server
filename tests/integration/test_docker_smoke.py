import os
import sys
import time
import hmac
import hashlib
import requests

BASE_URL = "http://127.0.0.1:8010"
BOOTSTRAP_KEY = "local-docker-key"

def smoke_test():
    print(f"Starting smoke test against {BASE_URL}...")
    
    # 1. Wait for health check
    for i in range(10):
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                print("Server is healthy!")
                break
        except:
            pass
        print(f"Waiting for server... ({i+1}/10)")
        time.sleep(2)
    else:
        print("Error: Server failed health check.")
        sys.exit(1)

    # 2. Test Handshake Init
    print("Testing handshake/init...")
    payload = {"llm_instance_id": "smoke-tester", "client_nonce": "nonce123"}
    headers = {"X-BOOTSTRAP-KEY": BOOTSTRAP_KEY, "Content-Type": "application/json"}
    resp = requests.post(f"{BASE_URL}/cognitive-api/v1/auth/handshake/init", json=payload, headers=headers)
    
    if resp.status_code != 200:
        print(f"Handshake Init Failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    
    data = resp.json().get("data", {})
    handshake_id = data.get("handshake_id")
    challenge = data.get("challenge")
    print(f"Handshake Init OK: id={handshake_id}")

    # 3. Test Handshake Complete
    print("Testing handshake/complete...")
    material = f"{handshake_id}:smoke-tester:{challenge}".encode("utf-8")
    proof = hmac.new(BOOTSTRAP_KEY.encode("utf-8"), material, hashlib.sha256).hexdigest()
    
    complete_payload = {"handshake_id": handshake_id, "client_proof": proof}
    resp = requests.post(f"{BASE_URL}/cognitive-api/v1/auth/handshake/complete", json=complete_payload, headers=headers)
    
    if resp.status_code != 200:
        print(f"Handshake Complete Failed: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    session_key = resp.json().get("data", {}).get("api_key")
    print(f"Handshake Complete OK: key issued.")

    # 4. Test Sync with Issued Key
    print("Testing sync with issued key...")
    sync_headers = {"X-API-KEY": session_key, "Content-Type": "application/json"}
    sync_body = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
    resp = requests.post(f"{BASE_URL}/cognitive-api/v1/sync", json=sync_body, headers=sync_headers)
    
    if resp.status_code == 200 and resp.json().get("result") == {}:
        print("Sync OK!")
    else:
        print(f"Sync Failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    # 5. Test Key Rotation
    print("Testing key rotation...")
    rotate_headers = {"X-API-KEY": session_key, "Content-Type": "application/json"}
    resp = requests.post(f"{BASE_URL}/cognitive-api/v1/auth/keys/rotate", json={}, headers=rotate_headers)
    
    if resp.status_code == 200:
        new_key = resp.json().get("data", {}).get("api_key")
        print("Rotation OK!")
        
        # Verify old key is revoked
        print("Verifying old key revocation...")
        resp = requests.post(f"{BASE_URL}/cognitive-api/v1/sync", json=sync_body, headers=sync_headers)
        if resp.status_code in (401, 403):
            print("Revocation Verified!")
        else:
            print(f"Revocation Failed: {resp.status_code} {resp.text}")
            sys.exit(1)
    else:
        print(f"Rotation Failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    print("\nALL SMOKE TESTS PASSED!")

if __name__ == "__main__":
    smoke_test()
