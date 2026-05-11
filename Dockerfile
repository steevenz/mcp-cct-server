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
    CCT_PORT=8010 \
    CCT_TRANSPORT=sse \
    CCT_MAX_SESSIONS=128 \
    CCT_LOG_LEVEL=INFO \
    CCT_DB_PATH=/app/database/cct_memory.db \
    CCT_PRICING_PATH=/app/database/datasets \
    CCT_BOOTSTRAP_API_KEY=local-docker-key

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Copy .env.example for reference
COPY .env.example .env.example

# Create database directory for persistence
RUN mkdir -p /app/database/datasets

# Expose the designated MCP port
EXPOSE 8010

# Health check (readiness): verifies HTTP endpoint is serving
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=5s \
            --retries=3 \
            CMD python -c "import os,sys,urllib.request; port=os.getenv('CCT_PORT','8010'); url=f'http://127.0.0.1:{port}/health'; r=urllib.request.urlopen(url, timeout=5); sys.exit(0 if r.status==200 else 1)" || exit 1

# Define the entry point, executing the main server module
CMD ["python", "-m", "src.main"]
