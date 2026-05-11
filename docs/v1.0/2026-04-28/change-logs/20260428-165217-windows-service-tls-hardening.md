# Change Log - 20260428-165217-windows-service-tls-hardening

Based on plan from `implementation-plans/20260428-165217-windows-service-tls-hardening.md`.

## Files Updated
- `scripts/server/discover.py`
- `scripts/server/manage.py`
- `scripts/server/setup.py`
- `scripts/setup/setup.bat`
- `scripts/setup/setup.ps1`
- `scripts/setup/setup.sh`
- `src/core/services/windows/background.py`
- `scripts/setup/services/windows/service.py`
- `tests/conftest.py`
- `tests/test_discover_tls.py`

## Summary of Changes
- Added strict TLS verification helpers for outbound discovery requests.
- Enforced dual trust source (`CCT_CA_BUNDLE` or OS trust store), with warning fallback to OS trust when custom bundle exists but is unreadable due permissions.
- Introduced rotating service logs and real-time child stdout/stderr ingestion.
- Added graceful process termination with forced-kill fallback.
- Added state polling for service lifecycle operations to reduce race conditions.
- Fixed project-root resolution bugs in `scripts/server/setup.py` and `scripts/server/manage.py`.
- Hardened Windows stop/log commands in `scripts/server/manage.py` to avoid brittle shell piping.
- Added new setup entrypoint flag `--service-e2e` / `-ServiceE2E` to run elevated service lifecycle E2E and tail logs.
- Extended auto-elevation trigger in PowerShell/CMD setup flow for service lifecycle operations and E2E checks.
- Added exit confirmation prompt behavior in setup entry scripts to prevent terminal auto-close after completion.
- Fixed broken test fixture import (`RoutingService`).
- Added targeted unit tests for TLS verification resolution.

## Verification Results
- `python -m pytest tests/test_discover_tls.py -q` -> PASS (5 tests).
- `python -m py_compile ...` for modified files -> PASS.
- `python scripts/server/discover.py health` -> PASS.
- `python scripts/server/manage.py status` -> PASS.
- `powershell -File scripts/setup/setup.ps1 -Help` -> PASS (new `-ServiceE2E` option visible).
- `scripts/setup/setup.bat --help` -> PASS (passes `--service-e2e` mapping path).
- `python scripts/setup/services/windows/service.py status` -> PASS (service running).
- `python scripts/setup/services/windows/service.py restart` -> BLOCKED (requires Administrator privileges).

## Residual Risks
- Full lifecycle E2E requires elevated terminal access.
- Discovery currently targets HTTP by default for local scan hosts; TLS strict mode is fully enforced when HTTPS targets are used.
