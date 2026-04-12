# CCT MCP Server — Technical Documentation Index

Dokumentasi ini menjelaskan struktur internal codebase `src/`, kontrak API (MCP tools), arsitektur data (SQLite), serta panduan development untuk kontribusi.

## Contents

- [01_ARCHITECTURE.md](./01_ARCHITECTURE.md) — Arsitektur sistem + diagram
- [02_API_REFERENCE.md](./02_API_REFERENCE.md) — Dokumentasi API MCP (tools yang diekspos)
- [03_INSTALL_CONFIG.md](./03_INSTALL_CONFIG.md) — Instalasi, konfigurasi environment, menjalankan server & dashboard
- [04_MODULE_GUIDE.md](./04_MODULE_GUIDE.md) — Penjelasan modul & komponen utama (`core/`, `engines/`, `modes/`, `tools/`, `analysis/`, `utils/`)
- [05_QUALITY_AND_IMPROVEMENTS.md](./05_QUALITY_AND_IMPROVEMENTS.md) — Temuan kualitas kode, risiko, dan rekomendasi improvement

## Quick Orientation (Developer Baru)

1. Entry point server: `src/main.py`
2. Lapisan API: `src/tools/*_tools.py` (decorator `@mcp.tool()`)
3. Orkestrasi: `src/engines/orchestrator.py`
4. Registry strategi → engine: `src/modes/registry.py`
5. Persistence: `src/engines/memory/manager.py` (SQLite)
6. Tracking sequence & anti-hallucination: `src/engines/sequential/engine.py`

