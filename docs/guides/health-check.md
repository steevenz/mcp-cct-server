# Health Check Guide

## Overview

The CCT MCP Server provides a comprehensive health check endpoint for monitoring system status, debugging issues, and integration with container orchestration platforms (Docker, Kubernetes).

## Quick Start

### Via MCP Tool

```python
# Call from your IDE or client
health_check()
```

### Via Dashboard

Open the **System Health** expander in the Streamlit Dashboard sidebar to see real-time health status.

## Response Format

### Healthy State

```json
{
  "status": "healthy",
  "timestamp": "2026-04-13T05:15:00+00:00",
  "version": "2026.04.12",
  "services": {
    "database": "healthy",
    "memory_manager": "healthy"
  },
  "metrics": {
    "active_sessions": 5,
    "total_thoughts": 127,
    "response_time_ms": 12.34,
    "rate_limit_window": 60,
    "rate_limit_max": 100
  }
}
```

### Degraded State

```json
{
  "status": "degraded",
  "timestamp": "2026-04-13T05:15:00+00:00",
  "version": "2026.04.12",
  "services": {
    "database": "degraded: connection timeout",
    "memory_manager": "healthy"
  },
  "metrics": {
    "active_sessions": 5,
    "total_thoughts": 127,
    "response_time_ms": 2500.00,
    "rate_limit_window": 60,
    "rate_limit_max": 100
  }
}
```

## Field Descriptions

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Overall system status: `healthy`, `degraded`, or `error` |
| `timestamp` | string | ISO 8601 timestamp of the health check |
| `version` | string | CCT Server version identifier |
| `services` | object | Individual service health statuses |
| `metrics` | object | Quantitative system metrics |

### Services Object

| Service | Description | Common Issues |
|---------|-------------|---------------|
| `database` | SQLite connectivity and performance | Connection timeouts, disk full, locked database |
| `memory_manager` | Memory management subsystem status | Memory pressure, corrupted sessions |

### Metrics Object

| Metric | Type | Description |
|--------|------|-------------|
| `active_sessions` | integer | Number of active cognitive sessions |
| `total_thoughts` | integer | Total thoughts stored in database |
| `response_time_ms` | float | Health check execution time (ms) |
| `rate_limit_window` | integer | Rate limiting window in seconds |
| `rate_limit_max` | integer | Max requests per window |

## Container Integration

### Docker

#### Dockerfile HEALTHCHECK

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

# Health check every 30s, timeout 3s, 3 retries before unhealthy
HEALTHCHECK --interval=30s \
            --timeout=3s \
            --start-period=5s \
            --retries=3 \
            CMD python -c "
import sys
import json
import sqlite3
from src.core.config import DEFAULT_DB_PATH
try:
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    conn.execute('SELECT 1')
    conn.close()
    sys.exit(0)
except:
    sys.exit(1)
" || exit 1

CMD ["python", "-m", "src.main"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  cct-server:
    build: .
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import sqlite3; conn = sqlite3.connect('/app/cct_memory.db'); conn.execute('SELECT 1'); conn.close()"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
    volumes:
      - ./data:/app/data
```

### Kubernetes

#### Liveness Probe

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cct-mcp-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cct-mcp-server
  template:
    metadata:
      labels:
        app: cct-mcp-server
    spec:
      containers:
      - name: cct-server
        image: cct-mcp-server:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - |
              import sqlite3
              from src.core.config import DEFAULT_DB_PATH
              conn = sqlite3.connect(DEFAULT_DB_PATH)
              conn.execute('SELECT 1')
              conn.close()
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 3
          failureThreshold: 3
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - |
              import sqlite3
              from src.core.config import DEFAULT_DB_PATH
              conn = sqlite3.connect(DEFAULT_DB_PATH)
              conn.execute('SELECT 1')
              conn.close()
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 2
```

## Monitoring & Alerting

### Prometheus Integration

```python
from prometheus_client import Gauge, generate_latest
from src.tools.session_tools import health_check

# Define metrics
cct_health_status = Gauge('cct_health_status', 'Overall health status (1=healthy, 0=degraded)')
cct_active_sessions = Gauge('cct_active_sessions', 'Number of active sessions')
cct_response_time = Gauge('cct_health_response_time_ms', 'Health check response time')

def update_metrics():
    """Update Prometheus metrics from health check."""
    health = health_check()
    
    # Set health status (1 for healthy, 0 otherwise)
    cct_health_status.set(1 if health['status'] == 'healthy' else 0)
    
    # Set other metrics
    cct_active_sessions.set(health['metrics']['active_sessions'])
    cct_response_time.set(health['metrics']['response_time_ms'])
```

### Alertmanager Rules

```yaml
groups:
  - name: cct_alerts
    rules:
      - alert: CCTServerDown
        expr: cct_health_status == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "CCT MCP Server is down or degraded"
          description: "Health check failed for {{ $labels.instance }}"
      
      - alert: CCTHighResponseTime
        expr: cct_health_response_time_ms > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CCT Server response time is high"
          description: "Response time is {{ $value }}ms for {{ $labels.instance }}"
      
      - alert: CCTTooManySessions
        expr: cct_active_sessions > 100
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "CCT Server has high session count"
          description: "{{ $value }} active sessions on {{ $labels.instance }}"
```

## Dashboard Integration

### System Health Panel

The Streamlit Dashboard includes a **System Health** expander in the sidebar showing:

- ✅/⚠️ Overall status indicator
- Service health for Database and Memory Manager
- Response time metrics
- Rate limiting configuration
- Database file size

### Export Health Report

Click the **📥 Export** button in the System Health panel to download a JSON health report:

```json
{
  "export_timestamp": "2026-04-13T05:20:00+00:00",
  "health_data": { ... },
  "system_info": {
    "python_version": "3.11.0",
    "platform": "Windows-10-10.0.19045",
    "database_path": "cct_memory.db",
    "database_size_kb": 2048
  }
}
```

## Health Check Implementation

### Code Structure

```python
# src/tools/session_tools.py

@mcp.tool()
def health_check() -> dict[str, object]:
    """
    Health check endpoint for monitoring and Docker/Kubernetes health probes.
    
    Returns system status, active sessions count, database connectivity,
    and rate limiting information.
    """
    start_time = time.time()
    
    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2026.04.12",
        "services": {},
        "metrics": {},
    }
    
    # Check database connectivity
    try:
        _ = orchestrator.memory.get_session("__health_check__")
        health["services"]["database"] = "healthy"
    except Exception as e:
        health["services"]["database"] = f"degraded: {str(e)}"
        health["status"] = "degraded"
    
    # Get active sessions count
    try:
        active_sessions = len(orchestrator.memory.list_sessions())
        health["metrics"]["active_sessions"] = active_sessions
        health["services"]["memory_manager"] = "healthy"
    except Exception as e:
        health["metrics"]["active_sessions"] = -1
        health["services"]["memory_manager"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    # Calculate response time
    health["metrics"]["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Get rate limiter stats
    rate_limiter = get_rate_limiter()
    health["metrics"]["rate_limit_window"] = rate_limiter.config.window_seconds
    health["metrics"]["rate_limit_max"] = rate_limiter.config.max_requests
    
    return health
```

## Troubleshooting

### Database Connection Failures

**Symptom:** `database: "degraded: connection timeout"`  
**Solutions:**
1. Check database file permissions
2. Verify disk space: `df -h`
3. Check for database locks: `lsof cct_memory.db`
4. Restart the server

### High Response Time

**Symptom:** `response_time_ms > 1000`  
**Solutions:**
1. Check system load: `top` or `htop`
2. Analyze database size: `ls -lh cct_memory.db`
3. Consider running VACUUM on SQLite: `sqlite3 cct_memory.db "VACUUM;"`
4. Check for runaway sessions

### Memory Manager Errors

**Symptom:** `memory_manager: "error: ..."`  
**Solutions:**
1. Check available RAM
2. Restart the server
3. Review recent session logs for corruption

## Best Practices

1. **Regular Health Checks:** Monitor health at least every 30 seconds in production
2. **Alert on Degraded:** Set up alerts for `status != "healthy"`
3. **Export Reports:** Periodically export health reports for trend analysis
4. **Capacity Planning:** Monitor `active_sessions` and `total_thoughts` for growth trends
5. **Response Time SLA:** Set thresholds (e.g., <100ms for healthy, <500ms for degraded)

## API Reference

### Health Check Tool

```python
health_check() -> Dict[str, object]
```

**Returns:** Health status dictionary with status, services, and metrics.

**Example:**
```python
result = health_check()
assert result["status"] in ["healthy", "degraded", "error"]
assert "database" in result["services"]
assert "memory_manager" in result["services"]
```

---

**See Also:**
- [Rate Limiting Guide](./rate-limiting.md)
- [Testing Guide](./testing.md)
- [Deployment Guide](../context-tree/setup/deployment.md)
