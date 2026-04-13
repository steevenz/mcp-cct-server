"""
Rate Limiting Module for CCT MCP Server.

Provides token bucket and sliding window rate limiting for API endpoints
to prevent abuse and ensure fair resource allocation.
"""
from __future__ import annotations

import time
import logging
from typing import Dict, Optional, Callable, Any
from functools import wraps
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests: int = 100  # Maximum requests per window
    window_seconds: int = 60  # Time window in seconds
    burst_size: int = 10  # Allow burst of requests
    

class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window rate limiter.
    
    Tracks request timestamps per client and enforces rate limits
    using a sliding window algorithm.
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self._requests: Dict[str, list[float]] = {}
        self._lock = Lock()
        
    def is_allowed(self, client_id: str) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed for given client.
        
        Args:
            client_id: Unique identifier for the client (session_id or IP)
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
            retry_after is None if allowed, otherwise seconds to wait
        """
        now = time.time()
        window_start = now - self.config.window_seconds
        
        with self._lock:
            # Initialize client if new
            if client_id not in self._requests:
                self._requests[client_id] = []
            
            # Clean old requests outside window
            self._requests[client_id] = [
                req_time for req_time in self._requests[client_id]
                if req_time > window_start
            ]
            
            # Check if under limit
            current_count = len(self._requests[client_id])
            
            if current_count < self.config.max_requests:
                # Allow request and record timestamp
                self._requests[client_id].append(now)
                return True, None
            
            # Rate limit exceeded - calculate retry after
            if self._requests[client_id]:
                oldest_request = min(self._requests[client_id])
                retry_after = int(oldest_request + self.config.window_seconds - now) + 1
                retry_after = max(1, retry_after)  # At least 1 second
            else:
                retry_after = self.config.window_seconds
                
            logger.warning(
                f"Rate limit exceeded for client {client_id}: "
                f"{current_count} requests in {self.config.window_seconds}s"
            )
            return False, retry_after
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests allowed for client in current window."""
        now = time.time()
        window_start = now - self.config.window_seconds
        
        with self._lock:
            if client_id not in self._requests:
                return self.config.max_requests
            
            # Clean and count
            valid_requests = [
                req_time for req_time in self._requests[client_id]
                if req_time > window_start
            ]
            
            remaining = max(0, self.config.max_requests - len(valid_requests))
            return remaining
    
    def reset(self, client_id: str) -> None:
        """Reset rate limit for specific client."""
        with self._lock:
            self._requests.pop(client_id, None)
            logger.info(f"Rate limit reset for client {client_id}")


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for burst handling.
    
    Allows bursts up to burst_size, then enforces steady rate.
    """
    
    def __init__(self, rate: float = 10.0, burst_size: int = 20):
        """
        Args:
            rate: Tokens per second (steady state rate)
            burst_size: Maximum burst size
        """
        self.rate = rate
        self.burst_size = burst_size
        self._buckets: Dict[str, dict] = {}
        self._lock = Lock()
        
    def is_allowed(self, client_id: str) -> tuple[bool, Optional[float]]:
        """
        Check if request is allowed (token available).
        
        Returns:
            Tuple of (is_allowed, wait_time_seconds)
        """
        now = time.time()
        
        with self._lock:
            # Initialize bucket for new client
            if client_id not in self._buckets:
                self._buckets[client_id] = {
                    'tokens': self.burst_size,
                    'last_update': now
                }
            
            bucket = self._buckets[client_id]
            
            # Add tokens based on time elapsed
            elapsed = now - bucket['last_update']
            tokens_to_add = elapsed * self.rate
            bucket['tokens'] = min(self.burst_size, bucket['tokens'] + tokens_to_add)
            bucket['last_update'] = now
            
            # Check if token available
            if bucket['tokens'] >= 1.0:
                bucket['tokens'] -= 1.0
                return True, None
            
            # Calculate wait time for next token
            wait_time = (1.0 - bucket['tokens']) / self.rate
            wait_time = max(0.1, wait_time)  # Minimum 100ms
            
            logger.warning(
                f"Token bucket empty for client {client_id}, "
                f"wait time: {wait_time:.2f}s"
            )
            return False, wait_time


# Global rate limiter instance
_default_limiter: Optional[SlidingWindowRateLimiter] = None


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Get or create global rate limiter instance."""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = SlidingWindowRateLimiter()
    return _default_limiter


def rate_limited(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_func: Optional[Callable[[Any], str]] = None
):
    """
    Decorator for rate limiting MCP tool functions.
    
    Args:
        max_requests: Maximum requests allowed per window
        window_seconds: Time window in seconds
        key_func: Function to extract client key from arguments
                 Defaults to using session_id from kwargs
    
    Example:
        @rate_limited(max_requests=50, window_seconds=60)
        async def cct_think_step(session_id: str, ...):
            ...
    """
    limiter = SlidingWindowRateLimiter(
        RateLimitConfig(max_requests=max_requests, window_seconds=window_seconds)
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract client key
            if key_func:
                client_key = key_func(*args, **kwargs)
            else:
                # Default: use session_id or first arg
                client_key = kwargs.get('session_id', args[0] if args else 'unknown')
            
            allowed, retry_after = limiter.is_allowed(client_key)
            
            if not allowed:
                return {
                    "status": "error",
                    "code": 429,
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "message": f"Too many requests. Retry after {retry_after} seconds."
                }
            
            # Add rate limit headers to response (if applicable)
            remaining = limiter.get_remaining(client_key)
            
            result = await func(*args, **kwargs)
            
            # Attach rate limit info if result is dict
            if isinstance(result, dict):
                result['_rate_limit'] = {
                    'remaining': remaining,
                    'limit': max_requests,
                    'window': window_seconds
                }
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract client key
            if key_func:
                client_key = key_func(*args, **kwargs)
            else:
                client_key = kwargs.get('session_id', args[0] if args else 'unknown')
            
            allowed, retry_after = limiter.is_allowed(client_key)
            
            if not allowed:
                return {
                    "status": "error",
                    "code": 429,
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "message": f"Too many requests. Retry after {retry_after} seconds."
                }
            
            remaining = limiter.get_remaining(client_key)
            result = func(*args, **kwargs)
            
            if isinstance(result, dict):
                result['_rate_limit'] = {
                    'remaining': remaining,
                    'limit': max_requests,
                    'window': window_seconds
                }
            
            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
