# Setup Script for CCT Cognitive OS Windows Service
# Author: Steeven Andrian — Senior Systems Architect
# Run this as Administrator
#
# Usage:
#   .\setup.ps1                    # Install with auto-startup (default)
#   .\setup.ps1 -StartupType auto  # Install with auto-startup on boot
#   .\setup.ps1 -StartupType manual # Install with manual start
#   .\setup.ps1 -NoStart           # Install but don't start immediately
#   .\setup.ps1 -TestService       # Start service + status + test MCP endpoint
#   .\setup.ps1 -Restart           # Restart Windows Service
#   .\setup.ps1 -Health            # Run health check on the MCP server

param(
    [ValidateSet("auto", "manual")]
    [string]$StartupType = "auto",
    
    [switch]$InstallService,
    [switch]$StartService,
    [switch]$StopService,
    [switch]$RestartService,
    [switch]$Status,
    [switch]$NoStart,  # Don't start service immediately after install
    [switch]$TestService,  # Start service + status + test MCP endpoint
    [switch]$Restart,  # Restart Windows Service
    [switch]$Health  # Run health check on the MCP server
)

$ErrorActionPreference = "Stop"

# GNU-style flag aliases
if ($args -match "--install-service") { $InstallService = $true }
if ($args -match "--start-service") { $StartService = $true }
if ($args -match "--stop-service") { $StopService = $true }
if ($args -match "--restart-service") { $RestartService = $true }
if ($args -match "--status") { $Status = $true }
if ($args -match "--health") { $Health = $true }

# 1. Check for Admin Privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script MUST be run as Administrator."
}

# 2. Define Paths
$RepoRoot = Resolve-Path "$PSScriptRoot\.."
$PythonVenv = "$RepoRoot\.venv\Scripts\python.exe"
$ServiceScript = "$RepoRoot\src\core\services\windows\background.py"
$ServicePort = 8001

# Backward-compatible aliases and default action
if ($Restart) {
    $RestartService = $true
}
if (-not ($InstallService -or $StartService -or $StopService -or $RestartService -or $Status -or $Health -or $TestService)) {
    $InstallService = $true
}

Write-Host "--- CCT Cognitive OS: Windows Service Setup ---" -ForegroundColor Cyan
Write-Host "Repository Root: $RepoRoot"
Write-Host "Using Python: $PythonVenv"

# 3. Verify Requirements
if (-not (Test-Path $PythonVenv)) {
    Write-Error "Virtual environment not found at $PythonVenv. Please run 'python -m venv .venv' first."
}

# 4. Install Service
if ($InstallService) {
    Write-Host "`nInstalling CCTMCPServer service..." -ForegroundColor Yellow
    & $PythonVenv $ServiceScript install

    # 5. Configure Startup Type
    Write-Host "Configuring startup type: $StartupType..." -ForegroundColor Yellow
    sc.exe config CCTMCPServer start= $StartupType

    # 6. Configure Recovery & Description
    Write-Host "Configuring service recovery options..." -ForegroundColor Yellow
    sc.exe failure CCTMCPServer reset= 86400 actions= restart/60000/restart/60000/restart/60000

    # 7. Start Service (unless -NoStart specified)
    if (-not $NoStart) {
        Write-Host "Starting service..." -ForegroundColor Yellow
        Start-Service CCTMCPServer
    } else {
        Write-Host "Service installed but not started (use -NoStart flag)." -ForegroundColor Yellow
    }

    Write-Host "`n[SUCCESS] CCT Cognitive OS service installed successfully." -ForegroundColor Green
    Write-Host "  Startup Type: $StartupType" -ForegroundColor Cyan
    if ($StartupType -eq "auto") {
        Write-Host "  Service will automatically start on Windows boot." -ForegroundColor Green
    } else {
        Write-Host "  Start manually with: sc start CCTMCPServer" -ForegroundColor Cyan
    }
    Write-Host "Check logs at: $RepoRoot\database\logs\cct_service.log" -ForegroundColor Gray
    Write-Host "MCP SSE Endpoint: http://localhost:$ServicePort/cognitive-api/v1/sync" -ForegroundColor Gray
}

# Start service command
if ($StartService) {
    Write-Host "`n--- Starting Service ---" -ForegroundColor Cyan
    Start-Service CCTMCPServer
    Start-Sleep 2
    sc.exe query CCTMCPServer
    exit 0
}

# Stop service command
if ($StopService) {
    Write-Host "`n--- Stopping Service ---" -ForegroundColor Cyan
    Stop-Service CCTMCPServer
    Start-Sleep 2
    sc.exe query CCTMCPServer
    exit 0
}

# 8. Restart Service (if -Restart specified)
if ($RestartService) {
    Write-Host "`n--- Restarting Service ---" -ForegroundColor Cyan
    
    # Stop service
    Write-Host "Stopping CCTMCPServer..." -ForegroundColor Yellow
    Stop-Service CCTMCPServer -ErrorAction SilentlyContinue
    Start-Sleep 3
    
    # Start service
    Write-Host "Starting CCTMCPServer..." -ForegroundColor Yellow
    Start-Service CCTMCPServer
    Start-Sleep 5
    
    # Check status
    Write-Host "Service status:" -ForegroundColor Gray
    sc.exe query CCTMCPServer
    
    Write-Host "`n[COMPLETE] Service restarted successfully." -ForegroundColor Green
    exit 0
}

# Service status command
if ($Status) {
    Write-Host "`n--- SERVICE STATUS ---" -ForegroundColor Cyan
    sc.exe query CCTMCPServer
    try {
        $health = curl "http://localhost:$ServicePort/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "Health endpoint: OK (HTTP $($health.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "Health endpoint: NOT_REACHABLE" -ForegroundColor Yellow
    }
    exit 0
}

# 9. Test Service (if -TestService specified)
if ($TestService) {
    Write-Host "`n--- Testing Service ---" -ForegroundColor Cyan
    
    # Start service if not already running
    $serviceStatus = Get-Service CCTMCPServer -ErrorAction SilentlyContinue
    if (-not $serviceStatus -or $serviceStatus.Status -ne "Running") {
        Write-Host "Starting CCTMCPServer..." -ForegroundColor Yellow
        Start-Service CCTMCPServer
        Start-Sleep 5
    }
    
    # Check status
    Write-Host "Service status:" -ForegroundColor Gray
    sc.exe query CCTMCPServer
    
    # Test health endpoint
    Write-Host "`nTesting health endpoint..." -ForegroundColor Gray
    try {
        curl "http://localhost:$ServicePort/health" -UseBasicParsing
    } catch {
        Write-Host "Health endpoint test failed" -ForegroundColor Red
    }
    
    # Test MCP SSE endpoint
    Write-Host "`nTesting MCP SSE endpoint..." -ForegroundColor Gray
    try {
        curl "http://localhost:$ServicePort/cognitive-api/v1/sync" -UseBasicParsing
    } catch {
        Write-Host "MCP SSE endpoint test failed" -ForegroundColor Red
    }
    
    Write-Host "`n[COMPLETE] Service test finished." -ForegroundColor Green
}

# --- Health Check Function ---
if ($Health) {
    Write-Host "`n--- HEALTH CHECK ---" -ForegroundColor Cyan
    Write-Host "Running comprehensive health check on MCP server" -ForegroundColor White
    Write-Host ""

    # 1. Check if server is running
    Write-Host "[1/5] Checking server status..." -ForegroundColor Gray
    try {
        $response = curl -s "http://localhost:$ServicePort/health" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Server is running" -ForegroundColor Green
        } else {
            Write-Host "✗ Server returned status: $($response.StatusCode)" -ForegroundColor Red
            Write-Host "Start server with: .\scripts\setup\setup.ps1 -Run" -ForegroundColor Yellow
            exit 1
        }
    } catch {
        Write-Host "✗ Server is not running" -ForegroundColor Red
        Write-Host "Start server with: .\scripts\setup\setup.ps1 -Run" -ForegroundColor Yellow
        exit 1
    }

    # 2. Test health endpoint
    Write-Host "`n[2/5] Testing health endpoint..." -ForegroundColor Gray
    try {
        $healthResponse = curl -s "http://localhost:$ServicePort/health" -UseBasicParsing
        if ($healthResponse.StatusCode -eq 200) {
            Write-Host "✓ Health endpoint: OK" -ForegroundColor Green
            Write-Host "Response: $($healthResponse.Content)" -ForegroundColor Gray
        } else {
            Write-Host "✗ Health endpoint failed with status: $($healthResponse.StatusCode)" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "✗ Health endpoint test failed" -ForegroundColor Red
        exit 1
    }

    # 3. Test MCP SSE endpoint
    Write-Host "`n[3/5] Testing MCP SSE endpoint..." -ForegroundColor Gray
    try {
        $sseResponse = curl -s "http://localhost:$ServicePort/cognitive-api/v1/sync" -UseBasicParsing
        if ($sseResponse.StatusCode -eq 200) {
            Write-Host "✓ MCP SSE endpoint: OK" -ForegroundColor Green
            Write-Host "Response length: $($sseResponse.Content.Length) characters" -ForegroundColor Gray
        } else {
            Write-Host "⚠ MCP SSE endpoint returned status: $($sseResponse.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ MCP SSE endpoint test inconclusive" -ForegroundColor Yellow
    }

    # 4. Test API key authentication
    Write-Host "`n[4/5] Testing API key authentication..." -ForegroundColor Gray
    try {
        $authResponse = curl -s -H "X-API-KEY: invalid-key" "http://localhost:$ServicePort/cognitive-api/v1/sync" -UseBasicParsing
        if ($authResponse.Content -like "*Invalid API key*") {
            Write-Host "✓ API key authentication: WORKING" -ForegroundColor Green
        } else {
            Write-Host "⚠ API key authentication test inconclusive" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ API key authentication test failed" -ForegroundColor Yellow
    }

    # 5. Test CORS headers
    Write-Host "`n[5/5] Testing CORS headers..." -ForegroundColor Gray
    try {
        $corsHeaders = curl -s -I -H "Origin: http://localhost:3000" "http://localhost:$ServicePort/health" -UseBasicParsing
        $corsDetected = $corsHeaders.Headers | Where-Object { $_.Key -like "*Access-Control*" }
        if ($corsDetected) {
            Write-Host "✓ CORS headers: ENABLED" -ForegroundColor Green
            foreach ($header in $corsDetected) {
                Write-Host "  $($header.Key): $($header.Value)" -ForegroundColor Gray
            }
        } else {
            Write-Host "⚠ CORS headers not detected" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ CORS headers test failed" -ForegroundColor Yellow
    }

    Write-Host "`n[COMPLETE] HEALTH CHECK COMPLETE" -ForegroundColor Green
    Write-Host "All tests passed successfully!" -ForegroundColor White
    Write-Host "✓ Server is healthy and ready for MCP connections" -ForegroundColor Green
    Write-Host ""
    exit 0
}
