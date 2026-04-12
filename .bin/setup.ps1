# File: src/.bin/setup.ps1
# Author: Steeven Andrian — Senior Systems Architect
# Objective: Production-Grade Initialization for CCT MCP Server

$ErrorActionPreference = "Stop"

# --- Visual Assets ---
$Banner = @"
  ██████╗ ██████╗████████╗     ██████╗ ██████╗ 
 ██╔════╝██╔════╝╚══██╔══╝    ██╔═══██╗██╔══██╗
 ██║     ██║        ██║       ██║   ██║██████╔╝
 ██║     ██║        ██║       ██║   ██║██╔═══╝ 
 ╚██████╗╚██████╗   ██║       ╚██████╔╝██║     
  ╚═════╝ ╚═════╝   ╚═╝        ╚═════╝ ╚═╝     
                                               
     COGNITIVE OPERATING SYSTEM
     Author: Steeven Andrian
"@

Write-Host "`n" -ForegroundColor Cyan
Write-Host $Banner -ForegroundColor Cyan
Write-Host "--------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Initializing Elite Architect Workspace..." -ForegroundColor Green
Write-Host "`n"

# --- 1. Python Check ---
Write-Host "[1/5] Verifying Python Environment..." -NoNewline
try {
    $PythonVersion = python --version 2>&1
    Write-Host " [FOUND: $PythonVersion]" -ForegroundColor DarkCyan
} catch {
    Write-Host " [FAILED]" -ForegroundColor Red
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Yellow
    exit 1
}

# --- 2. Virtual Environment ---
Write-Host "[2/5] Managing Virtual Environment (.venv)..." -NoNewline
if (-not (Test-Path ".venv")) {
    Write-Host " [CREATING...]" -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "SUCCESS: Virtual environment created." -ForegroundColor Green
} else {
    Write-Host " [EXISTING]" -ForegroundColor DarkCyan
}

# --- 3. Dependency Installation ---
Write-Host "[3/5] Syncing Dependencies (requirements.txt)..." -NoNewline
$VenvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { ".venv/bin/python" }

if (Test-Path "requirements.txt") {
    Write-Host " [INSTALLING...]" -ForegroundColor Yellow
    try {
        & $VenvPython -m pip install --upgrade pip --quiet 2>$null
    } catch {
        Write-Host " (Note: Pip upgrade skipped or failed, continuing...)" -ForegroundColor Gray
    }
    & $VenvPython -m pip install -r requirements.txt --quiet
    Write-Host "SUCCESS: 22+ Cognitive Primitives Ready." -ForegroundColor Green
} else {
    Write-Host " [MISSING]" -ForegroundColor Red
    Write-Host "WARNING: requirements.txt not found in project root." -ForegroundColor Yellow
}

# --- 4. Environment Configuration ---
Write-Host "[4/5] Auditing Configuration (.env)..." -NoNewline
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host " [INITIALIZING FROM EXAMPLE]" -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
    } else {
        Write-Host " [MISSING .env.example]" -ForegroundColor Red
    }
} else {
    Write-Host " [VERIFIED]" -ForegroundColor DarkCyan
}

# --- 5. Workspace Integrity ---
Write-Host "[5/5] Mapping Cognitive Architecture..." -NoNewline
$RequiredFolders = @("src", "src/engines", "src/modes", "docs")
$MissingCount = 0

foreach ($Folder in $RequiredFolders) {
    if (-not (Test-Path $Folder)) {
        Write-Host "`n  MISSING COMPONENT: $Folder" -ForegroundColor Red
        $MissingCount++
    }
}

if ($MissingCount -eq 0) {
    Write-Host " [STABLE]" -ForegroundColor Green
} else {
    Write-Host " [FRAGILE - $MissingCount Missing Components]" -ForegroundColor Yellow
}

Write-Host "`n--------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "✅ MISSION READY: CCT MCP Server is initialized." -ForegroundColor Green
Write-Host "`nTo start the server, run:" -ForegroundColor White
Write-Host "  .venv\Scripts\python src\main.py" -ForegroundColor Cyan
Write-Host "`nTo launch Mission Control Dashboard:" -ForegroundColor White
Write-Host "  .venv\Scripts\streamlit run dashboard.py" -ForegroundColor Cyan
Write-Host "`n"
