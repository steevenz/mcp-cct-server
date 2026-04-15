# Multi-stage build for smaller image
FROM python:3.11-slim-bookworm AS builder

# Set build arguments
ARG BUILDKIT_INLINE_CACHE=1

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim-bookworm

# Set environment variables to optimize Python execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# CCT Server Configuration
ENV CCT_HOST=0.0.0.0 \
    CCT_PORT=8000 \
    CCT_TRANSPORT=sse \
    CCT_MAX_SESSIONS=128 \
    CCT_LOG_LEVEL=INFO \
    CCT_DB_PATH=/app/database/cct_memory.db \
    CCT_PRICING_PATH=/app/database/datasets

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy source code
COPY src/ ./src/

# Copy .env.example for reference
COPY .env.example .env.example

# Create database directory for persistence
RUN mkdir -p /app/database/datasets

# Expose the designated MCP port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=5s \
            --retries=3 \
            CMD python -c "import sys; import sqlite3; conn = sqlite3.connect('${CCT_DB_PATH}'); conn.execute('SELECT 1'); conn.close(); sys.exit(0)" || exit 1

# Define the entry point, executing the main server module
CMD ["python", "-m", "src.main"]