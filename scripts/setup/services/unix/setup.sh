#!/bin/bash
# Setup Script for CCT Cognitive OS Linux/macOS Service
# Author: Steeven Andrian — Senior Systems Architect
# Run this with sudo on Linux/macOS

set -e

# Detect platform
PLATFORM=$(uname -s)
echo "Platform: $PLATFORM"

# Define paths
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PYTHON_VENV="$REPO_ROOT/.venv/bin/python"
SERVICE_SCRIPT="$REPO_ROOT/scripts/setup/services/unix/service.py"

echo "--- CCT Cognitive OS: Unix Service Setup ---"
echo "Repository Root: $REPO_ROOT"
echo "Using Python: $PYTHON_VENV"

# Verify requirements
if [ ! -f "$PYTHON_VENV" ]; then
    echo "❌ ERROR: Virtual environment not found at $PYTHON_VENV"
    echo "   Please run 'python -m venv .venv' first"
    exit 1
fi

# Create logs directory
mkdir -p "$REPO_ROOT/database/logs"

# Install service
echo ""
echo "🔧 Installing CCT service..."
"$PYTHON_VENV" "$SERVICE_SCRIPT" install

# Start service
echo ""
echo "🚀 Starting service..."
"$PYTHON_VENV" "$SERVICE_SCRIPT" start

echo ""
echo "✅ SUCCESS: CCT Cognitive OS is now running as a background service"
echo "   Check logs at: $REPO_ROOT/database/logs/"
echo "   MCP SSE Endpoint: http://localhost:8001"
echo ""
echo "Management commands:"
echo "  sudo $PYTHON_VENV $SERVICE_SCRIPT status"
echo "  sudo $PYTHON_VENV $SERVICE_SCRIPT stop"
echo "  sudo $PYTHON_VENV $SERVICE_SCRIPT start"
echo "  sudo $PYTHON_VENV $SERVICE_SCRIPT restart"
echo "  sudo $PYTHON_VENV $SERVICE_SCRIPT remove"
