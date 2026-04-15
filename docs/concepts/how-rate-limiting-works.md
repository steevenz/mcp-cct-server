# Rate Limiting Guide

## Overview

CCT MCP Server includes enterprise-grade rate limiting to prevent abuse, ensure fair resource allocation, and maintain system stability under high load.

## Architecture

The rate limiting system uses a **Sliding Window Algorithm** with the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Rate Limiter Architecture                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐      ┌─────────────────────┐      │
│  │  SlidingWindowRate  │      │  TokenBucketRate    │      │
│  │  Limiter            │      │  Limiter            │      │
│  │  - Per-client tracking│      │  - Burst handling   │      │
│  │  - 60s window       │      │  - 10 tokens/sec    │      │
│  └─────────────────────┘      └─────────────────────┘      │
│           │                            │                   │
│           └────────────┬───────────────┘                   │
│                        │                                    │
│           ┌────────────▼───────────────┐                   │
│           │   @rate_limited Decorator  │                   │
│           │   - Automatic enforcement  │                   │
│           │   - Retry-After headers    │                   │
│           └────────────────────────────┘                   │
│                        │                                    │
│           ┌────────────▼───────────────┐                   │
│           │    MCP Tool Endpoints      │                   │
│           │  - cct_think_step          │                   │
│           │  - actor_critic_dialog     │                   │
│           └────────────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Default Limits

| Endpoint | Max Requests | Window | Strategy |
|----------|--------------|--------|----------|
| `cct_think_step` | 120 | 60 seconds | Standard operations |
| `actor_critic_dialog` | 30 | 60 seconds | Computationally expensive |
| `council_of_critics_debate` | 30 | 60 seconds | Multi-agent processing |
| `temporal_horizon_projection` | 60 | 60 seconds | Medium complexity |

## Configuration

### Global Rate Limiter

Access the global rate limiter instance:

```python
from src.core.rate_limiter import get_rate_limiter

limiter = get_rate_limiter()
config = limiter.config

# Default configuration
config.max_requests = 100      # requests per window
config.window_seconds = 60     # time window
config.burst_size = 10         # burst allowance
```

### Custom Limits per Endpoint

Apply custom rate limiting to any function:

```python
from src.core.rate_limiter import rate_limited

@mcp.tool()
@rate_limited(max_requests=50, window_seconds=60)
async def my_custom_tool(session_id: str, ...):
    """Custom tool with 50 req/60s limit."""
    return {...}
```

## Rate Limit Response

When rate limit is exceeded, the response includes:

```json
{
  "status": "error",
  "code": 429,
  "error": "Rate limit exceeded",
  "retry_after": 45,
  "message": "Too many requests. Retry after 45 seconds.",
  "_rate_limit": {
    "remaining": 0,
    "limit": 120,
    "window": 60
  }
}
```

## Client-Side Handling

### Retry Logic (Python)

```python
import time
from typing import Dict, Any

def call_with_retry(tool_func, max_retries=3, **kwargs) -> Dict[str, Any]:
    """Call MCP tool with automatic retry on rate limit."""
    for attempt in range(max_retries):
        result = tool_func(**kwargs)
        
        if result.get("code") == 429:
            retry_after = result.get("retry_after", 60)
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue
            
        return result
    
    raise Exception("Max retries exceeded due to rate limiting")
```

### JavaScript/TypeScript

```typescript
async function callWithRetry(toolFunc: Function, maxRetries = 3, ...args: any[]) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        const result = await toolFunc(...args);
        
        if (result.code === 429) {
            const retryAfter = result.retry_after || 60;
            console.log(`Rate limited. Waiting ${retryAfter}s...`);
            await new Promise(r => setTimeout(r, retryAfter * 1000));
            continue;
        }
        
        return result;
    }
    
    throw new Error("Max retries exceeded due to rate limiting");
}
```

## Monitoring

### Check Rate Limit Status

```python
from src.core.rate_limiter import get_rate_limiter

limiter = get_rate_limiter()
remaining = limiter.get_remaining("session_id_123")
print(f"Remaining requests: {remaining}")
```

### Dashboard Integration

The Streamlit dashboard displays current rate limits in the **System Health** panel:

- Max Sessions: 128
- Max Thoughts/Session: 200

## Advanced Configuration

### Custom Rate Limiter Instance

```python
from src.core.rate_limiter import SlidingWindowRateLimiter, RateLimitConfig

# Create custom limiter
config = RateLimitConfig(
    max_requests=200,
    window_seconds=120,
    burst_size=20
)

custom_limiter = SlidingWindowRateLimiter(config)

# Use directly
allowed, retry_after = custom_limiter.is_allowed("client_123")
```

### Token Bucket for Bursty Traffic

```python
from src.core.rate_limiter import TokenBucketRateLimiter

# 10 tokens per second, max burst of 50
bucket = TokenBucketRateLimiter(rate=10.0, burst_size=50)

allowed, wait_time = bucket.is_allowed("client_123")
```

## Troubleshooting

### Common Issues

**Issue:** Getting rate limited too quickly  
**Solution:** Check if you're reusing session IDs. Each session has independent rate limits.

**Issue:** Rate limit not resetting  
**Solution:** Rate limits are per-client (session_id). Create a new session if needed.

**Issue:** Burst traffic causing 429s  
**Solution:** Implement client-side queuing or use the TokenBucketRateLimiter for smoother traffic.

### Reset Rate Limits (Admin)

```python
from src.core.rate_limiter import get_rate_limiter

limiter = get_rate_limiter()
limiter.reset("session_id_123")  # Reset specific client
```

## Best Practices

1. **Implement Exponential Backoff:** Don't retry immediately; use exponential backoff
2. **Cache Results:** Cache expensive operations to reduce API calls
3. **Batch Operations:** Group multiple thoughts into single calls when possible
4. **Monitor Usage:** Track your rate limit consumption via dashboard
5. **Handle 429s Gracefully:** Always handle rate limit errors in production code

## API Reference

### Classes

#### `SlidingWindowRateLimiter`

```python
class SlidingWindowRateLimiter:
    def __init__(self, config: RateLimitConfig = None)
    def is_allowed(self, client_id: str) -> tuple[bool, Optional[int]]
    def get_remaining(self, client_id: str) -> int
    def reset(self, client_id: str) -> None
```

#### `TokenBucketRateLimiter`

```python
class TokenBucketRateLimiter:
    def __init__(self, rate: float = 10.0, burst_size: int = 20)
    def is_allowed(self, client_id: str) -> tuple[bool, Optional[float]]
```

#### `RateLimitConfig`

```python
@dataclass
class RateLimitConfig:
    max_requests: int = 100
    window_seconds: int = 60
    burst_size: int = 10
```

### Decorator

```python
@rate_limited(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_func: Optional[Callable] = None
)
```

---

**See Also:**
- [System Health Guide](./health-check.md)
- [Testing Guide](./testing.md)
- [Security Best Practices](../rules/security.md)
