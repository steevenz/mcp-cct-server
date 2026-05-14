#!/usr/bin/env python3
"""
CCT Remote Handshake CLI
Automates the process of connecting a local IDE to a remote CCT server.

Usage:
    python scripts/setup/local/connect_mcp.py
"""
import json
import hmac
import hashlib
import secrets
import requests
import os
from pathlib import Path

def do_handshake():
    print("\n=== CCT REMOTE HANDSHAKE CLI ===")
    
    server_url = input("Remote Server URL (e.g. https://mcp.steevenz.com): ").strip().rstrip('/')
    if not server_url:
        print("Error: Server URL is required.")
        return

    bootstrap_key = input("Bootstrap API Key: ").strip()
    if not bootstrap_key:
        print("Error: Bootstrap Key is required.")
        return

    ide_name = input("IDE/Instance Name (e.g. cursor, vscode, gemini-cli) [gemini-cli]: ").strip() or "gemini-cli"
    
    client_nonce = secrets.token_hex(8)
    
    try:
        # 1. Init
        print(f"[*] Initializing handshake for '{ide_name}'...")
        init_resp = requests.post(
            f"{server_url}/cognitive-api/v1/auth/handshake/init",
            headers={"X-BOOTSTRAP-KEY": bootstrap_key},
            json={"llm_instance_id": ide_name, "client_nonce": client_nonce},
            timeout=10
        )
        init_resp.raise_for_status()
        init_data = init_resp.json()
        
        handshake_id = init_data["data"]["handshake_id"]
        challenge = init_data["data"]["challenge"]
        
        # 2. Proof
        message = f"{handshake_id}:{ide_name}:{challenge}"
        proof = hmac.new(
            bootstrap_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # 3. Complete
        print("[*] Completing handshake...")
        complete_resp = requests.post(
            f"{server_url}/cognitive-api/v1/auth/handshake/complete",
            headers={"X-BOOTSTRAP-KEY": bootstrap_key},
            json={"handshake_id": handshake_id, "client_proof": proof},
            timeout=10
        )
        complete_resp.raise_for_status()
        complete_data = complete_resp.json()
        
        api_key = complete_data["data"]["api_key"]
        mcp_url = f"{server_url}/cct"
        
        print("\n" + "="*40)
        print("🎉 HANDSHAKE SUCCESSFUL!")
        print("="*40)
        
        print("\n[Gemini CLI Command]")
        print(f'gemini mcp add --transport sse creative-critical-thinking {mcp_url} --header "X-API-KEY: {api_key}" --header "X-IDE-ORIGIN: {ide_name}"')
        
        mcp_config = {
            "url": mcp_url,
            "headers": {
                "X-API-KEY": api_key,
                "X-IDE-ORIGIN": ide_name
            }
        }
        
        print("\n[MCP JSON Config]")
        print(json.dumps(mcp_config, indent=2))
        
        print("\nNext Steps:")
        print(1, "Copy the Gemini CLI command above to add the server.")
        print(2, "Or copy the JSON config to your IDE's MCP settings.")
        
    except Exception as e:
        print(f"\n❌ Handshake Failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    do_handshake()
