# Tasks - 20260428-165217-windows-service-tls-hardening

Based on plan from `implementation-plans/20260428-165217-windows-service-tls-hardening.md`.

- [x] Audit scripts in `scripts/` and Windows service runtime files.
- [x] Implement strict TLS verify for all `httpx` calls in discovery flow.
- [x] Implement dual CA trust source with fail-closed behavior.
- [x] Harden `pywin32` background service logging and process supervision.
- [x] Improve Windows service start/stop/restart state checks.
- [x] Add TLS unit tests.
- [x] Fix `tests/conftest.py` router import mismatch.
- [x] Fix root path resolution in `scripts/server/setup.py` and `scripts/server/manage.py`.
- [x] Harden process stop/log shell command handling in `scripts/server/manage.py`.
- [x] Add `--service-e2e` / `-ServiceE2E` flow in setup entry scripts (`.bat`, `.ps1`, `.sh`) with privilege gating.
- [x] Update TLS edge-case behavior: unreadable `CCT_CA_BUNDLE` now warns and falls back to OS trust.
- [x] Add exit confirmation prompts in setup entry scripts to avoid auto-closed terminal windows.
- [x] Run focused verification (`pytest`, compile checks, status command).
- [ ] Run full elevated lifecycle E2E (`restart`, `stop`, `start`) in Administrator shell.
- [ ] Verify post-restart log continuity in `database/logs/cct_service.log` under elevated run.
