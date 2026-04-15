# Guide: How to Setup CCT MCP Server

This guide provides comprehensive step-by-step instructions to get the **Creative Critical Thinking (CCT)** server running and integrated into your development workflow across different platforms and deployment modes.

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Quick Setup](#2-quick-setup)
3. [Platform-Specific Setup](#3-platform-specific-setup)
4. [Transport Modes](#4-transport-modes)
5. [IDE Integration](#5-ide-integration)
6. [Multi-Agent/Multi-IDE Setup](#6-multi-agentmulti-ide-setup)
7. [Service Installation](#7-service-installation)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites

- **Python 3.8 or higher** installed (minimum version enforced by setup scripts)
- **Git** installed
- (Recommended) An API key for your preferred LLM provider:
  - Google Gemini 1.5 Flash (via [Google AI Studio](https://aistudio.google.com/))
  - OpenAI GPT-4
  - Anthropic Claude
  - Ollama (local models)

---

## 2. Quick Setup

### Automated Setup (Recommended)

The CCT project provides automated setup scripts that handle all dependencies, environment configuration, and service installation.

#### Windows
```powershell
# Clone the repository
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server

# Run automated setup
.\scripts\setup\setup.bat

# Or with PowerShell
.\scripts\setup\setup.ps1

# Available options:
# --install-service  Install as Windows Service
# --force            Force recreate .venv and reset database
# --skip-deps        Skip dependency installation
# --clean-reqs       Clean and reinstall requirements
# --multi-agent      Configure for multi-agent mode
# --port 8001        Set custom port
```

#### Linux/macOS
```bash
# Clone the repository
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server

# Run automated setup
chmod +x scripts/setup/setup.sh
./scripts/setup/setup.sh

# Available options:
# --install-service  Install as systemd service
# --force            Force recreate .venv and reset database
# --skip-deps        Skip dependency installation
# --clean-reqs       Clean and reinstall requirements
# --multi-agent      Configure for multi-agent mode
# --port 8001        Set custom port
```

#### Python Cross-Platform
```bash
# Clone the repository
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server

# Run Python setup script
python scripts/server/setup.py

# Available options:
# --force            Force recreate .venv and reset database
# --skip-deps        Skip dependency installation
# --run              Start server after setup
# --multi-agent      Configure for multi-agent mode
# --port 8001        Set custom port
```

### Manual Setup

If you prefer manual setup:

```bash
# Clone the repository
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server

# Create a virtual environment
python -m venv .venv

# Activate the venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
# (See Configuration section below)
```

---

## 3. Platform-Specific Setup

### Windows Setup

**Requirements:**
- Windows 10/11 or Windows Server 2019+
- PowerShell 5.1+
- Python 3.8+

**Setup Steps:**
1. Open PowerShell as Administrator (for service installation)
2. Navigate to project directory
3. Run: `.\scripts\setup\setup.bat --install-service`

**Windows Service Management:**
```powershell
# Install service with auto-startup on boot (recommended)
.\scripts\setup\setup.bat --install-service

# Or use the dedicated service setup script
.\scripts\setup\services\windows\setup.ps1

# Install with manual startup (no auto-start on boot)
.\scripts\setup\services\windows\setup.ps1 -StartupType manual

# Install but don't start immediately
.\scripts\setup\services\windows\setup.ps1 -NoStart

# Configure auto-startup after install
sc config CCTMCPServer start= auto

# Start service manually
sc start CCTMCPServer

# Stop service
sc stop CCTMCPServer

# Check status
sc query CCTMCPServer

# Remove service (requires admin)
python scripts\setup\services\windows\service.py remove
```

> [!NOTE]
> **Auto-Startup Feature**: By default, the service is configured to start automatically on Windows boot. Use `-StartupType manual` if you prefer to start the service manually.

### Linux/macOS Setup

**Requirements:**
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+) or macOS 10.15+
- Python 3.8+
- systemd (for service installation)

**Setup Steps:**
1. Open terminal
2. Navigate to project directory
3. Run: `./scripts/setup/setup.sh --install-service`

**Systemd Service Management:**
```bash
# Install service (requires sudo)
sudo ./scripts/setup/setup.sh --install-service

# Start service
sudo systemctl start cct-cognitive-os

# Stop service
sudo systemctl stop cct-cognitive-os

# Check status
sudo systemctl status cct-cognitive-os

# Enable auto-start
sudo systemctl enable cct-cognitive-os

# View logs
sudo journalctl -u cct-cognitive-os -f
```

---

## 4. Transport Modes

The CCT MCP Server supports two transport modes:

### stdio Transport (Default)
**Best for:** IDE integration, direct command-line usage

**Configuration:**
```env
CCT_TRANSPORT=stdio
```

**Usage:**
- IDEs connect directly via stdin/stdout
- No network configuration needed
- Lower latency
- Single connection per IDE instance

### SSE Transport (Server-Sent Events)
**Best for:** Multi-agent setups, HTTP clients, background services

**Configuration:**
```env
CCT_TRANSPORT=sse
CCT_HOST=0.0.0.0
CCT_PORT=8000
```

**Usage:**
- Multiple IDEs/agents can connect simultaneously
- HTTP-based communication
- Requires network configuration
- Supports health checks and monitoring

**HTTP Endpoints:**
- `GET /health` - Quick liveness check
- `GET /status` - Detailed telemetry (uptime, LLM provider, active sessions)
- `GET /cognitive-api/v1/sync` - SSE endpoint for MCP communication

---

## 5. IDE Integration

### Windsurf / Verdent.ai

#### stdio Mode (Single IDE)
Add to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "command": "C:/PATH/TO/mcp-cct-server/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/PATH/TO/mcp-cct-server/src/main.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        "CCT_TRANSPORT": "stdio",
        "CCT_LOG_LEVEL": "INFO",
        "CCT_LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

#### SSE Mode (Multi-Agent/IDE)
Add to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "url": "http://localhost:8000/cognitive-api/v1/sync",
      "env": {
        "CCT_LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

### Claude Desktop

#### stdio Mode
Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "command": "/PATH/TO/mcp-cct-server/.venv/bin/python",
      "args": [
        "-u",
        "/PATH/TO/mcp-cct-server/src/main.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        "CCT_TRANSPORT": "stdio",
        "CCT_LOG_LEVEL": "INFO",
        "CCT_LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

#### SSE Mode
```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "url": "http://localhost:8000/cognitive-api/v1/sync",
      "env": {
        "CCT_LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

### Cursor / Continue.dev

Similar configuration as Windsurf, using SSE mode for multi-agent setups.

---

## 6. Multi-Agent/Multi-IDE Setup

### Configuration for Multi-Agent Mode

**Option 1: Using Setup Scripts**
```bash
# Windows
.\scripts\setup\setup.bat --multi-agent --port 8001

# Linux/macOS
./scripts/setup/setup.sh --multi-agent --port 8001
```

**Option 2: Manual Configuration**
Edit `.env`:
```env
CCT_TRANSPORT=sse
CCT_HOST=0.0.0.0
CCT_PORT=8001
CCT_MAX_SESSIONS=128
```

### Starting the Multi-Agent Server

**Option 1: Using Server Manager**
```bash
# Windows
python scripts\server\manage.py start

# Linux/macOS
python scripts/server/manage.py start
```

**Option 2: Direct Execution**
```bash
# Activate venv first
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Start server
python src/main.py
```

### Connecting Multiple IDEs

Once the server is running in SSE mode, multiple IDEs can connect simultaneously:

**IDE 1 (Windsurf):**
```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "url": "http://localhost:8001/cognitive-api/v1/sync"
    }
  }
}
```

**IDE 2 (Cursor):**
```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "url": "http://localhost:8001/cognitive-api/v1/sync"
    }
  }
}
```

**IDE 3 (Claude Desktop):**
```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "url": "http://localhost:8001/cognitive-api/v1/sync"
    }
  }
}
```

### Server Management

**Check Server Status:**
```bash
# Windows
python scripts\server\manage.py status

# Linux/macOS
python scripts/server/manage.py status
```

**Stop Server:**
```bash
# Windows
python scripts\server\manage.py stop

# Linux/macOS
python scripts/server/manage.py stop
```

**View Logs:**
```bash
# Windows
python scripts\server\manage.py logs

# Linux/macOS
python scripts/server/manage.py logs
```

---

## 7. Service Installation

### Windows Service Installation

**Prerequisites:**
- Administrator privileges
- Python 3.8+
- pywin32 package (auto-installed by setup script)

**Installation:**
```powershell
# Run as Administrator
.\scripts\setup\setup.bat --install-service

# Or use the dedicated service setup with options:
.\scripts\setup\services\windows\setup.ps1                    # Auto-startup (default)
.\scripts\setup\services\windows\setup.ps1 -StartupType auto    # Explicit auto
.\scripts\setup\services\windows\setup.ps1 -StartupType manual # Manual start
.\scripts\setup\services\windows\setup.ps1 -NoStart         # Don't start now
```

**Service Management:**
```powershell
# Start service
sc start CCTMCPServer

# Stop service
sc stop CCTMCPServer

# Check status
sc query CCTMCPServer

# Configure auto-startup on boot
sc config CCTMCPServer start= auto

# View logs
Get-Content database\logs\cct_service.log -Tail 50
```

**Port Conflict Detection:**
The setup script now includes smart port management:
- Detects if port 8000 is already in use
- Automatically switches to available port (8001-9000)
- Updates `.env` configuration automatically
- Falls back to STDIO mode if no ports available

**Configuration for SSE Mode (Required for Service):**
```env
CCT_TRANSPORT=sse
CCT_HOST=0.0.0.0
CCT_PORT=8000
```

**IDE Configuration with Windows Service:**
```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "url": "http://localhost:8000/cognitive-api/v1/sync"
    }
  }
}
```

### Linux/macOS Service Installation

The CCT server provides unified service management scripts for both Linux (systemd) and macOS (launchd) platforms.

**Prerequisites:**
- sudo privileges
- Linux: systemd
- macOS: launchd
- Python 3.8+

#### Quick Installation

```bash
# Run the setup script with sudo
sudo bash scripts/setup/services/unix/setup.sh
```

This will:
- Detect your platform (Linux or macOS)
- Install the service (systemd on Linux, launchd on macOS)
- Start the service automatically
- Configure it to start on boot

#### Manual Service Management

**Using the Python Service Manager:**

```bash
# Install service
sudo python scripts/setup/services/unix/service.py install

# Start service
sudo python scripts/setup/services/unix/service.py start

# Stop service
sudo python scripts/setup/services/unix/service.py stop

# Restart service
sudo python scripts/setup/services/unix/service.py restart

# Check service status
sudo python scripts/setup/services/unix/service.py status

# Remove service
sudo python scripts/setup/services/unix/service.py remove
```

**Linux (systemd) Commands:**

```bash
# Start service
sudo systemctl start cct-cognitive-os

# Stop service
sudo systemctl stop cct-cognitive-os

# Check status
sudo systemctl status cct-cognitive-os

# Enable auto-start on boot
sudo systemctl enable cct-cognitive-os

# View logs
sudo journalctl -u cct-cognitive-os -f
```

**Service File Location:**
`/etc/systemd/system/cct-cognitive-os.service`

**macOS (launchd) Commands:**

```bash
# Start service
sudo launchctl start com.cct.cognitiveos

# Stop service
sudo launchctl stop com.cct.cognitiveos

# Check status
sudo launchctl list com.cct.cognitiveos

# View logs
tail -f database/logs/cct_service.log
```

**Plist File Location:**
`/Library/LaunchDaemons/com.cct.cognitiveos.plist`

#### Configuration for SSE Mode (Required for Service):

```env
CCT_TRANSPORT=sse
CCT_HOST=0.0.0.0
CCT_PORT=8001
```

#### IDE Configuration with Unix Service:

```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "url": "http://localhost:8001/cognitive-api/v1/sync"
    }
  }
}
```

---

## 8. Configuration

### Environment Variables (.env)

Copy the example environment file:
```bash
cp .env.example .env
```

**Key Configuration Options:**

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `CCT_TRANSPORT` | Transport mode | `stdio` | `stdio`, `sse` |
| `CCT_HOST` | Server host (SSE mode) | `0.0.0.0` | `0.0.0.0`, `127.0.0.1`, `localhost` |
| `CCT_PORT` | Server port (SSE mode) | `8000` | `1-65535` |
| `CCT_LLM_PROVIDER` | LLM provider | `gemini` | `gemini`, `openai`, `anthropic`, `ollama` |
| `CCT_DEFAULT_MODEL` | Default model | `claude-3-5-sonnet-20240620` | See pricing directory |
| `CCT_MAX_SESSIONS` | Max concurrent sessions | `128` | `1-100000` |
| `CCT_LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

**API Keys:**
```env
# Google Gemini
GEMINI_API_KEY=your_gemini_key

# OpenAI
OPENAI_API_KEY=your_openai_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
```

> [!TIP]
> **Guided Mode**: If you leave `CCT_LLM_PROVIDER` empty, the server will operate in **Guided Mode**, providing structured instructions instead of autonomous reasoning.

---

## 9. Troubleshooting

### Common Issues

**Issue: Server "hangs" or stays silent**
1. Check absolute paths in your IDE config
2. Verify you're using the venv python: `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Linux)
3. Check stderr logs in your IDE's MCP console
4. Verify API keys and internet connection

**Issue: Connection refused in SSE mode**
1. Ensure server is running: `python scripts/server/manage.py status`
2. Check firewall settings
3. Verify port is not already in use: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Linux)

**Issue: Windows Service won't start**
1. Run as Administrator
2. Check service logs: `database/logs/cct_service.log`
3. Verify pywin32 is installed: `pip install pywin32`
4. Restart service after config changes: `Restart-Service CCTMCPServer`
5. Check for port conflicts: `netstat -ano | findstr :8000` - if in use, service auto-switches to 8001+

**Issue: Port already in use (Error 10048)**
1. The setup script automatically detects port conflicts and switches to available port
2. Check which process uses the port: `netstat -ano | findstr :8000`
3. Kill conflicting process: `taskkill /F /PID <PID>`
4. Or manually configure different port in `.env`: `CCT_PORT=8001`

**Issue: Python version too old**
1. Setup scripts enforce minimum Python 3.8.0
2. Upgrade Python: https://www.python.org/downloads/

**Issue: Multi-agent connections failing**
1. Ensure server is in SSE mode: `CCT_TRANSPORT=sse`
2. Check host binding: `CCT_HOST=0.0.0.0` (not `127.0.0.1`)
3. Verify port is accessible from other machines

### Verification

**Test Server Connection:**
```bash
# Check server health (SSE mode)
curl http://localhost:8000/health

# Check server status
curl http://localhost:8000/status
```

**Test MCP Tools:**
Once connected to your IDE, try the `thinking` tool:
- **Autonomous Mode**: Detailed response generated by LLM
- **Guided Mode**: Structured protocol/template to follow

### Getting Help

- **Documentation**: Check `docs/` directory for detailed guides
- **Issues**: Report bugs on GitHub Issues
- **Logs**: Always include logs when reporting issues

---

## 10. Advanced Configuration

### Performance Tuning

**Environment Variables:**
```env
# Increase max thoughts per session
CCT_MAX_THOUGHTS=500

# Increase context window
CCT_MAX_CONTEXT_TOKENS=8000

# Adjust thinking pattern threshold
CCT_TP_THRESHOLD=0.95
```

### Custom Model Configuration

Add custom models to `database/datasets/`:
```json
{
  "model_id": "custom-model",
  "name": "Custom Model",
  "provider": "custom",
  "input_price_per_1k": 0.001,
  "output_price_per_1k": 0.002,
  "max_tokens": 4096
}
```

### Database Configuration

```env
# Custom database path
CCT_DB_PATH=/custom/path/cct_memory.db

# Custom pricing data path
CCT_PRICING_PATH=/custom/path/datasets
```

---

## Summary

**Quick Start (Windows):**
```powershell
.\scripts\setup\setup.bat --multi-agent --run
```

**Quick Start (Linux/macOS):**
```bash
./scripts/setup/setup.sh --multi-agent --run
```

**Multi-IDE Setup:**
1. Configure SSE mode in `.env`
2. Start server: `python scripts/server/manage.py start`
3. Connect IDEs to `http://localhost:8001/cognitive-api/v1/sse`

**Service Installation:**
- Windows: `.\scripts\setup\setup.bat --install-service` (as Admin) - Auto-starts on boot by default
- Linux/macOS: `sudo ./scripts/setup/setup.sh --install-service`

> [!NOTE]
> For detailed troubleshooting and advanced configuration, refer to `SETUP_TEST_RESULTS.md` and `PORT_FIXES_SUMMARY.md` in the project root.
