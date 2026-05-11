# Tasks - 20260428-220000-multi-ide-shared-proxy

Based on tasks from `tasks/20260428-194800-npm-wrapper-process-manager.md`.

## Phase 1: Wrapper architecture
- [x] Implement shared server discovery using `/status` signature.
- [x] Implement auth validation by probing `ping` with `X-API-KEY`.
- [x] Add shared server state file with lock + refCount.

## Phase 2: STDIO proxy
- [x] Read newline-delimited JSON-RPC from stdin.
- [x] Forward to `POST /cognitive-api/v1/sync` with headers.
- [x] Write JSON-RPC responses to stdout only.

## Phase 3: Verification
- [x] `node --check scripts/server/js/index.js`.
- [x] Smoke test `ping` roundtrip through proxy.
- [ ] Manual multi-IDE test: connect from 2 IDEs concurrently.
