# Change Log - 20260428-220000-multi-ide-shared-proxy

Based on change-log from `change-logs/20260428-194800-npm-wrapper-process-manager.md`.

## Semantic Changes
- `feat(wrapper-proxy):` convert npm wrapper to a per-IDE STDIO proxy forwarding to shared HTTP/SSE backend.
- `feat(shared-backend):` add discovery + auth validation + shared state/refCount tracking.
- `docs(guides):` update wrapper guide to describe multi-IDE shared backend behavior.

## Files Updated
- `scripts/server/js/index.js`
- `docs/guides/how-to-run-npm-wrapper.md`
