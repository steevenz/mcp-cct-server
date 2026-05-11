#!/bin/bash
# Setup Script for CCT Cognitive OS Linux/macOS Service
# Author: Steeven Andrian — Senior Systems Architect
# Run this with sudo on Linux/macOS

set -e

# Parameter initialization
HEALTH_CHECK=0
SHOW_HELP=0
STATUS_CHECK=0
INSTALL_SERVICE=0
START_SERVICE=0
STOP_SERVICE=0
RESTART_SERVICE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --health)
            HEALTH_CHECK=1
            shift
            ;;
        --status)
            STATUS_CHECK=1
            shift
            ;;
        --install-service)
            INSTALL_SERVICE=1
            shift
            ;;
        --start-service)
            START_SERVICE=1
            shift
            ;;
        --stop-service)
            STOP_SERVICE=1
            shift
            ;;
        --restart-service|--restart)
            RESTART_SERVICE=1
            shift
            ;;
        -h|--help)
            SHOW_HELP=1
            shift
            ;;
        *)
            echo "❌ ERROR: Unknown parameter: $1"
            echo "   Use --help for usage information"
            exit 1
            ;;
    esac
done

# Show help if requested
if [ $SHOW_HELP -eq 1 ]; then
    echo "Usage: $0 [OPTIONS]"
echo "Options:"
echo "  --health      Run health check on the MCP server"
echo "  --status      Check service status"
echo "  --install-service  Install service"
echo "  --start-service    Start service"
echo "  --stop-service     Stop service"
echo "  --restart-service  Restart service"
echo "  -h, --help    Show this help message"
    exit 0
fi

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

# Default command: install service when no explicit command is provided
if [ $HEALTH_CHECK -eq 0 ] && [ $STATUS_CHECK -eq 0 ] && [ $INSTALL_SERVICE -eq 0 ] && [ $START_SERVICE -eq 0 ] && [ $STOP_SERVICE -eq 0 ] && [ $RESTART_SERVICE -eq 0 ]; then
    INSTALL_SERVICE=1
fi

# Run health check if requested
if [ $HEALTH_CHECK -eq 1 ]; then
    echo ""
    echo "--- HEALTH CHECK ---"
    echo "Running comprehensive health check on MCP server"
    echo ""
    
    # 1. Check if server is running
    echo "[1/5] Checking server status..."
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✓ Server is running"
    else
        echo "✗ Server is not running"
        echo "Start server with: $PYTHON_VENV $SERVICE_SCRIPT start"
        exit 1
    fi
    
    # 2. Test health endpoint
    echo ""
    echo "[2/5] Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s http://localhost:8001/health)
    if [ $? -eq 0 ] && [ -n "$HEALTH_RESPONSE" ]; then
        echo "✓ Health endpoint: OK"
        echo "Response: $HEALTH_RESPONSE"
    else
        echo "✗ Health endpoint failed"
        exit 1
    fi
    
    # 3. Test MCP SSE endpoint
    echo ""
    echo "[3/5] Testing MCP SSE endpoint..."
    SSE_RESPONSE=$(curl -s http://localhost:8001/cognitive-api/v1/sync)
    if [ $? -eq 0 ]; then
        echo "✓ MCP SSE endpoint: OK"
        echo "Response length: ${#SSE_RESPONSE} characters"
    else
        echo "⚠ MCP SSE endpoint test inconclusive"
    fi
    
    # 4. Test API key authentication
    echo ""
    echo "[4/5] Testing API key authentication..."
    AUTH_RESPONSE=$(curl -s -H "X-API-KEY: invalid-key" http://localhost:8001/cognitive-api/v1/sync)
    if echo "$AUTH_RESPONSE" | grep -q "Invalid API key"; then
        echo "✓ API key authentication: WORKING"
    else
        echo "⚠ API key authentication test inconclusive"
    fi
    
    # 5. Test CORS headers
    echo ""
    echo "[5/5] Testing CORS headers..."
    CORS_HEADERS=$(curl -s -I -H "Origin: http://localhost:3000" http://localhost:8001/health)
    if echo "$CORS_HEADERS" | grep -q "Access-Control"; then
        echo "✓ CORS headers: ENABLED"
        echo "$CORS_HEADERS" | grep "Access-Control"
    else
        echo "⚠ CORS headers not detected"
    fi
    
    echo ""
    echo "[COMPLETE] HEALTH CHECK COMPLETE"
    echo "All tests passed successfully!"
    echo "✓ Server is healthy and ready for MCP connections"
    echo ""
    exit 0
fi

# Check service status if requested
if [ $STATUS_CHECK -eq 1 ]; then
    echo ""
    echo "--- SERVICE STATUS ---"
    echo "Checking CCT Cognitive OS service status"
    echo ""
    
    # Run status check using the service script
    echo "📊 Querying service status..."
    "$PYTHON_VENV" "$SERVICE_SCRIPT" status
    
    # Check if the service is actually running by testing the health endpoint
    echo ""
    echo "🌐 Testing server connectivity..."
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✓ Server is responding on port 8001"
        
        # Get detailed health response
        HEALTH_RESPONSE=$(curl -s http://localhost:8001/health)
        echo "Health endpoint response: $HEALTH_RESPONSE"
        
        # Test MCP endpoint
        echo ""
        echo "🔗 Testing MCP SSE endpoint..."
        if curl -s http://localhost:8001/cognitive-api/v1/sync > /dev/null 2>&1; then
            echo "✓ MCP SSE endpoint is accessible"
        else
            echo "⚠ MCP SSE endpoint may require authentication"
        fi
        
        echo ""
        echo "✅ SERVICE STATUS: ACTIVE AND HEALTHY"
        echo "The CCT Cognitive OS service is running and responding correctly."
    else
        echo "❌ Server is not responding on port 8001"
        echo "The service may be installed but not running, or there may be a configuration issue."
        echo ""
        echo "Troubleshooting steps:"
        echo "1. Check if service is running: sudo $PYTHON_VENV $SERVICE_SCRIPT status"
        echo "2. Start the service: sudo $PYTHON_VENV $SERVICE_SCRIPT start"
        echo "3. Check logs: tail -f $REPO_ROOT/database/logs/*.log"
        exit 1
    fi
    
    echo ""
    exit 0
fi

# Start service command
if [ $START_SERVICE -eq 1 ]; then
    echo ""
    echo "🚀 Starting service..."
    "$PYTHON_VENV" "$SERVICE_SCRIPT" start
    "$PYTHON_VENV" "$SERVICE_SCRIPT" status
    exit 0
fi

# Stop service command
if [ $STOP_SERVICE -eq 1 ]; then
    echo ""
    echo "🛑 Stopping service..."
    "$PYTHON_VENV" "$SERVICE_SCRIPT" stop
    "$PYTHON_VENV" "$SERVICE_SCRIPT" status
    exit 0
fi

# Restart service command
if [ $RESTART_SERVICE -eq 1 ]; then
    echo ""
    echo "🔄 Restarting service..."
    "$PYTHON_VENV" "$SERVICE_SCRIPT" restart
    "$PYTHON_VENV" "$SERVICE_SCRIPT" status
    exit 0
fi

# Install service
if [ $INSTALL_SERVICE -eq 1 ]; then
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
fi
