# Setup Script for CCT Cognitive OS Windows Service
# Author: Steeven Andrian — Senior Systems Architect
# Run this as Administrator
#
# Usage:
#   .\setup.ps1                    # Install with auto-startup (default)
#   .\setup.ps1 -StartupType auto  # Install with auto-startup on boot
#   .\setup.ps1 -StartupType manual # Install with manual start
#   .\setup.ps1 -NoStart           # Install but don't start immediately

param(
    [ValidateSet("auto", "manual")]
    [string]$StartupType = "auto",
    
    [switch]$NoStart  # Don't start service immediately after install
)

$ErrorActionPreference = "Stop"

# 1. Check for Admin Privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script MUST be run as Administrator."
}

# 2. Define Paths
$RepoRoot = Resolve-Path "$PSScriptRoot\.."
$PythonVenv = "$RepoRoot\.venv\Scripts\python.exe"
$ServiceScript = "$RepoRoot\src\core\services\windows\background.py"

Write-Host "--- CCT Cognitive OS: Windows Service Setup ---" -ForegroundColor Cyan
Write-Host "Repository Root: $RepoRoot"
Write-Host "Using Python: $PythonVenv"

# 3. Verify Requirements
if (-not (Test-Path $PythonVenv)) {
    Write-Error "Virtual environment not found at $PythonVenv. Please run 'python -m venv .venv' first."
}

# 4. Install Service
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
Write-Host "MCP SSE Endpoint: http://localhost:8000/sse" -ForegroundColor Gray
