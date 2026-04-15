---
title: "Domain: Setup (Deployment & Config)"
tags: ["setup", "installation", "transport", "config"]
keywords: ["bootstrap", "bin-tools", "environment", "deployment"]
importance: 100
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Domain: Setup

## Purpose
The Setup domain provides the foundational instructions and tools for deploying the CCT MCP Server. It bridges the gap between the source code and a running cognitive instance by automating installation, environment validation, and transport layer configuration.

## Scope
Included in this domain:
- **Binary Tools**: Documentation for the `.bin/` setup scripts (Artisan-style).
- **Environment Variables**: Mandatory and optional `CCT_` prefixed parameters.
- **Transport Configurations**: Settings for `stdio` and `http` communication layers.

Excluded from this domain:
- **Application Logic**: Engine-level behavior (handled by `Engines`).
- **Data Persistence**: Database internal management (handled by `Memory`).

## Usage
Consult this domain when:
- **Installing** a new instance of the CCT server.
- **Configuring** environment overrides for production vs. development.
- **Switching** transport layers (e.g., from local IDE stdio to remote HTTP).

## C&C Framework Alignment
The Setup domain establishes the **Environmental Baseline** for the C&C Framework. It ensuring that the system is correctly "Bootstrapped" with the necessary permissions, API keys, and memory paths needed for both **Creative** expansion and **Critical** empirical grounding.
