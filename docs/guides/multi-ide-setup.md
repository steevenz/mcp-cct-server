# Multi-IDE Setup Guide

**Version**: 1.1.0 | **Updated**: 2026-05-09

---

This guide covers setting up the CCT MCP server for concurrent access from multiple IDEs and LLM providers.

---

## 1. Prerequisites

- Node.js >= 18
- Python 3.10+
- `.env` file with `CCT_BOOTSTRAP_API_KEY` configured

---

## 2. Quick Start

```bash
# Start the shared server (default SSE on port 8001)
npm run cct-server

# Or start for specific IDE
npm run cct-server:vscode
npm run cct-server:cursor
npm run cct-server:jetbrains
npm run cct-server:windsurf
npm run cct-server:copilot
```

The first instance will start the Python server. Subsequent instances will auto-detect and connect to the running server.

---

## 3. Per-IDE Configuration

### 3.1 VSCode (STDIO)

**Launch:**
```bash
npm run cct-server:vscode
```

**MCP Config (`mcp_client_stdio.json`):**
```json
{
  "mcpServers": {
    "cct_mcp": {
      "command": "npx",
      "args": [
        "--yes", "--package", "c:/Users/steevenz/MCP/mcp-cct-server",
        "cct-mcp", "--ide", "vscode"
      ],
      "env": {
        "CCT_IDE": "vscode",
        "CCT_TRANSPORT": "stdio",
        "CCT_PORT": "8010"
      }
    }
  }
}
```

### 3.2 JetBrains (SSE)

**Launch:**
```bash
npm run cct-server:jetbrains
```

**MCP Config (`mcp_client_sse.json`):**
```json
{
  "mcpServers": {
    "CCT": {
      "url": "http://localhost:8001/cognitive-api/v1/sync",
      "headers": {
        "X-API-KEY": "cct-secret-token-2026",
        "X-IDE-ORIGIN": "jetbrains"
      }
    }
  }
}
```

### 3.3 Cursor (STDIO)

```bash
npm run cct-server:cursor
```

Uses port 8011 with `X-IDE-ORIGIN: cursor`.

### 3.4 GitHub Copilot (SSE)

```bash
npm run cct-server:copilot
```

Uses port 8003 with `X-IDE-ORIGIN: github_copilot`.

### 3.5 Windsurf (SSE)

```bash
npm run cct-server:windsurf
```

Uses port 8002 with `X-IDE-ORIGIN: windsurf`.

---

## 4. Custom Launch

Use CLI arguments for custom configurations:

```bash
# Direct
node ./scripts/server/js/index.js --ide my-ide --transport sse --port 8001

# Via npm with overrides
CCT_IDE=custom-ide npm run cct-server

# Environment variables
set CCT_IDE=my-ide
set CCT_TRANSPORT=sse
set CCT_PORT=8001
npm run cct-server
```

---

## 5. Verifying Connections

```bash
# List all connected LLMs
curl http://localhost:8001/status/llms

# Get details for specific LLM
curl http://localhost:8001/status/llm/vscode

# Check server health
curl http://localhost:8001/status
```

**Expected output (`/status/llms`):**
```json
{
  "llms": {
    "vscode": {
      "auth_type": "issued_api_key",
      "scopes": ["mcp:sync", "mcp:sse", "auth:rotate"],
      "first_seen": "2026-05-09T04:00:00",
      "last_active": "2026-05-09T04:05:00"
    },
    "jetbrains": {
      "auth_type": "issued_api_key",
      "scopes": ["mcp:sync", "mcp:sse", "auth:rotate"],
      "first_seen": "2026-05-09T04:01:00",
      "last_active": "2026-05-09T04:06:00"
    }
  },
  "total": 2
}
```

---

## 6. Connection Registry

The server maintains a live registry at `database/config/mcp_server_registry.json`:

```bash
cat database/config/mcp_server_registry.json
```

This file is updated automatically when IDEs connect/disconnect.

---

## 7. Running Behind Different Ports

While the default setup uses a single port (8001), you can run isolated instances:

```bash
# Isolated instance on port 9001
CCT_PORT=9001 node ./scripts/server/js/index.js --ide isolated --port 9001
```

This creates a completely separate server with its own connection registry and memory database.

---

## 8. Troubleshooting

### 8.1 "Port already in use"

```bash
# Check what's running on the port
netstat -ano | findstr :8001

# Kill the process
taskkill /PID <pid> /F
```

### 8.2 Connections not showing in registry

```bash
# Verify the registry file is writable
dir database\config\mcp_server_registry.json

# Check server logs for auth errors
curl http://localhost:8001/status
```

### 8.3 Session isolation not working

Ensure each IDE sends a unique `X-IDE-ORIGIN` header. Duplicate headers cause session sharing.

### 8.4 STDIO proxy fails to connect

```bash
# Verify the Python server is running
curl http://localhost:8001/health

# Start server explicitly
npm run cct-server
```
