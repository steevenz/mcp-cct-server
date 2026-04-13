# File: .bin/setup.ps1
# Author: Steeven Andrian — Senior Systems Architect
# Design: Laravel Artisan Style CLI

Param(
    [switch]$Force,      # Recreate venv and reset database
    [switch]$SkipDeps,   # Skip pip installation
    [switch]$Run,        # Run the server after setup
    [switch]$Help        # Show this help message
)

$Version = "1.0.0"

# --- Visual Setup ---
if ($Help) {
    Write-Host "`n  CCT COGNITIVE SERVER " -NoNewline -BackgroundColor Yellow -ForegroundColor Black
    Write-Host " $Version" -ForegroundColor DarkGray
    Write-Host "  Crafted By Steeven Andrian Salim - https://github.com/steevenz`n" -ForegroundColor Gray
    Write-Host "  USAGE: setup.ps1 [options]`n"
    Write-Host "  OPTIONS:"
    Write-Host "    --force          Force recreate .venv and reset cct_memory.db" -ForegroundColor Gray
    Write-Host "    --skip-deps      Skip installing dependencies from requirements.txt" -ForegroundColor Gray
    Write-Host "    --run            Automatically start the server after successful setup" -ForegroundColor Gray
    Write-Host "    --help           Display this help information`n"
    exit 0
}

# --- Artisan Banner ---
Write-Host "`n  CCT COGNITIVE SERVER " -NoNewline -BackgroundColor Yellow -ForegroundColor Black
Write-Host " $Version" -ForegroundColor DarkGray
Write-Host "  Crafted By Steeven Andrian Salim - https://github.com/steevenz`n" -ForegroundColor Gray

# --- Progress Helpers ---
function Show-Status ([string]$Label, [string]$Status, [string]$Color = "Green") {
    $IndentedLabel = "  " + $Label.PadRight(40, ".")
    Write-Host $IndentedLabel -NoNewline -ForegroundColor Gray
    Write-Host " [" -NoNewline -ForegroundColor Gray
    Write-Host "$Status" -NoNewline -ForegroundColor $Color
    Write-Host "]" -ForegroundColor Gray
}

# --- 1. Python Check ---
Show-Status "Verifying Python Environment" "WAITING" "Yellow"
try {
    Show-Status "Verifying Python Environment ($(python --version 2>&1))" "DONE" "Green"
} catch {
    Show-Status "Verifying Python Environment" "FAIL" "Red"
    Write-Host "`n  ERROR: Python is not installed or not in PATH.`n" -BackgroundColor Red -ForegroundColor White
    exit 1
}

# --- 2. Force Cleanup ---
if ($Force) {
    Show-Status "Forcing Clean Architecture" "CLEANING" "Yellow"
    if (Test-Path ".venv") { Remove-Item -Recurse -Force ".venv" }
    if (Test-Path "cct_memory.db") { Remove-Item "cct_memory.db" }
    Show-Status "Forcing Clean Architecture" "CLEAN" "Green"
}

# --- 3. Virtual Environment ---
if (-not (Test-Path ".venv")) {
    Show-Status "Managing Virtual Environment" "CREATING" "Yellow"
    python -m venv .venv
    Show-Status "Managing Virtual Environment" "DONE" "Green"
} else {
    Show-Status "Managing Virtual Environment" "EXISTING" "DarkCyan"
}

# --- 4. Dependencies ---
if ($SkipDeps) {
    Show-Status "Syncing Dependencies" "SKIPPED" "Cyan"
} else {
    Show-Status "Syncing Dependencies" "SYNCING" "Yellow"
    $VenvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { ".venv/bin/python" }
    if (Test-Path "requirements.txt") {
        & $VenvPython -m pip install --upgrade pip --quiet
        & $VenvPython -m pip install -r requirements.txt --quiet
        Show-Status "Syncing Dependencies" "DONE" "Green"
    } else {
        Show-Status "Syncing Dependencies" "MISSING" "Red"
    }
}

# --- 5. Environment ---
Show-Status "Auditing Configuration (.env)" "AUDITING" "Yellow"
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Show-Status "Auditing Configuration (.env)" "INITIALIZED" "Green"
    } else {
        Show-Status "Auditing Configuration (.env)" "FAILED" "Red"
    }
} else {
    Show-Status "Auditing Configuration (.env)" "VERIFIED" "DarkCyan"
}

# --- Finish ---
Write-Host "`n  SUCCESS  " -NoNewline -BackgroundColor Green -ForegroundColor Black
Write-Host " Mission Ready: CCT MCP Server is initialized.`n"

if ($Run) {
    Write-Host "  INFO  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    Write-Host " Launching Cognitive Engine...`n"
    $VenvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { ".venv/bin/python" }
    & $VenvPython src/main.py
} else {
    Write-Host "  To start the server, run:" -ForegroundColor Gray
    Write-Host "  .venv\Scripts\python src\main.py`n" -ForegroundColor Cyan
}
