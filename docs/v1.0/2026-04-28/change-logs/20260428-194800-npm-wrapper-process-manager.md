# Change Log - 20260428-194800-npm-wrapper-process-manager

Based on change-log from `change-logs/20260428-182350-mcp-startup-fetch-fix.md`.

## Semantic Changes
- `feat(dx-wrapper):` add Node executable wrapper for Python MCP runtime at `scripts/server/js/index.js`.
- `feat(bootstrap):` auto-create `venv` and install dependencies when not present.
- `feat(process-manager):` add child-process shutdown hooks to avoid zombie Python runtime.
- `feat(package):` add npm bin mappings `cct-mcp` and `cct-server` -> `./scripts/server/js/index.js`.

## Files Updated
- `scripts/server/js/index.js` (new)
- `package.json` (new)

## Verification
- Pending execution: `node --check scripts/server/js/index.js`
- Pending execution: manual `npx cct-mcp` integration test in IDE.
