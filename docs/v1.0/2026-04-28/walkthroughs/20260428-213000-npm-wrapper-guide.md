# Walkthrough - 20260428-213000-npm-wrapper-guide

Based on walkthrough from `walkthroughs/20260428-194800-npm-wrapper-process-manager.md`.

## How to use the guide
1. Open `docs/guides/how-to-run-npm-wrapper.md`.
2. Follow prerequisites and `.env` configuration requirements.
3. Use the exact `npm` or `npx` commands for your platform.
4. Confirm STDIO mode via the verification section.
5. If issues occur, follow the troubleshooting section.

## Key invariant reminders
- Wrapper logs must stay on stderr.
- STDIO mode should not bind an HTTP port.
- Stopping the IDE MCP server should stop the Python child.
