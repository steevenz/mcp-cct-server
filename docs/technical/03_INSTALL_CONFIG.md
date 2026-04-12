# Installation & Configuration

## Prerequisites

- Python 3.11+ (repo ini menggunakan Pydantic v2 dan pola typing modern).
- Virtual environment (recommended).

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run MCP Server

Entry point server: `src/main.py`.

```bash
python src/main.py
```

### Environment Variables

Ada dua surface konfigurasi:

1) **Aktif dipakai oleh `src/main.py`**

- `MCP_SERVER_HOST` (default `0.0.0.0`)
- `MCP_SERVER_PORT` (default `8000`)

2) **Disediakan oleh `src/core/config.py` (Settings loader)**

- `CCT_SERVER_NAME` (default `cct-mcp-server`)
- `CCT_TRANSPORT` (`stdio|http`, default `stdio`)
- `CCT_HOST` (default `0.0.0.0`)
- `CCT_PORT` (default `8000`)
- `CCT_MAX_SESSIONS` (default `128`)

Rekomendasi untuk produksi: konsolidasikan menjadi satu sumber konfigurasi agar tidak terjadi divergensi.

## Run Dashboard (Mission Control)

```bash
streamlit run dashboard.py
```

Catatan: dashboard membaca DB yang sama (`cct_memory.db`). Pastikan working directory konsisten atau gunakan path absolut di konfigurasi jika dibutuhkan.

## Run Tests

```bash
python -m pytest -q
```

## Data Files

- `datasets/pricing.json`: registry pricing untuk kalkulasi cost pada `TokenHarness` (`src/utils/harness.py`).
- `cct_memory.db`: SQLite DB default untuk persistence (dibuat otomatis jika belum ada).

## Deployment Notes

- SQLite cocok untuk single-node dan beban moderat. Jika concurrency tinggi, pertimbangkan WAL mode dan konfigurasi connection pooling/locking.
- Jangan menyimpan secret di `.env` yang di-commit; gunakan `.env.example` sebagai template.

