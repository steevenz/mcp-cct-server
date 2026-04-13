"""
Tests for rate limiting module.
"""
import pytest
import time
from src.core.rate_limiter import (
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    RateLimitConfig,
    rate_limited,
    get_rate_limiter
)


class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiting algorithm."""
    
    def test_initial_request_allowed(self):
        """Test that first request is always allowed."""
        limiter = SlidingWindowRateLimiter(RateLimitConfig(max_requests=5, window_seconds=60))
        allowed, retry_after = limiter.is_allowed("client_1")
        
        assert allowed is True
        assert retry_after is None
    
    def test_request_count_tracking(self):
        """Test that requests are tracked correctly."""
        limiter = SlidingWindowRateLimiter(RateLimitConfig(max_requests=3, window_seconds=60))
        
        # Make 3 requests (all should be allowed)
        for _ in range(3):
            allowed, _ = limiter.is_allowed("client_1")
            assert allowed is True
        
        # 4th request should be blocked
        allowed, retry_after = limiter.is_allowed("client_1")
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    def test_window_sliding(self):
        """Test that old requests fall out of the window."""
        limiter = SlidingWindowRateLimiter(RateLimitConfig(max_requests=2, window_seconds=1))
        
        # Make 2 requests
        limiter.is_allowed("client_1")
        limiter.is_allowed("client_1")
        
        # Should be blocked
        allowed, _ = limiter.is_allowed("client_1")
        assert allowed is False
        
        # Wait for window to slide
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed("client_1")
        assert allowed is True
    
    def test_different_clients_isolated(self):
        """Test that rate limits are isolated per client."""
        limiter = SlidingWindowRateLimiter(RateLimitConfig(max_requests=2, window_seconds=60))
        
        # Client 1 uses up their quota
        limiter.is_allowed("client_1")
        limiter.is_allowed("client_1")
        
        # Client 2 should still be allowed
        allowed, _ = limiter.is_allowed("client_2")
        assert allowed is True
    
    def test_get_remaining(self):
        """Test remaining request calculation."""
        limiter = SlidingWindowRateLimiter(RateLimitConfig(max_requests=5, window_seconds=60))
        
        assert limiter.get_remaining("new_client") == 5
        
        limiter.is_allowed("new_client")
        assert limiter.get_remaining("new_client") == 4
        
        limiter.is_allowed("new_client")
        limiter.is_allowed("new_client")
        assert limiter.get_remaining("new_client") == 2
    
    def test_reset(self):
        """Test manual rate limit reset."""
        limiter = SlidingWindowRateLimiter(RateLimitConfig(max_requests=2, window_seconds=60))
        
        # Use up quota
        limiter.is_allowed("client_1")
        limiter.is_allowed("client_1")
        
        # Blocked
        allowed, _ = limiter.is_allowed("client_1")
        assert allowed is False
        
        # Reset
        limiter.reset("client_1")
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed("client_1")
        assert allowed is True


class TestTokenBucketRateLimiter:
    """Test token bucket rate limiting algorithm."""
    
    def test_burst_allowed(self):
        """Test that burst requests are allowed up to bucket size."""
        limiter = TokenBucketRateLimiter(rate=1.0, burst_size=5)
        
        # Should allow burst of 5
        for _ in range(5):
            allowed, _ = limiter.is_allowed("client_1")
            assert allowed is True
        
        # 6th should be blocked
        allowed, wait_time = limiter.is_allowed("client_1")
        assert allowed is False
        assert wait_time is not None
        assert wait_time > 0
    
    def test_token_refill(self):
        """Test that tokens refill over time."""
        limiter = TokenBucketRateLimiter(rate=10.0, burst_size=1)
        
        # Use the only token
        allowed, _ = limiter.is_allowed("client_1")
        assert allowed is True
        
        # Should be blocked
        allowed, wait_time = limiter.is_allowed("client_1")
        assert allowed is False
        
        # Wait for token refill
        time.sleep(0.15)  # 10 tokens/second = 0.1s per token
        
        # Should be allowed now
        allowed, _ = limiter.is_allowed("client_1")
        assert allowed is True


class TestRateLimitedDecorator:
    """Test rate limiting decorator."""
    
    def test_sync_function_rate_limited(self):
        """Test decorator on synchronous function."""
        
        @rate_limited(max_requests=2, window_seconds=60)
        def test_func(session_id: str, data: str) -> dict:
            return {"status": "success", "data": data}
        
        # First 2 calls should succeed
        result1 = test_func("session_1", "test1")
        assert result1["status"] == "success"
        
        result2 = test_func("session_1", "test2")
        assert result2["status"] == "success"
        
        # 3rd call should be rate limited
        result3 = test_func("session_1", "test3")
        assert result3["status"] == "error"
        assert result3["code"] == 429
        assert "retry_after" in result3
    
    def test_async_function_rate_limited(self):
        """Test decorator on async function."""
        import asyncio
        
        @rate_limited(max_requests=2, window_seconds=60)
        async def async_test_func(session_id: str, data: str) -> dict:
            return {"status": "success", "data": data}
        
        # First 2 calls should succeed
        result1 = asyncio.run(async_test_func("session_2", "test1"))
        assert result1["status"] == "success"
        
        result2 = asyncio.run(async_test_func("session_2", "test2"))
        assert result2["status"] == "success"
        
        # 3rd call should be rate limited
        result3 = asyncio.run(async_test_func("session_2", "test3"))
        assert result3["status"] == "error"
        assert result3["code"] == 429
    
    def test_rate_limit_info_in_response(self):
        """Test that rate limit info is added to successful responses."""
        
        @rate_limited(max_requests=5, window_seconds=60)
        def test_func(session_id: str) -> dict:
            return {"result": "ok"}
        
        result = test_func("session_3")
        
        assert "_rate_limit" in result
        assert result["_rate_limit"]["limit"] == 5
        assert result["_rate_limit"]["window"] == 60
        assert result["_rate_limit"]["remaining"] == 4
    
    def test_different_sessions_independent(self):
        """Test that different sessions have independent rate limits."""
        
        @rate_limited(max_requests=1, window_seconds=60)
        def test_func(session_id: str) -> dict:
            return {"status": "success"}
        
        # Session 1 uses its only request
        result1 = test_func("session_a")
        assert result1["status"] == "success"
        
        # Session 1 blocked
        result2 = test_func("session_a")
        assert result2["status"] == "error"
        
        # Session 2 should still work
        result3 = test_func("session_b")
        assert result3["status"] == "success"


class TestGlobalRateLimiter:
    """Test global rate limiter singleton."""
    
    def test_singleton_instance(self):
        """Test that get_rate_limiter returns same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
    
    def test_global_limiter_has_default_config(self):
        """Test default configuration of global limiter."""
        limiter = get_rate_limiter()
        
        assert limiter.config.max_requests == 100
        assert limiter.config.window_seconds == 60
