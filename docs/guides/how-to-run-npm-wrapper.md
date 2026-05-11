# Guide: Run CCT MCP via npm/npx (STDIO Wrapper)

This guide explains how to run the Node.js wrapper at:
- `scripts/server/js/index.js`

The wrapper is designed for **IDE MCP STDIO** usage while allowing **multiple IDEs** to share one underlying CCT Python server.

## Why this wrapper exists
MCP clients that use STDIO treat **stdout as the protocol wire**. If human logs print to stdout, most IDE MCP clients will crash.

This wrapper guarantees:
- **All setup/status logs go to stderr**
- **stdout remains reserved for MCP JSON-RPC** (proxy responses only)
- **Multi-IDE sharing** by forwarding requests to one shared HTTP/SSE backend

---

## Prerequisites & system requirements

### Supported OS
- Windows 10/11
- macOS
- Linux

### Required software
- Node.js **18+** (for consistent runtime behavior)
- Python **3.8+** (consistent with existing setup scripts)
- A working C/C++ toolchain is not required for typical installs, but some Python packages may download wheels.

### Repo prerequisites
- You must run inside a checked-out repo:

```bash
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server
```

---

## Environment configuration requirements

The Python server loads configuration from `.env`.

Minimum required:
- `CCT_BOOTSTRAP_API_KEY` must be set (the server fails startup if missing)

Recommended for IDE usage:
- Set `CCT_BOOTSTRAP_API_KEY` directly in the IDE MCP server `env` block (more deterministic than relying on global machine env).
- Set a dedicated backend bind target to avoid accidentally reusing an older server already running on `8000/8001`:
  - `CCT_HOST=127.0.0.1`
  - `CCT_PORT=8010`

Recommended:
- Copy `.env.example` to `.env` and adjust values.

```bash
# macOS/Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Notes:
- The wrapper forces `CCT_TRANSPORT=stdio` for the child process.
- If you set `CCT_TRANSPORT` in `.env`, the wrapper still forces STDIO for IDE safety.

---

## Dependency installation (automatic)

The wrapper uses a project-local venv directory named `venv/`.

On first run, if `venv/` does not exist, it will synchronously execute:
- `python -m venv venv`
- `venv python -m pip install -r requirements.txt`

All output from these setup steps is redirected to `stderr`.

---

## Run with npm (local development)

From the project root:

```bash
npm run cct-mcp
```

Alternative alias:

```bash
npm run cct-server
```

---

## Run with npx (recommended for IDE MCP)

### 1) Run from anywhere (explicit package path)

Windows PowerShell:

```powershell
npx --yes --package "c:\Users\steevenz\MCP\mcp-cct-server" cct-mcp
```

macOS/Linux:

```bash
npx --yes --package /absolute/path/to/mcp-cct-server cct-mcp
```

### 2) Run from repo root (local package)

```bash
npx --yes --package . cct-mcp
```

Alias:

```bash
npx --yes --package . cct-server
```

---

## Command-line arguments and options

### Wrapper CLI flags
- No custom CLI flags are implemented.
- Any extra args are ignored by the wrapper.

### Useful environment variables
- `PYTHON`: if set, wrapper uses this interpreter for initial venv creation.
  - Example:

```bash
# macOS/Linux
export PYTHON=/usr/bin/python3

# Windows PowerShell
$env:PYTHON = "C:\Python312\python.exe"
```

---

## Expected output and behavior

### Expected behavior
- Wrapper prints setup/status logs to **stderr**.
- Wrapper starts (or reuses) a **shared HTTP/SSE** CCT server in the background.
- Wrapper acts as a **STDIO JSON-RPC proxy**: each IDE session gets its own wrapper process, but all wrappers talk to the same shared backend server.

### What you should see
You should see a log line similar to:

```text
Launching standard STDIO transport...
```

You may see Uvicorn bind logs (server backend) in **stderr**, but MCP protocol messages must only appear on **stdout**.

```text
Uvicorn running on http://0.0.0.0:8000
```

If MCP JSON appears in stderr or human logs appear in stdout, the IDE MCP client may crash.

---

## Verification steps

### 1) Verify STDIO proxy mode
Run:

```bash
npx --yes --package . cct-mcp
```

Confirm the output includes:
- JSON-RPC responses on stdout for a probe (e.g. `ping`)

### 2) Verify shared server is running (optional)
In another terminal, verify the shared server is listening on the configured port (default: `8001`):

Windows:

```powershell
netstat -ano | findstr :8001
```

macOS/Linux:

```bash
lsof -i :8001 | cat
```

### 3) Verify shared multi-IDE behavior
- Start one IDE session and keep it open.
- Start a second IDE session using the same MCP config.
- Both should work without starting duplicate backends.

---

## Example use cases

### Use case 1: Trae / Cursor / Claude Desktop MCP server
Use the IDE MCP config entry:

```json
{
  "mcpServers": {
    "creative-critical-thinking": {
      "command": "npx",
      "args": ["--yes", "--package", "c:/Users/steevenz/MCP/mcp-cct-server", "cct-mcp"],
      "env": {
        "CCT_TRANSPORT": "stdio",
        "CCT_HOST": "127.0.0.1",
        "CCT_PORT": "8010",
        "CCT_BOOTSTRAP_API_KEY": "<YOUR_CCT_BOOTSTRAP_API_KEY>"
      }
    }
  }
}
```

### Use case 2: Local smoke test
Use npm script:

```bash
npm run cct-mcp
```

---

## Troubleshooting

### Problem: `No system Python interpreter found for initial bootstrap.`
Cause:
- Wrapper can’t find `python`/`python3`/`py`.

Fix:
- Install Python and ensure it’s on PATH, or set `PYTHON` env var.

### Problem: `pip install -r requirements.txt` takes very long
Cause:
- Large dependency set (ML + web + MCP packages).

Fix:
- Let the first install complete once.
- Ensure you have stable internet.

### Problem: Wrapper starts Uvicorn / binds ports
Cause:
- Transport is not being forced to STDIO.

Fix:
- Ensure you are running via wrapper (`cct-mcp`), not `python src/main.py`.
- If you still see bind logs, verify your IDE is using the command-based MCP server entry.

### Problem: IDE crashes on connect
Cause:
- Something printed human logs to stdout.

Fix:
- Ensure your wrapper logs go to stderr.
- Ensure no extra shell wrappers echo to stdout.

### Problem: Tool name violates `^[a-zA-Z0-9_-]{1,64}$`
Symptom:
- IDE reports errors like `tool name mcp_Creative Critical Thinking_thinking violates ...`

Cause:
- Some IDEs derive tool identifiers from the MCP server name in config, e.g. `mcp_<serverName>_thinking`.
- If your MCP server key contains spaces/punctuation, the derived tool name becomes invalid.

Fix:
- Rename the MCP server key to a safe identifier (no spaces), e.g. `cct_mcp` or `Creative_Critical_Thinking`.

### Problem: API key error during startup
Cause:
- `CCT_BOOTSTRAP_API_KEY` missing.

Fix:
- Set it in `.env` (recommended) or process environment.

---

## Related
- Setup overview: `docs/guides/how-to-setup.md`
- Multi-agent server management: `docs/guides/how-to-manage-server.md`
