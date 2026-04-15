# File: .bin/setup.ps1
# Author: Steeven Andrian — Senior Systems Architect
# Design: Laravel Artisan Style CLI

Param(
    [switch]$Force,          # Recreate venv and reset database
    [switch]$SkipDeps,       # Skip pip installation
    [switch]$Run,            # Run the server after setup
    [switch]$InstallService, # Install as Windows Service
    [switch]$MultiAgent,     # Configure for multi-agent mode
    [switch]$CleanReqs,      # Clean and reinstall requirements
    [int]$Port = 0,          # Server port (0 = auto 8001)
    [switch]$Help            # Show this help message
)

$Version = "2.0.0"
$CCT_Default_Port = if ($Port -gt 0) { $Port } else { 8001 }
$MinPythonVersion = [Version]"3.8.0"

# --- Auto-Elevation for Service Installation ---
if ($InstallService) {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-Host "`n  ELEVATION REQUIRED  " -NoNewline -BackgroundColor Yellow -ForegroundColor Black
        Write-Host " Windows Service installation requires Administrator privileges.`n" -ForegroundColor Yellow
        Write-Host "  Requesting elevation..." -ForegroundColor Gray
        
        # Re-run this script with elevated privileges
        $scriptPath = $MyInvocation.MyCommand.Definition
        $argString = "-InstallService"
        if ($Force) { $argString += " -Force" }
        if ($SkipDeps) { $argString += " -SkipDeps" }
        if ($CleanReqs) { $argString += " -CleanReqs" }
        if ($Run) { $argString += " -Run" }
        if ($MultiAgent) { $argString += " -MultiAgent" }
        if ($Port -gt 0) { $argString += " -Port $Port" }
        
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`" $argString" -Verb RunAs
        exit 0
    }
}

# --- Helper Functions ---
function Check-Admin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-PortInUse {
    param([int]$Port)
    try {
        $listener = New-Object System.Net.Sockets.TcpListener ([System.Net.IPAddress]::Any), $Port
        $listener.Start()
        $listener.Stop()
        return $false
    } catch {
        return $true
    }
}

function Find-AvailablePort {
    param([int]$StartPort = 8000, [int]$MaxPort = 9000)
    for ($port = $StartPort; $port -le $MaxPort; $port++) {
        if (-not (Test-PortInUse -Port $port)) {
            return $port
        }
    }
    return $null
}

function Test-CCTProcessRunning {
    # Check for existing Python processes running main.py
    $processes = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | 
        Where-Object { $_.CommandLine -match "main\.py" }
    return $processes.Count -gt 0
}

function Test-CCTServiceRunning {
    try {
        $service = Get-Service -Name "CCTMCPServer" -ErrorAction SilentlyContinue
        if ($service -and $service.Status -eq "Running") {
            return $true
        }
    } catch {}
    return $false
}

function Test-CCTServiceExists {
    try {
        $service = Get-Service -Name "CCTMCPServer" -ErrorAction SilentlyContinue
        return $service -ne $null
    } catch {}
    return $false
}

function Get-CCTServiceStatus {
    try {
        $service = Get-Service -Name "CCTMCPServer" -ErrorAction SilentlyContinue
        if ($service) {
            return $service.Status.ToString()
        }
    } catch {}
    return "NOT_INSTALLED"
}

function Check-PythonVersion {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+\.\d+\.\d+)") {
        $version = [Version]$matches[1]
        if ($version -lt $MinPythonVersion) {
            Write-Host "`n  ERROR: Python $version is not supported. Minimum required: $MinPythonVersion`n" -BackgroundColor Red -ForegroundColor White
            exit 1
        }
        return $true
    }
    return $false
}

# --- Visual Setup ---
if ($Help) {
    Write-Host "`n  CCT COGNITIVE SERVER " -NoNewline -BackgroundColor Yellow -ForegroundColor Black
    Write-Host " $Version" -ForegroundColor DarkGray
    Write-Host "  Crafted By Steeven Andrian Salim - https://github.com/steevenz`n" -ForegroundColor Gray
    Write-Host "  USAGE: setup.ps1 [options]`n"
    Write-Host "  OPTIONS:"
    Write-Host "    -Force              Force recreate .venv and reset cct_memory.db" -ForegroundColor Gray
    Write-Host "    -SkipDeps           Skip installing dependencies from requirements.txt" -ForegroundColor Gray
    Write-Host "    -CleanReqs          Clean and reinstall all requirements" -ForegroundColor Gray
    Write-Host "    -Run                Automatically start the server after successful setup" -ForegroundColor Gray
    Write-Host "    -InstallService     Install as Windows Service (auto-elevates to Admin)" -ForegroundColor Gray
    Write-Host "    -MultiAgent         Configure for multi-agent shared server mode" -ForegroundColor Gray
    Write-Host "    -Port <n>           Set server port (default: 8001)" -ForegroundColor Gray
    Write-Host "    -Help               Display this help information`n" -ForegroundColor Gray
    Write-Host "  WINDOWS SERVICE:" -ForegroundColor Yellow
    Write-Host "    -InstallService     Install as Windows Service (runs on boot)" -ForegroundColor Gray
    Write-Host "    Auto-elevates:      Automatically requests Admin if not elevated" -ForegroundColor Gray
    Write-Host "    Start service: sc start CCTMCPServer" -ForegroundColor Cyan
    Write-Host "    Stop service:  sc stop CCTMCPServer`n"
    Write-Host "  MULTI-AGENT MODE:" -ForegroundColor Yellow
    Write-Host "    Run server once, all AI agents share it. Prevents port conflicts." -ForegroundColor Gray
    Write-Host "    Example: setup.ps1 --multi-agent --run`n" -ForegroundColor Cyan
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
    if (Check-PythonVersion) {
        $pythonVersion = python --version 2>&1
        Show-Status "Verifying Python Environment ($pythonVersion)" "DONE" "Green"
    } else {
        Show-Status "Verifying Python Environment" "FAIL" "Red"
        Write-Host "`n  ERROR: Python is not installed or not in PATH.`n" -BackgroundColor Red -ForegroundColor White
        exit 1
    }
} catch {
    Show-Status "Verifying Python Environment" "FAIL" "Red"
    Write-Host "`n  ERROR: Python check failed.`n" -BackgroundColor Red -ForegroundColor White
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
    
    if ($CleanReqs) {
        Show-Status "Cleaning Dependencies" "CLEANING" "Yellow"
        & $VenvPython -m pip freeze | ForEach-Object { & $VenvPython -m pip uninstall -y $_ --quiet 2>$null }
        Show-Status "Cleaning Dependencies" "CLEAN" "Green"
    }
    
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

# --- 5.5. Multi-Agent Server Configuration ---
if ($MultiAgent -or $Port -gt 0) {
    Show-Status "Configuring Multi-Agent Server" "CONFIGURING" "Yellow"
    
    # Read existing .env
    $envContent = Get-Content ".env" -Raw
    
    # Update port
    if ($envContent -match "CCT_PORT=") {
        $envContent = $envContent -replace "CCT_PORT=.*", "CCT_PORT=$CCT_Default_Port"
    } else {
        $envContent += "`nCCT_PORT=$CCT_Default_Port"
    }
    
    # Set transport to SSE for multi-agent
    if ($MultiAgent) {
        if ($envContent -match "CCT_TRANSPORT=") {
            $envContent = $envContent -replace "CCT_TRANSPORT=.*", "CCT_TRANSPORT=sse"
        } else {
            $envContent += "`nCCT_TRANSPORT=sse"
        }
    }
    
    # Save updated .env
    Set-Content ".env" $envContent
    
    Show-Status "Configuring Multi-Agent Server" "PORT=$CCT_Default_Port" "Green"
}

# --- 6. Windows Service Installation ---
if ($InstallService) {
    Show-Status "Installing Windows Service" "CHECKING" "Yellow"
    
    if (-not (Check-Admin)) {
        Show-Status "Installing Windows Service" "DENIED" "Red"
        Write-Host "`n  ERROR: Administrator privileges required for Windows Service installation.`n" -BackgroundColor Red -ForegroundColor White
        Write-Host "  Please run this script as Administrator.`n" -ForegroundColor Yellow
        exit 1
    }
    
    # Check for existing service installation
    $serviceStatus = Get-CCTServiceStatus
    
    if ($serviceStatus -eq "Running") {
        Show-Status "Checking Service Status" "ALREADY RUNNING" "Yellow"
        Write-Host "`n  WARNING: CCTMCPServer service is already installed and RUNNING." -ForegroundColor Yellow
        Write-Host "  Options:" -ForegroundColor White
        Write-Host "    1. Stop service:        sc stop CCTMCPServer" -ForegroundColor Cyan
        Write-Host "    2. Then reinstall:    Run this script again`n" -ForegroundColor Cyan
        exit 1
    }
    
    if ($serviceStatus -eq "Stopped") {
        Show-Status "Checking Service Status" "STOPPED - NEEDS REINSTALL" "Yellow"
        Write-Host "`n  WARNING: CCTMCPServer service exists but is STOPPED." -ForegroundColor Yellow
        Write-Host "  Kill (remove) existing service and reinstall? (Y/N)" -NoNewline -ForegroundColor White
        $response = Read-Host
        if ($response -eq 'Y' -or $response -eq 'y') {
            Show-Status "Removing Old Service" "IN PROGRESS" "Yellow"
            try {
                sc.exe delete CCTMCPServer | Out-Null
                Start-Sleep -Seconds 2
                Show-Status "Removing Old Service" "DONE" "Green"
            } catch {
                Show-Status "Removing Old Service" "ERROR" -Color "Red"
                Write-Host "  Manual removal: sc delete CCTMCPServer`n" -ForegroundColor Yellow
                exit 1
            }
        } else {
            Write-Host "`n  Installation cancelled. Remove manually with: sc delete CCTMCPServer`n" -ForegroundColor Yellow
            exit 0
        }
    }
    
    if (Test-CCTProcessRunning) {
        Show-Status "Checking Process Status" "CONFLICT DETECTED" "Yellow"
        Write-Host "`n  WARNING: CCT main.py is already running as standalone process." -ForegroundColor Yellow
        Write-Host "  This may cause port conflicts. Kill existing process? (Y/N)" -NoNewline -ForegroundColor White
        $response = Read-Host
        if ($response -eq 'Y' -or $response -eq 'y') {
            Get-CimInstance Win32_Process -Filter "Name='python.exe'" | 
                Where-Object { $_.CommandLine -match "main\.py" } | 
                ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
            Show-Status "Terminating Conflicts" "DONE" "Green"
        }
    }
    
    # Auto-select port if default is in use
    if (Test-PortInUse -Port $CCT_Default_Port) {
        $newPort = Find-AvailablePort -StartPort ($CCT_Default_Port + 1)
        if ($newPort) {
            Show-Status "Port $CCT_Default_Port in use" "SWITCHING TO $newPort" "Yellow"
            $CCT_Default_Port = $newPort
            
            # Update .env with new port
            $envContent = Get-Content ".env" -Raw
            if ($envContent -match "CCT_PORT=") {
                $envContent = $envContent -replace "CCT_PORT=.*", "CCT_PORT=$CCT_Default_Port"
            } else {
                $envContent += "`nCCT_PORT=$CCT_Default_Port"
            }
            Set-Content ".env" $envContent
        } else {
            Show-Status "Port Availability" "NO PORTS AVAILABLE" "Red"
            Write-Host "`n  ERROR: No available ports found between 8000-9000.`n" -BackgroundColor Red -ForegroundColor White
            exit 1
        }
    }
    
    Show-Status "Installing Windows Service" "INSTALLING" "Yellow"
    
    $ServiceScript = "src\core\services\windows\background.py"
    if (Test-Path $ServiceScript) {
        & $VenvPython $ServiceScript install
        Show-Status "Installing Windows Service" "INSTALLED" "Green"
        
        Write-Host "`n  INFO  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
        Write-Host " Start service with: " -NoNewline
        Write-Host "sc start CCTMCPServer" -ForegroundColor Yellow
        Write-Host "  Or use: python scripts\setup\services\windows\service.py start`n" -ForegroundColor Gray
    } else {
        Show-Status "Installing Windows Service" "NOT FOUND" "Red"
    }
}

# --- Finish ---
Write-Host "`n  SUCCESS  " -NoNewline -BackgroundColor Green -ForegroundColor Black
Write-Host " Mission Ready: CCT MCP Server is initialized.`n"

# Display multi-agent banner if configured
if ($MultiAgent) {
    Write-Host "  MULTI-AGENT MODE  " -NoNewline -BackgroundColor Magenta -ForegroundColor White
    Write-Host " Server configured for shared access`n"
    Write-Host "  Quick Start:" -ForegroundColor Yellow
    Write-Host "  1. Start server:    .venv\Scripts\python src\main.py" -ForegroundColor Cyan
    Write-Host "  2. Or use manager:   scripts\server\manage.py start" -ForegroundColor Cyan
    Write-Host "  3. Connect agents:  http://localhost:$CCT_Default_Port" -ForegroundColor Cyan
    Write-Host "  4. Example:         python examples\multi_agent_example.py`n" -ForegroundColor Gray
}

if ($Run) {
    Write-Host "  INFO  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    if ($MultiAgent) {
        Write-Host " Launching Multi-Agent Shared Server...`n"
    } else {
        Write-Host " Launching Cognitive Engine...`n"
    }
    $VenvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { ".venv/bin/python" }
    & $VenvPython src/main.py
} else {
    if (-not $MultiAgent) {
        Write-Host "  To start the server, run:" -ForegroundColor Gray
        Write-Host "  .venv\Scripts\python src\main.py`n" -ForegroundColor Cyan
    }
}
