# Guide: CCT Server Management

This guide provides comprehensive documentation for managing the CCT MCP Server using the server management tools in the `scripts/server` directory.

## Table of Contents
1. [Overview](#1-overview)
2. [Server Management Tools](#2-server-management-tools)
3. [Server Discovery (discover.py)](#3-server-discovery-discoverpy)
4. [Server Manager (manage.py)](#4-server-manager-managepy)
5. [Server Setup (setup.py)](#5-server-setup-setuppy)
6. [Common Workflows](#6-common-workflows)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Overview

The CCT MCP Server provides three Python-based tools for server management:

- **discover.py** - Server discovery and health monitoring
- **manage.py** - Server lifecycle management (start, stop, restart)
- **setup.py** - Cross-platform server setup and configuration

These tools work together to provide a complete server management solution for development, testing, and production deployments.

---

## 2. Server Management Tools

### Tool Comparison

| Tool | Purpose | Key Commands | Use Case |
|------|---------|--------------|----------|
| `discover.py` | Discovery & Monitoring | scan, status, health, start | Finding servers, health checks |
| `manage.py` | Lifecycle Management | start, stop, restart, logs, status | Controlling server lifecycle |
| `setup.py` | Setup & Configuration | --force, --skip-deps, --run | Initial setup and configuration |

### Tool Locations

All tools are located in `scripts/server/`:
```
scripts/server/
├── discover.py    # Server discovery and monitoring
├── manage.py      # Server lifecycle management
└── setup.py       # Cross-platform setup
```

---

## 3. Server Discovery (discover.py)

The `discover.py` script provides server discovery, health monitoring, and automatic server startup capabilities.

### Features

- **Server Scanning**: Discover running CCT servers on your network
- **Health Monitoring**: Check server health and status
- **Auto-Start**: Automatically start server if not running
- **Server Pool Management**: Manage multiple server instances
- **HTTP-based Discovery**: Uses HTTP requests to find servers

### Commands

#### scan
Scan for running CCT servers.

```bash
python scripts/server/discover.py scan
```

**Output:**
```
  CCT COGNITIVE SERVER 1.0.0
  Crafted By Steeven Andrian Salim - https://github.com/steevenz

🔍 Scanning for CCT servers...
  DISCOVERY  Found 2 CCT server(s)

✅ CCT Server is RUNNING
   📍 http://localhost:8000
      Port: 8000
      Healthy: True
      Uptime: Unknown
      Connections: 0

   📍 http://127.0.0.1:8000
      Port: 8000
      Healthy: True
      Uptime: Unknown
      Connections: 0

   AI Agents can connect to: http://localhost:8000
```

**Options:**
- `-v, --verbose` - Show detailed scan information

---

#### start
Start the server if it's not already running.

```bash
python scripts/server/discover.py start
```

**Behavior:**
- Checks if server is already running
- Starts server if not running
- Uses default configuration from `.env`
- Displays server URL after startup

**Options:**
- `-v, --verbose` - Show detailed startup information

---

#### status
Show detailed server status.

```bash
python scripts/server/discover.py status
```

**Output:**
```
  CCT COGNITIVE SERVER 1.0.0
  Crafted By Steeven Andrian Salim - https://github.com/steevenz

📊 Server Status
   Status: RUNNING
   URL: http://localhost:8000
   Port: 8000
   Healthy: True
   Connections: 0
```

**Options:**
- `-v, --verbose` - Show detailed status information

---

#### health
Perform health check on the server.

```bash
python scripts/server/discover.py health
```

**Output:**
```
  CCT COGNITIVE SERVER 1.0.0
  Crafted By Steeven Andrian Salim - https://github.com/steevenz

🏥 Health Check
   Status: HEALTHY
   Response Time: 45ms
   Uptime: 2h 30m 15s
```

**Options:**
- `-v, --verbose` - Show detailed health information

---

### Programmatic Usage

You can also use `discover.py` as a Python module:

```python
from scripts.server.discover import CCTServerDiscovery, CCTServerPool

# Create discovery instance
discovery = CCTServerDiscovery()

# Scan for servers (async)
import asyncio
servers = asyncio.run(discovery.scan(verbose=True))

# Use server pool
pool = CCTServerPool()
pool.add_server("http://localhost:8000")
pool.add_server("http://127.0.0.1:8000")

# Get health status
health = asyncio.run(pool.check_health())
```

---

## 4. Server Manager (manage.py)

The `manage.py` script provides comprehensive server lifecycle management.

### Features

- **Start/Stop/Restart**: Full control over server lifecycle
- **Status Monitoring**: Real-time server status
- **Log Viewing**: View server logs with tail functionality
- **Process Management**: Cross-platform process management
- **Auto-Discovery**: Automatically finds running servers

### Commands

#### status
Check server status.

```bash
python scripts/server/manage.py status
```

**Output:**
```
  CCT COGNITIVE SERVER 1.0.0
  Crafted By Steeven Andrian Salim - https://github.com/steevenz

🔍 Checking CCT server status...
✅ CCT Server is RUNNING
   📍 http://localhost:8000
      Port: 8000
      Healthy: True
      Uptime: Unknown
      Connections: 0

   AI Agents can connect to: http://localhost:8000
```

**Options:**
- `-v, --verbose` - Show detailed status information

---

#### start
Start the CCT server.

```bash
python scripts/server/manage.py start
```

**Behavior:**
- Checks if server is already running
- Starts server if not running
- Uses configuration from `.env`
- Displays server URL after startup
- Supports environment variables for port/host

**Options:**
- `-v, --verbose` - Show detailed startup information

**Environment Variables:**
- `CCT_PORT` - Server port (default: 8001)
- `CCT_HOST` - Server host (default: 0.0.0.0)

**Example:**
```bash
# Start with custom port
CCT_PORT=8002 python scripts/server/manage.py start
```

---

#### stop
Stop the CCT server.

```bash
python scripts/server/manage.py stop
```

**Behavior:**
- Finds running server process
- Gracefully stops the server
- Waits for process termination
- Displays stop confirmation

**Options:**
- `-v, --verbose` - Show detailed stop information

**Platform-Specific:**
- **Windows**: Uses `taskkill` command
- **Linux/macOS**: Uses `kill` command

---

#### restart
Restart the CCT server.

```bash
python scripts/server/manage.py restart
```

**Behavior:**
- Stops the server if running
- Waits for process termination
- Starts the server again
- Displays restart confirmation

**Options:**
- `-v, --verbose` - Show detailed restart information

**Use Case:**
- Apply configuration changes
- Recover from errors
- Regular maintenance

---

#### logs
View server logs.

```bash
python scripts/server/manage.py logs
```

**Behavior:**
- Displays server log output
- Shows recent log entries
- Monitors for new log entries

**Options:**
- `--tail N` - Show last N log lines (default: 50)
- `-v, --verbose` - Show detailed log information

**Example:**
```bash
# Show last 100 log lines
python scripts/server/manage.py logs --tail 100
```

**Platform-Specific:**
- **Windows**: Uses PowerShell `Get-Content` with `Wait` parameter
- **Linux/macOS**: Uses `tail -f` command

---

### Advanced Usage

#### Custom Port/Host

```bash
# Start with custom configuration
CCT_PORT=8002 CCT_HOST=127.0.0.1 python scripts/server/manage.py start
```

#### Verbose Mode

```bash
# Get detailed information
python scripts/server/manage.py status -v
python scripts/server/manage.py start -v
python scripts/server/manage.py stop -v
```

#### Log Monitoring

```bash
# Monitor logs in real-time
python scripts/server/manage.py logs --tail 100
```

---

## 5. Server Setup (setup.py)

The `setup.py` script provides cross-platform server setup and configuration.

### Features

- **Virtual Environment Management**: Create and manage Python virtual environments
- **Dependency Installation**: Install required packages
- **Environment Configuration**: Set up `.env` file
- **Multi-Agent Configuration**: Configure for multi-agent mode
- **Auto-Start**: Start server after setup
- **Force Cleanup**: Clean and reset installation

### Commands

#### Standard Setup
Run standard setup with default options.

```bash
python scripts/server/setup.py
```

**What it does:**
1. Checks Python environment
2. Creates virtual environment (if needed)
3. Installs dependencies
4. Sets up `.env` file (if needed)
5. Configures server settings

---

#### Force Setup
Force recreate virtual environment and reset database.

```bash
python scripts/server/setup.py --force
```

**What it does:**
- Removes existing `.venv` directory
- Removes existing database
- Recreates virtual environment
- Reinstalls dependencies
- Resets configuration

**Use Case:**
- Clean installation
- Recover from corruption
- Start fresh

---

#### Skip Dependencies
Skip dependency installation.

```bash
python scripts/server/setup.py --skip-deps
```

**What it does:**
- Skips `pip install` steps
- Only sets up environment configuration
- Useful when dependencies are already installed

**Use Case:**
- Quick configuration changes
- Development iterations
- Dependency troubleshooting

---

#### Auto-Start
Start server after successful setup.

```bash
python scripts/server/setup.py --run
```

**What it does:**
- Performs standard setup
- Starts server automatically
- Displays server URL
- Useful for first-time setup

---

#### Multi-Agent Mode
Configure for multi-agent shared server mode.

```bash
python scripts/server/setup.py --multi-agent
```

**What it does:**
- Sets `CCT_TRANSPORT=sse` in `.env`
- Configures for multiple IDE connections
- Optimizes for concurrent access
- Sets appropriate session limits

**Use Case:**
- Multi-IDE development
- Team collaboration
- Shared server deployment

---

#### Custom Port
Set custom server port.

```bash
python scripts/server/setup.py --port 8001
```

**What it does:**
- Sets `CCT_PORT` in `.env`
- Configures server to use custom port
- Useful for avoiding port conflicts

**Example:**
```bash
# Multi-agent with custom port
python scripts/server/setup.py --multi-agent --port 8001
```

---

### Combined Options

You can combine multiple options:

```bash
# Force setup with multi-agent mode and auto-start
python scripts/server/setup.py --force --multi-agent --run

# Setup with custom port and skip dependencies
python scripts/server/setup.py --port 8002 --skip-deps

# Complete setup with all options
python scripts/server/setup.py --force --multi-agent --port 8001 --run
```

---

## 6. Common Workflows

### Initial Setup

```bash
# 1. Run setup
python scripts/server/setup.py

# 2. Start server
python scripts/server/manage.py start

# 3. Check status
python scripts/server/manage.py status
```

### Multi-Agent Setup

```bash
# 1. Configure for multi-agent mode
python scripts/server/setup.py --multi-agent --port 8001

# 2. Start server
python scripts/server/manage.py start

# 3. Verify status
python scripts/server/discover.py scan
```

### Development Workflow

```bash
# 1. Make code changes
# 2. Restart server to apply changes
python scripts/server/manage.py restart

# 3. Check logs for errors
python scripts/server/manage.py logs --tail 100

# 4. Verify server is healthy
python scripts/server/discover.py health
```

### Troubleshooting Workflow

```bash
# 1. Check server status
python scripts/server/manage.py status

# 2. View logs for errors
python scripts/server/manage.py logs

# 3. If needed, force restart
python scripts/server/manage.py restart

# 4. If still failing, force reinstall
python scripts/server/setup.py --force --run
```

### Production Deployment

```bash
# 1. Clean setup
python scripts/server/setup.py --force --multi-agent --port 8001

# 2. Start server
python scripts/server/manage.py start

# 3. Verify health
python scripts/server/discover.py health

# 4. Monitor logs
python scripts/server/manage.py logs --tail 100
```

### Service Management

**Windows Service:**
```bash
# Install service (as Administrator)
python scripts/setup/services/windows/service.py install

# Start service
python scripts/setup/services/windows/service.py start

# Check status
python scripts/setup/services/windows/service.py status

# Stop service
python scripts/setup/services/windows/service.py stop
```

**Linux/macOS systemd Service:**
```bash
# Install service (with sudo)
sudo ./scripts/setup/setup.sh --install-service

# Start service
sudo systemctl start cct-cognitive-os

# Check status
sudo systemctl status cct-cognitive-os

# View logs
sudo journalctl -u cct-cognitive-os -f
```

---

## 7. Troubleshooting

### Server Won't Start

**Symptoms:**
- `manage.py start` fails
- Server process doesn't appear
- Port already in use error

**Solutions:**

1. **Check for existing processes:**
```bash
python scripts/server/discover.py scan
```

2. **Check port availability:**
```bash
# Windows
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :8000
```

3. **Kill existing process:**
```bash
python scripts/server/manage.py stop
```

4. **Use different port:**
```bash
CCT_PORT=8002 python scripts/server/manage.py start
```

5. **Force reinstall:**
```bash
python scripts/server/setup.py --force --run
```

---

### Server Not Responding

**Symptoms:**
- Server starts but doesn't respond
- Health check fails
- Connection timeout

**Solutions:**

1. **Check server logs:**
```bash
python scripts/server/manage.py logs --tail 100
```

2. **Verify configuration:**
```bash
# Check .env file
cat .env
```

3. **Test health endpoint:**
```bash
curl http://localhost:8000/health
```

4. **Restart server:**
```bash
python scripts/server/manage.py restart
```

---

### Permission Errors

**Symptoms:**
- Permission denied errors
- Cannot write to directories
- Cannot bind to ports

**Solutions:**

1. **Run with appropriate permissions:**
```bash
# Windows: Run PowerShell as Administrator
# Linux/macOS: Use sudo for service installation
sudo ./scripts/setup/setup.sh --install-service
```

2. **Check file permissions:**
```bash
# Linux/macOS
ls -la .venv/
chmod +x scripts/server/*.py
```

3. **Use user directories for development:**
```bash
# Avoid system directories
# Use project-relative paths
```

---

### Virtual Environment Issues

**Symptoms:**
- Python not found in venv
- Dependencies not installed
- Import errors

**Solutions:**

1. **Force recreate venv:**
```bash
python scripts/server/setup.py --force
```

2. **Manually recreate venv:**
```bash
# Remove existing
rm -rf .venv

# Create new
python -m venv .venv

# Activate and install
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

3. **Check Python version:**
```bash
python --version
# Must be 3.8 or higher
```

---

### Configuration Issues

**Symptoms:**
- Server using wrong port
- Environment variables not loaded
- .env file not found

**Solutions:**

1. **Verify .env file:**
```bash
# Check if .env exists
ls -la .env

# Create from example if missing
cp .env.example .env
```

2. **Verify environment variables:**
```bash
# Check CCT_PORT
echo $CCT_PORT  # Linux/macOS
echo %CCT_PORT%  # Windows

# Set if needed
export CCT_PORT=8001  # Linux/macOS
set CCT_PORT=8001  # Windows
```

3. **Re-run setup:**
```bash
python scripts/server/setup.py
```

---

### Discovery Issues

**Symptoms:**
- discover.py can't find servers
- Health checks fail
- Scan shows no servers

**Solutions:**

1. **Verify server is running:**
```bash
python scripts/server/manage.py status
```

2. **Check transport mode:**
```bash
# Ensure SSE mode for discovery
grep CCT_TRANSPORT .env
# Should be: CCT_TRANSPORT=sse
```

3. **Test HTTP endpoint directly:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/status
```

4. **Check firewall settings:**
```bash
# Ensure port is not blocked
# Windows Firewall
# Linux: iptables, ufw
# macOS: pfctl
```

---

## Best Practices

### Development

1. **Use verbose mode for debugging:**
```bash
python scripts/server/manage.py start -v
```

2. **Monitor logs during development:**
```bash
python scripts/server/manage.py logs --tail 100
```

3. **Use different ports for different environments:**
```bash
# Development: 8000
# Staging: 8001
# Production: 8002
```

4. **Clean setup between major changes:**
```bash
python scripts/server/setup.py --force
```

### Production

1. **Use multi-agent mode for shared access:**
```bash
python scripts/server/setup.py --multi-agent --port 8001
```

2. **Install as service for auto-start:**
```bash
# Windows
python scripts/setup/services/windows/service.py install

# Linux/macOS
sudo ./scripts/setup/setup.sh --install-service
```

3. **Monitor server health regularly:**
```bash
python scripts/server/discover.py health
```

4. **Use appropriate logging level:**
```env
CCT_LOG_LEVEL=WARNING  # Production
CCT_LOG_LEVEL=DEBUG    # Development
```

### Security

1. **Restrict network access when possible:**
```env
CCT_HOST=127.0.0.1  # Local only
```

2. **Never commit .env to version control:**
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

3. **Rotate API keys regularly:**
```bash
# Update API keys in .env
# Restart server to apply changes
python scripts/server/manage.py restart
```

4. **Use service accounts for production:**
```bash
# Create separate API keys for production
# Use principle of least privilege
```

---

## Summary

**Key Tools:**
- `discover.py` - Server discovery and health monitoring
- `manage.py` - Server lifecycle management
- `setup.py` - Cross-platform setup and configuration

**Common Commands:**
```bash
# Setup
python scripts/server/setup.py --multi-agent --run

# Management
python scripts/server/manage.py start
python scripts/server/manage.py status
python scripts/server/manage.py stop
python scripts/server/manage.py restart
python scripts/server/manage.py logs

# Discovery
python scripts/server/discover.py scan
python scripts/server/discover.py health
```

**Best Practices:**
- Use verbose mode for debugging
- Monitor logs regularly
- Use different ports for different environments
- Install as service for production
- Never commit .env to version control
- Rotate API keys regularly

**Getting Help:**
- Use `-v, --verbose` flag for detailed information
- Check logs for error messages
- Verify configuration in .env
- Test HTTP endpoints directly
- Check firewall and network settings
