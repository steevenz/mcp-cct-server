---
name: agents
description: Project operating manual for AI coding agents
version: 1.0.0
last_updated: 2025-10-19
author: Steeven Andrian
alwaysApply: true
---

# AGENTS.md – Project Operating Manual for AI Agents

## 0. Project Overview
Creative Critical Thinking MCP Server is a project that provides a server-side interface for MCP for AI coding agents.

## 1. Project Name
Creative Critical Thinking MCP Server

## 2. Project Path
c:\Users\steevenz\MCP\mcp-cct-server

## 3. Project Codename
mcp-cct-server

## 4. Project Standards
- Python 3.12
- Node.js 20 LTS
- Prettier, ESLint config, Black formatting
- Vitest, Pytest, Playwright
- PascalCase for components, kebab-case for files

## 5. Project Rules (MUST / MUST NOT)
### MUST
- Follows the ~/.aicoders/docs/standards/*.md files for project standards
- Follows the ~/.aicoders/user_rules/*.md files for project rules
- Follows the ~/.aicoders/rules/*.md files for project rules
- Follows the ~/.aicoders/docs/guidelines/*.md files for project guidelines
- Follows the ~/.aicoders/workflow/*.md files for project workflow
- Follows the <project-root>/.agents/README.md for project overview

### MUST use MCP
- Must use MCP Filesystem to interact with Folders and Files
- Must use MCP Creative Critical Thinking to Help you think and reason
- Must use MCP Memory to store and retrieve information

## 6. AI Guiderails / Guidelines & Constraints
- When generate project structure must follow the project standards, rules, guidelines, and workflow
- When generate, fix, patch or modify code must follow the project standards, rules, guidelines, and workflow
- When generating code, always consider the project standards, rules, guidelines, and workflow

## 7. AI Main Workflow When Responding to Prompts
1. **Scope check** – Determine which part of the codebase is relevant.
2. **Read first** – Understand existing file structure and conventions before editing.
3. **Plan → implement → verify** – State implementation plan, write code, then verify with tests.
4. **After changes** – Run `pnpm run test`, `pnpm run lint`, and `pnpm run build`.
5. **Post‑completion** – Check for documentation drift; update README if necessary.

## 8. Project Environment
- **Host:** Windows 11
- **Node.js version:** 20 LTS
- **Python version:** 3.12
- **Database:** PostgreSQL 15
- **Package manager:** pnpm
- **Testing:** Vitest, Pytest, Playwright
- **IDE:** Visual Studio Code
- **Terminal:** Windows Terminal
- **Shell:** PowerShell
- **Git:** Git for Windows
- **Docker:** Docker Desktop
- **Postman:** Postman
- **Insomnia:** Insomnia

## 9. Project Deployment
- **Deployment target:** Netlify/Vercel for Online Development, Digital Ocean for Production
- **CI/CD:** GitHub Actions
- **Environment variables:** `.env.production`, `.env.staging`
- **Build command:** `pnpm run build`
- **Start command:** `pnpm run start`

---
