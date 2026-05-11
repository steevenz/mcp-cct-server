#!/bin/bash
# File: .bin/setup.sh
# Author: Steeven Andrian â€” Senior Systems Architect
# Design: Laravel Artisan Style CLI

VERSION="1.0.0"
MIN_PYTHON_VERSION="3.8.0"

# Colors & Blocks
INFO_BLOCK='\033[43;30m' # Black on Yellow
DONE_BLOCK='\033[42;30m' # Black on Green
FAIL_BLOCK='\033[41;37m' # White on Red
RUN_BLOCK='\033[44;37m'  # White on Blue
NC='\033[0m'              # No Color
GRAY='\033[0;90m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'

# Parameters
FORCE=0
SKIP_DEPS=0
CLEAN_REQS=0
RUN=0
INSTALL_SERVICE=0
MULTI_AGENT=0
TEST_SERVICE=0
START_SERVICE=0
STOP_SERVICE=0
RESTART_SERVICE=0
HEALTH_CHECK=0
STATUS_CHECK=0
SERVICE_E2E=0
DOWNLOAD=0
REGISTER=0
PORT=0

pause_on_exit() {
    if [ "${CCT_NO_EXIT_PROMPT:-0}" = "1" ]; then
        return
    fi
    printf "\nPress Enter to exit..."
    read -r _
}

exit_script() {
    code=${1:-0}
    pause_on_exit
    exit "$code"
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --force) FORCE=1 ;;
        --skip-deps) SKIP_DEPS=1 ;;
        --clean-reqs) CLEAN_REQS=1 ;;
        --run) RUN=1 ;;
        --install-service) INSTALL_SERVICE=1 ;;
        --multi-agent) MULTI_AGENT=1 ;;
        --test-service) TEST_SERVICE=1 ;;
        --restart) RESTART_SERVICE=1 ;; # Backward-compatible alias
        --restart-service) RESTART_SERVICE=1 ;;
        --start-service) START_SERVICE=1 ;;
        --stop-service) STOP_SERVICE=1 ;;
        --health) HEALTH_CHECK=1 ;;
        --status) STATUS_CHECK=1 ;;
        --service-e2e) SERVICE_E2E=1 ;;
        --download) DOWNLOAD=1 ;;
        --register) REGISTER=1 ;;
        --port) PORT="$2"; shift ;;
        --help)
            echo -e "\n  ${INFO_BLOCK} CCT COGNITIVE SERVER ${NC} ${GRAY}${VERSION}${NC}"
            echo -e "  ${GRAY}Crafted By Steeven Andrian Salim - https://github.com/steevenz${NC}\n"
            echo -e "  USAGE: setup.sh [options]\n"
            echo -e "  OPTIONS:"
            echo -e "    --force          Force recreate .venv and reset cct_memory.db"
            echo -e "    --skip-deps      Skip installing dependencies from requirements.txt"
            echo -e "    --clean-reqs     Clean and reinstall all requirements"
            echo -e "    --run            Automatically start the server after successful setup"
            echo -e "    --install-service Install as systemd service (Linux/Mac)"
            echo -e "    --test-service   Start service + status + test MCP endpoint"
            echo -e "    --restart        Restart service (alias of --restart-service)"
            echo -e "    --restart-service Restart service (Linux/Mac)"
            echo -e "    --start-service   Start service (Linux/Mac)"
            echo -e "    --stop-service    Stop service (Linux/Mac)"
            echo -e "    --health         Run health check on the MCP server"
            echo -e "    --status         Check service status and server connectivity"
            echo -e "    --service-e2e    Run service lifecycle E2E (restart/stop/start + log tail)"
            echo -e "    --multi-agent      Configure for multi-agent shared server mode"
            echo -e "    --port <n>         Set server port (default: 8001)"
            echo -e "    --help           Display this help information\n"
            echo -e "  SYSTEMD SERVICE:"
            echo -e "    --install-service Install as systemd service (runs on boot)"
            echo -e "    Note: Requires sudo privileges"
            echo -e "    Start service:  sudo systemctl start cct-cognitive-os"
            echo -e "    Stop service:   sudo systemctl stop cct-cognitive-os\n"
            echo -e "  MULTI-AGENT MODE:"
            echo -e "    Run server once, all AI agents share it. Prevents port conflicts."
            echo -e "    Example: setup.sh --multi-agent --run\n"
            exit_script 0
            ;;
        *) echo "Unknown parameter: $1"; exit_script 1 ;;
    esac
    shift
done

echo -e "\n  ${INFO_BLOCK} CCT COGNITIVE SERVER ${NC} ${GRAY}${VERSION}${NC}"
echo -e "  ${GRAY}Crafted By Steeven Andrian Salim - https://github.com/steevenz${NC}\n"

# Progress Helpers
show_status() {
    label=$1
    status=$2
    color=$3
    printf "  ${GRAY}%-40s${NC} [${color}%s${NC}]\n" "${label}..." "${status}"
}

check_admin() {
    if [ "$EUID" -ne 0 ]; then
        return 1
    fi
    return 0
}

check_python_version() {
    local python_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    if [[ $(echo -e "$python_version\n$MIN_PYTHON_VERSION" | sort -V | head -n1) == "$MIN_PYTHON_VERSION" ]]; then
        return 0
    else
        echo -e "\n  ${FAIL_BLOCK} ERROR ${NC} Python $python_version is not supported. Minimum required: $MIN_PYTHON_VERSION\n"
        return 1
    fi
}

# --- 1. Python Check ---
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    show_status "Verifying Python Environment" "FAIL" "${RED}"
    echo -e "\n  ${FAIL_BLOCK} ERROR ${NC} Python is not installed or not in PATH.\n"
    exit_script 1
fi

if check_python_version; then
    python_version=$($PYTHON_CMD --version 2>&1)
    show_status "Verifying Python Environment ($python_version)" "DONE" "${GREEN}"
else
    exit_script 1
fi

# --- 2. Force Cleanup ---
if [ $FORCE -eq 1 ]; then
    show_status "Forcing Clean Architecture" "CLEANING" "${YELLOW}"
    rm -rf .venv
    rm -f cct_memory.db
    show_status "Forcing Clean Architecture" "CLEAN" "${GREEN}"
fi

# --- 3. Virtual Environment ---
if [ ! -d ".venv" ]; then
    show_status "Managing Virtual Environment" "CREATING" "${YELLOW}"
    $PYTHON_CMD -m venv .venv
    show_status "Managing Virtual Environment" "DONE" "${GREEN}"
else
    show_status "Managing Virtual Environment" "EXISTING" "${CYAN}"
fi

# --- 4. Dependencies ---
if [ $SKIP_DEPS -eq 1 ]; then
    show_status "Syncing Dependencies" "SKIPPED" "${CYAN}"
else
    show_status "Syncing Dependencies" "SYNCING" "${YELLOW}"
    if [ -f "requirements.txt" ]; then
        . .venv/bin/activate

        if [ $CLEAN_REQS -eq 1 ]; then
            show_status "Cleaning Dependencies" "CLEANING" "${YELLOW}"
            pip freeze | xargs pip uninstall -y --quiet 2>/dev/null
            show_status "Cleaning Dependencies" "CLEAN" "${GREEN}"
        fi

        python -m pip install --upgrade pip --quiet
        python -m pip install -r requirements.txt --quiet
        show_status "Syncing Dependencies" "DONE" "${GREEN}"
    else
        show_status "Syncing Dependencies" "MISSING" "${RED}"
    fi
fi

# --- 4.5 Model Download (Gemma) ---
if [ $DOWNLOAD -eq 1 ]; then
    show_status "Downloading Gemma Models" "IN PROGRESS" "${YELLOW}"
    . .venv/bin/activate
    python scripts/setup/download_models.py
    if [ $? -eq 0 ]; then
        show_status "Downloading Gemma Models" "DONE" "${GREEN}"
    else
        show_status "Downloading Gemma Models" "FAILED" "${RED}"
    fi
fi

# --- 4.6 MCP Registration ---
if [ $REGISTER -eq 1 ]; then
    show_status "Registering MCP Server" "IN PROGRESS" "${YELLOW}"
    . .venv/bin/activate
    python scripts/setup/register_mcp.py
    if [ $? -eq 0 ]; then
        show_status "Registering MCP Server" "DONE" "${GREEN}"
    else
        show_status "Registering MCP Server" "FAILED" "${RED}"
    fi
fi

# --- 5. Environment ---
show_status "Auditing Configuration (.env)" "AUDITING" "${YELLOW}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        show_status "Auditing Configuration (.env)" "INITIALIZED" "${GREEN}"
    else
        show_status "Auditing Configuration (.env)" "FAILED" "${RED}"
    fi
else
    show_status "Auditing Configuration (.env)" "VERIFIED" "${CYAN}"
fi

# --- 5.5. Multi-Agent Server Configuration ---
CCT_DEFAULT_PORT=${PORT:-${CCT_PORT:-8001}}
if [ $MULTI_AGENT -eq 1 ] || [ $PORT -gt 0 ]; then
    show_status "Configuring Multi-Agent Server" "CONFIGURING" "${YELLOW}"

    # Read existing .env
    env_content=$(cat .env)

    # Update port
    if echo "$env_content" | grep -q "CCT_PORT="; then
        env_content=$(echo "$env_content" | sed "s/CCT_PORT=.*/CCT_PORT=$CCT_DEFAULT_PORT/")
    else
        env_content="${env_content}"$'\n'"CCT_PORT=$CCT_DEFAULT_PORT"
    fi

    # Set transport to SSE for multi-agent
    if [ $MULTI_AGENT -eq 1 ]; then
        if echo "$env_content" | grep -q "CCT_TRANSPORT="; then
            env_content=$(echo "$env_content" | sed "s/CCT_TRANSPORT=.*/CCT_TRANSPORT=sse/")
        else
            env_content="${env_content}"$'\n'"CCT_TRANSPORT=sse"
        fi
    fi

    # Save updated .env
    echo "$env_content" > .env

    show_status "Configuring Multi-Agent Server" "PORT=$CCT_DEFAULT_PORT" "${GREEN}"
fi

# --- 6. Systemd/launchd Service Installation ---
if [ $INSTALL_SERVICE -eq 1 ]; then
    show_status "Installing Systemd/launchd Service" "CHECKING" "${YELLOW}"

    if ! check_admin; then
        show_status "Installing Systemd/launchd Service" "DENIED" "${RED}"
        echo -e "\n  ${FAIL_BLOCK} ERROR ${NC} Administrator privileges required for service installation.\n"
        echo -e "  ${YELLOW}Please run this script with sudo.\n"
        exit_script 1
    fi

    show_status "Installing Systemd/launchd Service" "INSTALLING" "${YELLOW}"

    # Use the new unified service manager
    PROJECT_ROOT=$(pwd)
    . .venv/bin/activate
    python "$PROJECT_ROOT/scripts/setup/services/unix/service.py" install

    if [ $? -eq 0 ]; then
        show_status "Installing Systemd/launchd Service" "INSTALLED" "${GREEN}"
        echo -e "\n  ${RUN_BLOCK} INFO ${NC} Service installed successfully"
        echo -e "  ${YELLOW}Linux (systemd):${NC}   sudo systemctl start cct-cognitive-os"
        echo -e "  ${YELLOW}macOS (launchd):${NC}   sudo launchctl start com.cct.cognitiveos"
        echo -e "  ${GRAY}Or use:${NC}           sudo python scripts/setup/services/unix/service.py start\n"
    else
        show_status "Installing Systemd/launchd Service" "FAILED" "${RED}"
        echo -e "\n  ${FAIL_BLOCK} ERROR ${NC} Service installation failed.\n"
        exit_script 1
    fi
fi

# --- 6.4. Start/Stop/Restart Service Commands ---
if [ $START_SERVICE -eq 1 ] || [ $STOP_SERVICE -eq 1 ] || [ $RESTART_SERVICE -eq 1 ]; then
    PROJECT_ROOT=$(pwd)
    SERVICE_MANAGER="$PROJECT_ROOT/scripts/setup/services/unix/service.py"
    . .venv/bin/activate

    if [ $START_SERVICE -eq 1 ]; then
        echo -e "\n  ${INFO_BLOCK} START SERVICE ${NC} Starting cct-cognitive-os service\n"
        python "$SERVICE_MANAGER" start
        python "$SERVICE_MANAGER" status
        echo -e "\n  ${DONE_BLOCK} START COMPLETE ${NC} Service started successfully.\n"
        exit_script 0
    fi

    if [ $STOP_SERVICE -eq 1 ]; then
        echo -e "\n  ${INFO_BLOCK} STOP SERVICE ${NC} Stopping cct-cognitive-os service\n"
        python "$SERVICE_MANAGER" stop
        python "$SERVICE_MANAGER" status
        echo -e "\n  ${DONE_BLOCK} STOP COMPLETE ${NC} Service stopped successfully.\n"
        exit_script 0
    fi

    if [ $RESTART_SERVICE -eq 1 ]; then
        echo -e "\n  ${INFO_BLOCK} RESTART SERVICE ${NC} Restarting cct-cognitive-os service\n"
        python "$SERVICE_MANAGER" restart
        python "$SERVICE_MANAGER" status
        echo -e "\n  ${DONE_BLOCK} RESTART COMPLETE ${NC} Service restarted successfully.\n"
        exit_script 0
    fi
fi

# --- 6.5. Test Service Command ---
if [ $TEST_SERVICE -eq 1 ]; then
    echo -e "\n  ${INFO_BLOCK} TEST SERVICE ${NC} Starting service + status + MCP endpoint test\n"

    # Start service
    echo -e "  ${GRAY}[1/4] Starting cct-cognitive-os service...${NC}"
    sudo systemctl start cct-cognitive-os
    sleep 5

    # Check status
    echo -e "  ${GRAY}[2/4] Checking service status...${NC}"
    sudo systemctl status cct-cognitive-os

    # Test health endpoint
    echo -e "\n  ${GRAY}[3/4] Testing health endpoint...${NC}"
    curl "http://localhost:$CCT_DEFAULT_PORT/health" || echo -e "  ${RED}Health endpoint test failed${NC}"

    # Test MCP SSE endpoint
    echo -e "\n  ${GRAY}[4/4] Testing MCP SSE endpoint...${NC}"
    curl "http://localhost:$CCT_DEFAULT_PORT/cognitive-api/v1/sync" || echo -e "  ${RED}MCP SSE endpoint test failed${NC}"

    echo -e "\n  ${DONE_BLOCK} TEST COMPLETE ${NC} Service test finished.\n"
    exit_script 0
fi

# --- 6.55. Service E2E Command ---
if [ $SERVICE_E2E -eq 1 ]; then
    echo -e "\n  ${INFO_BLOCK} SERVICE E2E ${NC} Running restart -> stop -> start + log tail\n"

    # If running from Git Bash/MSYS/Cygwin on Windows, delegate to setup.ps1 for elevation prompt.
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*)
                    CCT_NO_EXIT_PROMPT=1 powershell -ExecutionPolicy Bypass -File scripts/setup/setup.ps1 -ServiceE2E
            exit_script $?
            ;;
    esac

    if ! check_admin; then
        echo -e "\n  ${FAIL_BLOCK} ERROR ${NC} Administrator privileges required for service E2E.\n"
        echo -e "  ${YELLOW}Please run this command with sudo.${NC}\n"
        exit_script 1
    fi

    PROJECT_ROOT=$(pwd)
    SERVICE_MANAGER="$PROJECT_ROOT/scripts/setup/services/unix/service.py"
    SERVICE_LOG="$PROJECT_ROOT/database/logs/cct_service.log"
    . .venv/bin/activate

    echo -e "  ${GRAY}[1/4] Restart service...${NC}"
    python "$SERVICE_MANAGER" restart || exit_script 1

    echo -e "\n  ${GRAY}[2/4] Stop service...${NC}"
    python "$SERVICE_MANAGER" stop || exit_script 1

    echo -e "\n  ${GRAY}[3/4] Start service...${NC}"
    python "$SERVICE_MANAGER" start || exit_script 1

    echo -e "\n  ${GRAY}[4/4] Tail service log (last 120 lines)...${NC}"
    if [ -f "$SERVICE_LOG" ]; then
        tail -n 120 "$SERVICE_LOG"
    else
        echo -e "  ${YELLOW}[WARN] Log file not found: $SERVICE_LOG${NC}"
    fi

    echo -e "\n  ${DONE_BLOCK} SERVICE E2E COMPLETE ${NC} Lifecycle checks executed successfully.\n"
    exit_script 0
fi

# --- 6.6. Health Check Command ---
if [ $HEALTH_CHECK -eq 1 ]; then
    echo -e "\n  ${INFO_BLOCK} HEALTH CHECK ${NC} Running comprehensive health check on MCP server\n"

    # Check if server is running
    echo -e "  ${GRAY}[1/5] Checking server status...${NC}"
    if curl -s "http://localhost:$CCT_DEFAULT_PORT/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}âœ“ Server is running${NC}"
    else
        echo -e "  ${RED}âœ— Server is not running${NC}"
        echo -e "  ${YELLOW}Start server with: source .venv/bin/activate && python src/main.py${NC}"
        exit_script 1
    fi

    # Test health endpoint
    echo -e "\n  ${GRAY}[2/5] Testing health endpoint...${NC}"
    HEALTH_RESPONSE=$(curl -s "http://localhost:$CCT_DEFAULT_PORT/health")
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}âœ“ Health endpoint: OK${NC}"
        echo -e "  ${GRAY}Response: ${HEALTH_RESPONSE}${NC}"
    else
        echo -e "  ${RED}âœ— Health endpoint failed${NC}"
        exit_script 1
    fi

    # Test MCP SSE endpoint
    echo -e "\n  ${GRAY}[3/5] Testing MCP SSE endpoint...${NC}"
    SSE_RESPONSE=$(curl -s "http://localhost:$CCT_DEFAULT_PORT/cognitive-api/v1/sync")
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}âœ“ MCP SSE endpoint: OK${NC}"
        echo -e "  ${GRAY}Response length: ${#SSE_RESPONSE} characters${NC}"
    else
        echo -e "  ${RED}âœ— MCP SSE endpoint failed${NC}"
        exit_script 1
    fi

    # Test API key authentication
    echo -e "\n  ${GRAY}[4/5] Testing API key authentication...${NC}"
    AUTH_RESPONSE=$(curl -s -H "X-API-KEY: invalid-key" "http://localhost:$CCT_DEFAULT_PORT/cognitive-api/v1/sync")
    if echo "$AUTH_RESPONSE" | grep -q "Invalid API key"; then
        echo -e "  ${GREEN}âœ“ API key authentication: WORKING${NC}"
    else
        echo -e "  ${YELLOW}âš  API key authentication test inconclusive${NC}"
    fi

    # Test CORS headers
    echo -e "\n  ${GRAY}[5/5] Testing CORS headers...${NC}"
    CORS_HEADERS=$(curl -s -I -H "Origin: http://localhost:3000" "http://localhost:$CCT_DEFAULT_PORT/health" | grep -i "access-control")
    if [ -n "$CORS_HEADERS" ]; then
        echo -e "  ${GREEN}âœ“ CORS headers: ENABLED${NC}"
        echo -e "  ${GRAY}$CORS_HEADERS${NC}"
    else
        echo -e "  ${YELLOW}âš  CORS headers not detected${NC}"
    fi

    echo -e "\n  ${DONE_BLOCK} HEALTH CHECK COMPLETE ${NC} All tests passed successfully!\n"
    echo -e "  ${GREEN}âœ“ Server is healthy and ready for MCP connections${NC}\n"
    exit_script 0
fi

# --- Status Check ---
if [ $STATUS_CHECK -eq 1 ]; then
    echo -e "\n  ${INFO_BLOCK} SERVICE STATUS CHECK ${NC}\n"

    # Check if service is installed and running
    echo -e "  ðŸ“Š Checking CCT Cognitive OS service status..."

    # Try to get service status using systemctl (Linux/Mac)
    if command -v systemctl >/dev/null 2>&1; then
        if systemctl is-active --quiet cct-cognitive-os 2>/dev/null; then
            echo -e "  ${GREEN}âœ“ Service is running (systemd)${NC}"
            SERVICE_RUNNING=true
        else
            echo -e "  ${YELLOW}âš  Service is not running (systemd)${NC}"
            SERVICE_RUNNING=false
        fi

        # Show detailed status
        echo -e "\n  ðŸ“‹ Detailed service status:"
        systemctl status cct-cognitive-os --no-pager -l
    else
        echo -e "  ${YELLOW}âš  Systemd not available - checking process status${NC}"

        # Check if server process is running
        if pgrep -f "python.*src/main.py" >/dev/null; then
            echo -e "  ${GREEN}âœ“ Server process is running${NC}"
            SERVICE_RUNNING=true
        else
            echo -e "  ${YELLOW}âš  Server process is not running${NC}"
            SERVICE_RUNNING=false
        fi
    fi

    # Test server connectivity
    echo -e "\n  ðŸŒ Testing server connectivity..."
    if curl -s "http://localhost:$CCT_DEFAULT_PORT/health" >/dev/null 2>&1; then
        echo -e "  ${GREEN}âœ“ Server is responding on port $CCT_DEFAULT_PORT${NC}"

        # Get health response
        HEALTH_RESPONSE=$(curl -s "http://localhost:$CCT_DEFAULT_PORT/health")
        echo -e "  ðŸ“„ Health endpoint response: $HEALTH_RESPONSE"

        # Test MCP endpoint
        echo -e "\n  ðŸ”— Testing MCP SSE endpoint..."
        if curl -s "http://localhost:$CCT_DEFAULT_PORT/cognitive-api/v1/sync" >/dev/null 2>&1; then
            echo -e "  ${GREEN}âœ“ MCP SSE endpoint is accessible${NC}"
        else
            echo -e "  ${YELLOW}âš  MCP SSE endpoint may require authentication${NC}"
        fi

        echo -e "\n  âœ… SERVICE STATUS: ACTIVE AND HEALTHY"
        echo -e "  The CCT Cognitive OS service is running and responding correctly.\n"
    else
        echo -e "  ${RED}âŒ Server is not responding on port $CCT_DEFAULT_PORT${NC}"
        echo -e "  The service may be installed but not running, or there may be a configuration issue.\n"

        echo -e "  ${YELLOW}Troubleshooting steps:${NC}"
        echo -e "  1. Check if service is running: sudo systemctl status cct-cognitive-os"
        echo -e "  2. Start the service: sudo systemctl start cct-cognitive-os"
        echo -e "  3. Check logs: tail -f database/logs/*.log"
        echo -e "  4. Verify installation: ./setup.sh --install-service"

        exit_script 1
    fi

    echo -e "\n"
    exit_script 0
fi

# --- Finish ---
echo -e "\n  ${DONE_BLOCK} SUCCESS ${NC} Mission Ready: CCT MCP Server is initialized.\n"

# Display multi-agent banner if configured
if [ $MULTI_AGENT -eq 1 ]; then
    echo -e "  ${INFO_BLOCK} MULTI-AGENT MODE ${NC} Server configured for shared access\n"
    echo -e "  ${YELLOW}Quick Start:${NC}"
    echo -e "  ${CYAN}1. Start server:    .venv/bin/python src/main.py${NC}"
    echo -e "  ${CYAN}2. Or use manager:   scripts/server/manage.py start${NC}"
    echo -e "  ${CYAN}3. Connect agents:  http://localhost:$CCT_DEFAULT_PORT${NC}"
    echo -e "  ${GRAY}4. Example:         python examples/multi_agent_example.py${NC}\n"
fi

if [ $RUN -eq 1 ]; then
    echo -e "  ${RUN_BLOCK} INFO ${NC} Launching Cognitive Engine...\n"
    . .venv/bin/activate
    python src/main.py
else
    if [ $MULTI_AGENT -eq 0 ]; then
        echo -e "  ${GRAY}To start the server, run:${NC}"
        echo -e "  ${CYAN}source .venv/bin/activate && python src/main.py${NC}\n"
    fi
fi
