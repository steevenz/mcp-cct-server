# Implementation Plan - 20260428-165217-windows-service-tls-hardening

Based on plan from N/A (first baseline in docs/v1.0).

## Scope
- Harden Windows service runtime stability for `pywin32` service flow.
- Enforce strict TLS verification for outbound `httpx` requests (CA + hostname, fail closed).
- Improve service lifecycle reliability for start/stop/restart wait-state handling.

## Planned Changes
1. `scripts/server/discover.py`
- Add strict TLS resolver for all `httpx` async clients.
- Implement dual CA trust mode:
  - Use `CCT_CA_BUNDLE` when set and file exists.
  - Fallback to system trust store when not set.
  - Fail closed when `CCT_CA_BUNDLE` is set but invalid.
- Keep non-TLS behavior unchanged for `http://` targets.

2. `src/core/services/windows/background.py`
- Replace basic file logging with rotating log handler.
- Stream child process `stdout` and `stderr` in real-time via dedicated pump threads.
- Add controlled subprocess shutdown with terminate/kill fallback.
- Keep restart loop but avoid output-loss path.

3. `scripts/setup/services/windows/service.py`
- Add `sc.exe` wrapper helper and explicit state polling.
- Start/stop now wait until RUNNING/STOPPED (or timeout).
- Restart exits early when stop fails.

4. Tests
- Add focused TLS tests for resolver behavior in `tests/test_discover_tls.py`.
- Fix test harness import break in `tests/conftest.py` (`RoutingService`).

## Verification Plan
- Run focused tests for TLS resolver.
- Run compile/syntax checks for modified modules.
- Execute service status and lifecycle commands on machine where privileges allow.

## Risks
- Service lifecycle commands require elevated shell on Windows.
- Existing environments without pytest in `.venv` need fallback to system Python.
