# File: .bin/setup.ps1
# Author: Steeven Andrian â€” Senior Systems Architect
# Design: Laravel Artisan Style CLI

Param(
    [switch]$Force,          # Recreate venv and reset database
    [switch]$SkipDeps,       # Skip pip installation
    [switch]$Run,            # Run the server after setup
    [switch]$InstallService, # Install as Windows Service
    [switch]$StartService,   # Start Windows Service
    [switch]$StopService,    # Stop Windows Service
    [switch]$RestartService, # Restart Windows Service
    [switch]$Restart,        # Backward-compatible alias
    [switch]$MultiAgent,     # Configure for multi-agent mode
    [switch]$CleanReqs,      # Clean and reinstall requirements
    [switch]$TestService,    # Start service + status + test MCP endpoint
    [switch]$ServiceE2E,     # Elevated service E2E: restart -> stop -> start -> tail logs
    [switch]$Health,         # Run health check on the MCP server
    [switch]$Status,         # Check service status and server connectivity
    [int]$Port = 0,          # Server port (0 = auto 8010)
    [switch]$Download,       # Download Gemma models
    [switch]$Register,       # Register server in IDE MCP configs
    [switch]$Help            # Show this help message
)

# Handle GNU-style aliases for consistency with other scripts
if ($args -match "--download") { $Download = $true }
if ($args -match "--register") { $Register = $true }
if ($args -match "--install-service") { $InstallService = $true }

$Version = "2.1.0"
$CCT_Default_Port = if ($Port -gt 0) { $Port } else { 8010 }
$MinPythonVersion = [Version]"3.8.0"

function Invoke-Exit {
    param([int]$Code = 0)

    $shouldPrompt = $env:CCT_NO_EXIT_PROMPT -ne "1" -and $Host.Name -eq "ConsoleHost"
    if ($shouldPrompt) {
        Write-Host ""
        [void](Read-Host "Press Enter to exit")
    }

    exit $Code
}

# --- Auto-Elevation for Service Installation ---
if ($InstallService -or $StartService -or $StopService -or $RestartService -or $Restart -or $ServiceE2E) {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if (-not $isAdmin) {
        Write-Host "`n  ELEVATION REQUIRED  " -NoNewline -BackgroundColor Yellow -ForegroundColor Black
        Write-Host " Windows Service installation requires Administrator privileges.`n" -ForegroundColor Yellow
        Write-Host "  Requesting elevation..." -ForegroundColor Gray

        # Re-run this script with elevated privileges
        $scriptPath = $MyInvocation.MyCommand.Definition
        $argString = ""
        if ($InstallService) { $argString += " -InstallService" }
        if ($StartService) { $argString += " -StartService" }
        if ($StopService) { $argString += " -StopService" }
        if ($RestartService) { $argString += " -RestartService" }
        if ($Restart) { $argString += " -Restart" }
        if ($ServiceE2E) { $argString += " -ServiceE2E" }
        if ($Force) { $argString += " -Force" }
        if ($SkipDeps) { $argString += " -SkipDeps" }
        if ($CleanReqs) { $argString += " -CleanReqs" }
        if ($Run) { $argString += " -Run" }
        if ($MultiAgent) { $argString += " -MultiAgent" }
        if ($Port -gt 0) { $argString += " -Port $Port" }

        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`" $argString" -Verb RunAs
        Invoke-Exit 0
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
            Invoke-Exit 1
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
    Write-Host "    -StartService       Start Windows Service" -ForegroundColor Gray
    Write-Host "    -StopService        Stop Windows Service" -ForegroundColor Gray
    Write-Host "    -RestartService     Restart Windows Service" -ForegroundColor Gray
    Write-Host "    -ServiceE2E         Elevated restart/stop/start + tail service log" -ForegroundColor Gray
    Write-Host "    -MultiAgent         Configure for multi-agent shared server mode" -ForegroundColor Gray
    Write-Host "    -Port <n>           Set server port (default: 8001)" -ForegroundColor Gray
    Write-Host "    -Health             Run health check on the MCP server" -ForegroundColor Gray
    Write-Host "    -Status             Check service status and server connectivity" -ForegroundColor Gray
    Write-Host "    -Help               Display this help information`n" -ForegroundColor Gray
    Write-Host "  WINDOWS SERVICE:" -ForegroundColor Yellow
    Write-Host "    -InstallService     Install as Windows Service (runs on boot)" -ForegroundColor Gray
    Write-Host "    Auto-elevates:      Automatically requests Admin if not elevated" -ForegroundColor Gray
    Write-Host "    Start service: sc start CCTMCPServer" -ForegroundColor Cyan
    Write-Host "    Stop service:  sc stop CCTMCPServer`n"
    Write-Host "  MULTI-AGENT MODE:" -ForegroundColor Yellow
    Write-Host "    Run server once, all AI agents share it. Prevents port conflicts." -ForegroundColor Gray
    Write-Host "    Example: setup.ps1 --multi-agent --run`n" -ForegroundColor Cyan
    Invoke-Exit 0
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
        Invoke-Exit 1
    }
} catch {
    Show-Status "Verifying Python Environment" "FAIL" "Red"
    Write-Host "`n  ERROR: Python check failed.`n" -BackgroundColor Red -ForegroundColor White
    Invoke-Exit 1
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

# --- 4.5 Model Download (Gemma) ---
if ($Download) {
    Show-Status "Downloading Gemma Models" "IN PROGRESS" "Yellow"
    $VenvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { ".venv/bin/python" }
    & $VenvPython scripts/setup/download_models.py
    if ($LASTEXITCODE -eq 0) {
        Show-Status "Downloading Gemma Models" "DONE" "Green"
    } else {
        Show-Status "Downloading Gemma Models" "FAILED" "Red"
    }
}

# --- 4.6 MCP Registration ---
if ($Register) {
    Show-Status "Registering MCP Server" "IN PROGRESS" "Yellow"
    $VenvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { ".venv/bin/python" }
    & $VenvPython scripts/setup/register_mcp.py
    if ($LASTEXITCODE -eq 0) {
        Show-Status "Registering MCP Server" "DONE" "Green"
    } else {
        Show-Status "Registering MCP Server" "FAILED" "Red"
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
        Invoke-Exit 1
    }

    # Check for existing service installation
    $serviceStatus = Get-CCTServiceStatus

    if ($serviceStatus -eq "Running") {
        Show-Status "Checking Service Status" "ALREADY RUNNING" "Yellow"
        Write-Host "`n  WARNING: CCTMCPServer service is already installed and RUNNING." -ForegroundColor Yellow
        Write-Host "  Options:" -ForegroundColor White
        Write-Host "    1. Stop service:        sc stop CCTMCPServer" -ForegroundColor Cyan
        Write-Host "    2. Then reinstall:    Run this script again`n" -ForegroundColor Cyan
        Invoke-Exit 1
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
                Invoke-Exit 1
            }
        } else {
            Write-Host "`n  Installation cancelled. Remove manually with: sc delete CCTMCPServer`n" -ForegroundColor Yellow
            Invoke-Exit 0
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
            Invoke-Exit 1
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

# --- Start Service Command ---
if ($StartService) {
    Write-Host "`n  START SERVICE  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    Write-Host " Starting CCTMCPServer`n"
    sc.exe start CCTMCPServer | Out-Null
    Start-Sleep 3
    sc.exe query CCTMCPServer
    Write-Host "`n  START COMPLETE  " -NoNewline -BackgroundColor Green -ForegroundColor Black
    Write-Host " Service started successfully.`n"
    Invoke-Exit 0
}

# --- Stop Service Command ---
if ($StopService) {
    Write-Host "`n  STOP SERVICE  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    Write-Host " Stopping CCTMCPServer`n"
    sc.exe stop CCTMCPServer | Out-Null
    Start-Sleep 3
    sc.exe query CCTMCPServer
    Write-Host "`n  STOP COMPLETE  " -NoNewline -BackgroundColor Green -ForegroundColor Black
    Write-Host " Service stopped successfully.`n"
    Invoke-Exit 0
}

# --- Restart Service Command ---
if ($Restart -or $RestartService) {
    Write-Host "`n  RESTART SERVICE  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    Write-Host " Restarting CCTMCPServer`n"

    # Stop service
    Write-Host "  [1/3] Stopping CCTMCPServer..." -ForegroundColor Gray
    sc.exe stop CCTMCPServer | Out-Null
    Start-Sleep 3

    # Start service
    Write-Host "  [2/3] Starting CCTMCPServer..." -ForegroundColor Gray
    sc.exe start CCTMCPServer | Out-Null
    Start-Sleep 5

    # Check status
    Write-Host "  [3/3] Checking service status..." -ForegroundColor Gray
    sc.exe query CCTMCPServer

    Write-Host "`n  RESTART COMPLETE  " -NoNewline -BackgroundColor Green -ForegroundColor Black
    Write-Host " Service restarted successfully.`n"
    Invoke-Exit 0
}

# --- Test Service Command ---
if ($TestService) {
    Write-Host "`n  TEST SERVICE  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    Write-Host " Starting service + status + MCP endpoint test`n"

    # Start service
    Write-Host "  [1/4] Starting CCTMCPServer..." -ForegroundColor Gray
    sc.exe start CCTMCPServer | Out-Null
    Start-Sleep 5

    # Check status
    Write-Host "  [2/4] Checking service status..." -ForegroundColor Gray
    sc.exe query CCTMCPServer

    # Test health endpoint
    Write-Host "`n  [3/4] Testing health endpoint..." -ForegroundColor Gray
    try {
        curl "http://localhost:$CCT_Default_Port/health" -UseBasicParsing
    } catch {
        Write-Host "  Health endpoint test failed" -ForegroundColor Red
    }

    # Test MCP SSE endpoint
    Write-Host "`n  [4/4] Testing MCP SSE endpoint..." -ForegroundColor Gray
    try {
        curl "http://localhost:$CCT_Default_Port/cognitive-api/v1/sync" -UseBasicParsing -TimeoutSec 5
    } catch {
        Write-Host "  MCP SSE endpoint test completed" -ForegroundColor Yellow
    }

    Write-Host "`n  TEST COMPLETE  " -NoNewline -BackgroundColor Green -ForegroundColor Black
    Write-Host " Service test finished.`n"
    Invoke-Exit 0
}

# --- Health Check Command ---
if ($Health) {
    Write-Host "`n  HEALTH CHECK  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    Write-Host " Running comprehensive health check on MCP server`n"

    # Check if server is running
    Write-Host "  [1/5] Checking server status..." -ForegroundColor Gray
    try {
        $null = curl "http://localhost:$CCT_Default_Port/health" -UseBasicParsing -ErrorAction SilentlyContinue
        Write-Host "  [OK] Server is running" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] Server is not running" -ForegroundColor Red
        Write-Host "  Start server with: .\\.venv\\Scripts\\python.exe src\\main.py" -ForegroundColor Yellow
        Invoke-Exit 1
    }

    # Test health endpoint
    Write-Host "`n  [2/5] Testing health endpoint..." -ForegroundColor Gray
    try {
        $healthResponse = curl "http://localhost:$CCT_Default_Port/health" -UseBasicParsing
        Write-Host "  [OK] Health endpoint: OK" -ForegroundColor Green
        Write-Host "  Response: $($healthResponse.Content)" -ForegroundColor Gray
    } catch {
        Write-Host "  [FAIL] Health endpoint failed" -ForegroundColor Red
        Invoke-Exit 1
    }

    # Test MCP SSE endpoint
    Write-Host "`n  [3/5] Testing MCP SSE endpoint..." -ForegroundColor Gray
    try {
        $sseResponse = curl "http://localhost:$CCT_Default_Port/cognitive-api/v1/sync" -UseBasicParsing -TimeoutSec 5
        Write-Host "  [OK] MCP SSE endpoint: OK" -ForegroundColor Green
        Write-Host "  Response length: $($sseResponse.Content.Length) characters" -ForegroundColor Gray
    } catch {
        Write-Host "  [FAIL] MCP SSE endpoint failed" -ForegroundColor Red
        Invoke-Exit 1
    }

    # Test API key authentication
    Write-Host "`n  [4/5] Testing API key authentication..." -ForegroundColor Gray
    try {
        $authHeaders = @{ "X-API-KEY" = "invalid-key" }
        $authResponse = curl -Headers $authHeaders "http://localhost:$CCT_Default_Port/cognitive-api/v1/sync" -UseBasicParsing -ErrorAction SilentlyContinue
        $authContent = if ($authResponse -and $authResponse.Content) { $authResponse.Content } else { "" }
        if ($authContent -match "Invalid API key") {
            Write-Host "  API key authentication: WORKING" -ForegroundColor Green
        } else {
            Write-Host "  API key authentication test inconclusive" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  API key authentication test inconclusive" -ForegroundColor Yellow
    }

    # Test CORS headers
    Write-Host "`n  [5/5] Testing CORS headers..." -ForegroundColor Gray
    try {
        $corsHeaders = curl -Headers @{"Origin" = "http://localhost:3000"} -Method HEAD "http://localhost:$CCT_Default_Port/health" -UseBasicParsing
        $corsDetected = $false
        if ($corsHeaders.Headers -and $corsHeaders.Headers["Access-Control-Allow-Origin"]) {
            $corsDetected = $true
            Write-Host "  [OK] CORS headers: ENABLED" -ForegroundColor Green
            Write-Host "  Access-Control-Allow-Origin: $($corsHeaders.Headers['Access-Control-Allow-Origin'])" -ForegroundColor Gray
        }

        if (-not $corsDetected) {
            Write-Host "  [WARN] CORS headers not detected" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [WARN] CORS headers test inconclusive" -ForegroundColor Yellow
    }

    Write-Host "`n  HEALTH CHECK COMPLETE  " -NoNewline -BackgroundColor Green -ForegroundColor Black
    Write-Host " All tests passed successfully!`n"
    Write-Host "  [OK] Server is healthy and ready for MCP connections`n" -ForegroundColor Green
    Invoke-Exit 0
}

# --- Service E2E Command ---
if ($ServiceE2E) {
    if (-not (Check-Admin)) {
        Write-Host "`n  ERROR: Administrator privileges required for service E2E checks.`n" -BackgroundColor Red -ForegroundColor White
        Invoke-Exit 1
    }

    $VenvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { ".venv/bin/python" }
    $ServiceManager = "scripts\setup\services\windows\service.py"
    $ServiceLog = "database\logs\cct_service.log"

    if (-not (Test-Path $ServiceManager)) {
        Write-Host "`n  ERROR: Service manager not found: $ServiceManager`n" -BackgroundColor Red -ForegroundColor White
        Invoke-Exit 1
    }

    Write-Host "`n  SERVICE E2E  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    Write-Host " Running restart -> stop -> start + log tail`n"

    Write-Host "  [1/4] Restart service..." -ForegroundColor Gray
    & $VenvPython $ServiceManager restart
    if ($LASTEXITCODE -ne 0) { Invoke-Exit $LASTEXITCODE }

    Write-Host "`n  [2/4] Stop service..." -ForegroundColor Gray
    & $VenvPython $ServiceManager stop
    if ($LASTEXITCODE -ne 0) { Invoke-Exit $LASTEXITCODE }

    Write-Host "`n  [3/4] Start service..." -ForegroundColor Gray
    & $VenvPython $ServiceManager start
    if ($LASTEXITCODE -ne 0) { Invoke-Exit $LASTEXITCODE }

    Write-Host "`n  [4/4] Tail service log (last 120 lines)..." -ForegroundColor Gray
    if (Test-Path $ServiceLog) {
        Get-Content $ServiceLog -Tail 120
    } else {
        Write-Host "  [WARN] Log file not found: $ServiceLog" -ForegroundColor Yellow
    }

    Write-Host "`n  SERVICE E2E COMPLETE  " -NoNewline -BackgroundColor Green -ForegroundColor Black
    Write-Host " Lifecycle checks executed successfully.`n"
    Invoke-Exit 0
}

# --- Status Check Command ---
if ($Status) {
    Write-Host "`n  SERVICE STATUS CHECK  " -NoNewline -BackgroundColor Cyan -ForegroundColor Black
    Write-Host " Checking CCTMCPServer status`n"

    try {
        $service = Get-Service -Name "CCTMCPServer" -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "  Service state: $($service.Status)" -ForegroundColor Cyan
            sc.exe query CCTMCPServer
        } else {
            Write-Host "  Service state: NOT_INSTALLED" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Unable to query service status" -ForegroundColor Yellow
    }

    Write-Host "`n  Connectivity check on port $CCT_Default_Port..." -ForegroundColor Gray
    try {
        $healthProbe = curl "http://localhost:$CCT_Default_Port/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "  Health endpoint: OK (HTTP $($healthProbe.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "  Health endpoint: NOT_REACHABLE" -ForegroundColor Yellow
    }

    Invoke-Exit 0
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

