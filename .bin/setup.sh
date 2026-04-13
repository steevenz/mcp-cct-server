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
RUN=0

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --force) FORCE=1 ;;
        --skip-deps) SKIP_DEPS=1 ;;
        --run) RUN=1 ;;
        --help)
            echo -e "\n  ${INFO_BLOCK} CCT COGNITIVE SERVER ${NC} ${GRAY}${VERSION}${NC}"
            echo -e "  ${GRAY}Crafted By Steeven Andrian Salim - https://github.com/steevenz${NC}\n"
            echo -e "  USAGE: setup.sh [options]\n"
            echo -e "  OPTIONS:"
            echo -e "    --force          Force recreate .venv and reset cct_memory.db"
            echo -e "    --skip-deps      Skip installing dependencies from requirements.txt"
            echo -e "    --run            Automatically start the server after successful setup"
            echo -e "    --help           Display this help information\n"
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
show_status "Verifying Python Environment" "DONE" "${GREEN}"

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

# --- Finish ---
echo -e "\n  ${DONE_BLOCK} SUCCESS ${NC} Mission Ready: CCT MCP Server is initialized.\n"

if [ $RUN -eq 1 ]; then
    echo -e "  ${RUN_BLOCK} INFO ${NC} Launching Cognitive Engine...\n"
    . .venv/bin/activate
    python src/main.py
else
    echo -e "  ${GRAY}To start the server, run:${NC}"
    echo -e "  ${CYAN}source .venv/bin/activate && python src/main.py${NC}\n"
fi
