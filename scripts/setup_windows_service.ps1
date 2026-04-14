# Setup Script for CCT Cognitive OS Windows Service
# Run this as Administrator

$ErrorActionPreference = "Stop"

# 1. Check for Admin Privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script MUST be run as Administrator."
}

# 2. Define Paths
$RepoRoot = Resolve-Path "$PSScriptRoot\.."
$PythonVenv = "$RepoRoot\.venv\Scripts\python.exe"
$ServiceScript = "$RepoRoot\src\os_integration\windows_service.py"

Write-Host "--- CCT Cognitive OS: Windows Service Setup ---" -ForegroundColor Cyan
Write-Host "Repository Root: $RepoRoot"
Write-Host "Using Python: $PythonVenv"

# 3. Verify Requirements
if (-not (Test-Path $PythonVenv)) {
    Write-Error "Virtual environment not found at $PythonVenv. Please run 'python -m venv .venv' first."
}

# 4. Install Service
Write-Host "`nInstalling CCTCognitiveOS service..." -ForegroundColor Yellow
& $PythonVenv $ServiceScript --startup auto install

# 5. Configure Recovery & Description
Write-Host "Configuring service recovery options..." -ForegroundColor Yellow
sc.exe failure CCTCognitiveOS reset= 86400 actions= restart/60000/restart/60000/restart/60000

# 6. Start Service
Write-Host "Starting service..." -ForegroundColor Yellow
Start-Service CCTCognitiveOS

Write-Host "`n[SUCCESS] CCT Cognitive OS is now running as a background service." -ForegroundColor Green
Write-Host "Check logs at: $RepoRoot\database\logs\cct_service.log" -ForegroundColor Gray
Write-Host "MCP SSE Endpoint: http://localhost:8000/sse" -ForegroundColor Gray
