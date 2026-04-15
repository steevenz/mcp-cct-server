@echo off
REM CMD Wrapper for CCT Artisan Setup System
REM Author: Steeven Andrian
REM 
REM Usage:
REM   setup.bat                    # Standard setup
REM   setup.bat --install-service  # Install as Windows Service (auto-elevates)
REM   setup.bat --force            # Force recreate .venv and reset database
REM   setup.bat --skip-deps        # Skip dependency installation
REM   setup.bat --clean-reqs       # Clean and reinstall requirements
REM   setup.bat --run              # Start server after setup
REM   setup.bat --multi-agent      # Configure for multi-agent mode
REM   setup.bat --port 8001        # Set custom port

REM Auto-elevate to Administrator if --install-service is requested
set "ELEVATE=0"
for %%a in (%*) do (
    if "%%a"=="--install-service" set "ELEVATE=1"
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
        set POWERSHELL_ARGS=%POWERSHELL_ARGS% -InstallService
    ) else if "%%a"=="--force" (
        set POWERSHELL_ARGS=%POWERSHELL_ARGS% -Force
    ) else if "%%a"=="--skip-deps" (
        set POWERSHELL_ARGS=%POWERSHELL_ARGS% -SkipDeps
    ) else if "%%a"=="--clean-reqs" (
        set POWERSHELL_ARGS=%POWERSHELL_ARGS% -CleanReqs
    ) else if "%%a"=="--run" (
        set POWERSHELL_ARGS=%POWERSHELL_ARGS% -Run
    ) else if "%%a"=="--multi-agent" (
        set POWERSHELL_ARGS=%POWERSHELL_ARGS% -MultiAgent
    ) else if "%%a"=="--port" (
        set POWERSHELL_ARGS=%POWERSHELL_ARGS% -Port
    ) else (
        set POWERSHELL_ARGS=%POWERSHELL_ARGS% %%a
    )
)

powershell -ExecutionPolicy Bypass -File scripts\setup\setup.ps1 %POWERSHELL_ARGS%
popd
