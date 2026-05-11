@echo off
setlocal EnableDelayedExpansion
REM CMD Wrapper for CCT Artisan Setup System
REM Author: Steeven Andrian
REM
REM Usage:
REM   setup.bat                    # Standard setup
REM   setup.bat --install-service  # Install as Windows Service (auto-elevates)
REM   setup.bat --test-service     # Start service + status + test MCP endpoint
REM   setup.bat --restart          # Restart Windows Service (legacy alias)
REM   setup.bat --restart-service  # Restart Windows Service
REM   setup.bat --start-service    # Start Windows Service
REM   setup.bat --stop-service     # Stop Windows Service
REM   setup.bat --service-e2e      # restart -> stop -> start -> tail logs (auto-elevates)
REM   setup.bat --status           # Show service status
REM   setup.bat --health           # Run health check on the MCP server
REM   setup.bat --force            # Force recreate .venv and reset database
REM   setup.bat --skip-deps        # Skip dependency installation
REM   setup.bat --clean-reqs       # Clean and reinstall requirements
REM   setup.bat --run              # Start server after setup
REM   setup.bat --multi-agent      # Configure for multi-agent mode
REM   setup.bat --port 8001        # Set custom port

REM Auto-elevate to Administrator if service install/control is requested
set "ELEVATE=0"
set "PROMPT_EXIT=1"
for %%a in (%*) do (
    if "%%a"=="--install-service" set "ELEVATE=1"
    if "%%a"=="--start-service" set "ELEVATE=1"
    if "%%a"=="--stop-service" set "ELEVATE=1"
    if "%%a"=="--restart-service" set "ELEVATE=1"
    if "%%a"=="--restart" set "ELEVATE=1"
    if "%%a"=="--service-e2e" set "ELEVATE=1"
    if "%%a"=="--no-exit-prompt" set "PROMPT_EXIT=0"
)

REM Check if already running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    if "%ELEVATE%"=="1" (
        echo ====================================================
        echo  CCT Windows Service Installation
        echo ====================================================
        echo.
        echo  Administrator privileges required for service installation.
        echo  Requesting elevation...
        echo.
        timeout /t 2 >nul

        REM Re-run this script with elevated privileges
        powershell -Command "Start-Process '%~f0' -ArgumentList '%*' -Verb RunAs"
        if "%PROMPT_EXIT%"=="1" (
            echo.
            set /p "_CCT_EXIT_PROMPT=Press Enter to exit..."
        )
        exit /b
    )
)

pushd %~dp0\..\..
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m pip install --quiet pywin32 2>nul
)

REM Convert parameter format for PowerShell
set POWERSHELL_ARGS=
for %%a in (%*) do (
    if "%%a"=="--install-service" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -InstallService
    ) else if "%%a"=="--start-service" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -StartService
    ) else if "%%a"=="--stop-service" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -StopService
    ) else if "%%a"=="--restart-service" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -RestartService
    ) else if "%%a"=="--force" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -Force
    ) else if "%%a"=="--skip-deps" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -SkipDeps
    ) else if "%%a"=="--clean-reqs" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -CleanReqs
    ) else if "%%a"=="--run" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -Run
    ) else if "%%a"=="--multi-agent" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -MultiAgent
    ) else if "%%a"=="--port" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -Port
    ) else if "%%a"=="--test-service" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -TestService
    ) else if "%%a"=="--restart" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -Restart
    ) else if "%%a"=="--health" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -Health
    ) else if "%%a"=="--status" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -Status
    ) else if "%%a"=="--service-e2e" (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! -ServiceE2E
    ) else (
        set POWERSHELL_ARGS=!POWERSHELL_ARGS! %%a
    )
)

set "CCT_NO_EXIT_PROMPT=1"
powershell -ExecutionPolicy Bypass -File scripts\setup\setup.ps1 !POWERSHELL_ARGS!
popd
if "%PROMPT_EXIT%"=="1" (
    echo.
    set /p "_CCT_EXIT_PROMPT=Press Enter to exit..."
)
