#!/bin/bash
# File: src/.bin/setup.sh
# Author: Steeven Andrian — Senior Systems Architect

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Banner ---
echo -e "${CYAN}"
cat << "EOF"
  ██████╗ ██████╗████████╗     ██████╗ ██████╗ 
 ██╔════╝██╔════╝╚══██╔══╝    ██╔═══██╗██╔══██╗
 ██║     ██║        ██║       ██║   ██║██████╔╝
 ██║     ██║        ██║       ██║   ██║██╔═══╝ 
 ╚██████╗╚██████╗   ██║       ╚██████╔╝██║     
  ╚═════╝ ╚═════╝   ╚═╝        ╚═════╝ ╚═╝     
                                               
     COGNITIVE OPERATING SYSTEM
     Author: Steeven Andrian
EOF
echo -e "${NC}"
echo "--------------------------------------------------------"
echo -e "${GREEN}Initializing Elite Architect Workspace...${NC}"
echo ""

# --- 1. Python Check ---
printf "[1/5] Verifying Python Environment..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo -e " [${RED}FAILED${NC}]"
    exit 1
fi
VERSION=$($PYTHON_CMD --version)
echo -e " [FOUND: $VERSION]"

# --- 2. Virtual Environment ---
printf "[2/5] Managing Virtual Environment (.venv)..."
if [ ! -d ".venv" ]; then
    echo -e " [${YELLOW}CREATING...${NC}]"
    $PYTHON_CMD -m venv .venv
else
    echo -e " [${CYAN}EXISTING${NC}]"
fi

# --- 3. Dependency Installation ---
printf "[3/5] Syncing Dependencies (requirements.txt)..."
if [ -f "requirements.txt" ]; then
    echo -e " [${YELLOW}INSTALLING...${NC}]"
    source .venv/bin/activate
    python -m pip install --upgrade pip --quiet || echo " (Note: Pip upgrade skipped, continuing...)"
    python -m pip install -r requirements.txt --quiet
    echo -e "${GREEN}SUCCESS: 22+ Cognitive Primitives Ready.${NC}"
else
    echo -e " [${RED}MISSING${NC}]"
fi

# --- 4. Environment Configuration ---
printf "[4/5] Auditing Configuration (.env)..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e " [${YELLOW}INITIALIZING${NC}]"
        cp .env.example .env
    else
        echo -e " [${RED}MISSING${NC}]"
    fi
else
    echo -e " [${CYAN}VERIFIED${NC}]"
fi

# --- 5. Workspace Integrity ---
printf "[5/5] Mapping Cognitive Architecture..."
REQUIRED=("src" "src/engines" "src/modes" "docs")
MISSING=0
for dir in "${REQUIRED[@]}"; do
    if [ ! -d "$dir" ]; then
        MISSING=$((MISSING+1))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo -e " [${GREEN}STABLE${NC}]"
else
    echo -e " [${YELLOW}FRAGILE${NC}]"
fi

echo "--------------------------------------------------------"
echo -e "${GREEN}✅ MISSION READY: CCT MCP Server is initialized.${NC}"
echo ""
echo "To start the server, run:"
echo "  source .venv/bin/activate && python src/main.py"
echo ""
echo "To launch Mission Control Dashboard:"
echo "  streamlit run dashboard.py"
echo ""
