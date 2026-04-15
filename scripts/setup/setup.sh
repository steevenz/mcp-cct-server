#!/bin/bash
# File: .bin/setup.sh
# Author: Steeven Andrian — Senior Systems Architect
# Design: Laravel Artisan Style CLI

VERSION="1.0.0"

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
PORT=0

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --force) FORCE=1 ;;
        --skip-deps) SKIP_DEPS=1 ;;
        --clean-reqs) CLEAN_REQS=1 ;;
        --run) RUN=1 ;;
        --install-service) INSTALL_SERVICE=1 ;;
        --multi-agent) MULTI_AGENT=1 ;;
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
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
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
    exit 1
fi

if check_python_version; then
    python_version=$($PYTHON_CMD --version 2>&1)
    show_status "Verifying Python Environment ($python_version)" "DONE" "${GREEN}"
else
    exit 1
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
CCT_DEFAULT_PORT=${PORT:-8001}
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
        exit 1
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
        exit 1
    fi
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
fi
