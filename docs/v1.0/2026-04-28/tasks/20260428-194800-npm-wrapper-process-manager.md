# Tasks - 20260428-194800-npm-wrapper-process-manager

Based on tasks from `tasks/20260428-182350-mcp-startup-fetch-fix.md`.

## Phase 1: Analysis
- [x] Inspect `scripts/server`, `scripts/setup`, and `src` startup patterns.
- [x] Confirm wrapper must preserve stdout for MCP protocol only.
- DoD: Technical constraints mapped to Node wrapper architecture.

## Phase 2: Implementation
- [x] Create `scripts/server/js/index.js` with shebang and root resolution.
- [x] Add `venv` bootstrap (`python -m venv venv` + `pip install -r requirements.txt`) when missing.
- [x] Enforce stderr-only wrapper logging.
- [x] Spawn Python child with inherited stdio and forced `CCT_TRANSPORT=stdio`.
- [x] Add graceful shutdown handlers (`SIGINT`, `SIGTERM`, `exit`).
- [x] Add npm bin command in root `package.json`.
- DoD: Wrapper and package metadata are present and linked.

## Phase 3: Validation
- [x] Run `node --check scripts/server/js/index.js`.
- [x] Verify package bin mapping resolves to wrapper path.
- [ ] Manual IDE invocation test with `npx cct-mcp` (or alias `npx cct-server`).
- DoD: No syntax errors and startup lifecycle works as expected.
