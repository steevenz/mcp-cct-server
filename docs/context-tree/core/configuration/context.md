---
title: "Core: System Configuration"
tags: ["core", "config", "transport"]
keywords: ["env-vars", "stdio", "http", "overrides"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Topic: Configuration

## Overview
The Configuration topic defines the environment-level parameters that control the instantiation and runtime behavior of the CCT MCP Server. It handles transport management, session limits, and the initial tuning of the cognitive architecture.

## Key Concepts
- **Environment Parity**: Support for `CCT_` prefixed environment variables to override defaults (e.g., `CCT_LOG_LEVEL`, `CCT_MAX_THOUGHTS`).
- **Transport Modes**: Flexible communication via standard MCP `stdio` (pipe) or high-concurrency `http` layers for specialized deployments.
- **Resource Hard-Capping**: Enforcing a strict limit on concurrent cognitive sessions (`DEFAULT_MAX_SESSIONS: 128`) to ensure server stability.

## Related Topics
- [../context.md](../context.md)
- [../models/context.md](../models/context.md)
