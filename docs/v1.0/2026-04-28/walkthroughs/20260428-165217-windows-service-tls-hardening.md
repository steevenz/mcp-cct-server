# Walkthrough - 20260428-165217-windows-service-tls-hardening

Based on plan from `implementation-plans/20260428-165217-windows-service-tls-hardening.md`.

## 1) TLS Hardening (`scripts/server/discover.py`)
- Introduced `resolve_tls_verify(target_url)`:
  - Returns system trust (`True`) for HTTPS when no custom CA is set.
  - Returns custom CA bundle path when `CCT_CA_BUNDLE` exists and valid.
  - Raises runtime error when `CCT_CA_BUNDLE` is set to missing file (fail closed).
  - Falls back to system trust with warning when `CCT_CA_BUNDLE` exists but is unreadable due permissions.
- Introduced `build_async_http_client(...)` to ensure all discovery-side `httpx` async calls use strict verification.

## 2) Service Runtime Stability (`src/core/services/windows/background.py`)
- Replaced basic logger setup with `RotatingFileHandler` to prevent unbounded log growth.
- Added stream pump threads for `stdout` and `stderr` to avoid pipe blocking and preserve runtime output.
- Added `_stop_process()` for graceful shutdown + kill fallback.
- Standardized launch/relaunch through `_launch_server(...)` and retained supervised restart loop.

## 3) Lifecycle Reliability (`scripts/setup/services/windows/service.py`)
- Added `_run_sc(...)` and `_wait_for_state(...)` helpers.
- `start()` now requires service to reach RUNNING within timeout.
- `stop()` now requires service to reach STOPPED within timeout.
- `restart()` now aborts if stop phase fails.

## 4) Tests and Harness
- Added `tests/test_discover_tls.py` (4 focused tests).
- Updated `tests/conftest.py` to import router from `src.core.services.orchestration.routing` and instantiate `RoutingService`.

## 5) Script Stability Fixes (`scripts/server/manage.py`, `scripts/server/setup.py`)
- Corrected project root traversal from `scripts/server/*` to repository root.
- Replaced brittle `netstat | findstr` composition with PowerShell `Get-NetTCPConnection` process discovery.
- Fixed log tail command invocation using `powershell -Command`.

## 6) Setup Entrypoint E2E Trigger (`scripts/setup/setup.bat`, `scripts/setup/setup.ps1`, `scripts/setup/setup.sh`)
- Added `--service-e2e` (bash/cmd) and `-ServiceE2E` (PowerShell) to run:
  - restart service
  - stop service
  - start service
  - tail service log (`database/logs/cct_service.log`, 120 lines)
- Windows path now auto-requests Administrator privileges when E2E/service lifecycle operations are invoked.
- Bash entrypoint delegates to PowerShell E2E flow on Windows shells (`MINGW/MSYS/CYGWIN`).
- Setup entry scripts now prompt before terminal exit to keep output visible (`CCT_NO_EXIT_PROMPT=1` suppresses prompt for automation/chained calls).

## 7) How to Complete E2E on This Machine
Run in Administrator PowerShell:
```powershell
cd C:\Users\steevenz\MCP\mcp-cct-server
.\.venv\Scripts\python.exe scripts\setup\services\windows\service.py restart
.\.venv\Scripts\python.exe scripts\setup\services\windows\service.py stop
.\.venv\Scripts\python.exe scripts\setup\services\windows\service.py start
Get-Content .\database\logs\cct_service.log -Tail 80
```
Expected:
- service transitions RUNNING -> STOPPED -> RUNNING.
- `cct_service.log` contains fresh `[CCT STDOUT]`/`[CCT STDERR]` lines after restart.
