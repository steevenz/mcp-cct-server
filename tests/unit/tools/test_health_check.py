"""
Tests for health check endpoint.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from src.tools.session_tools import register_session_tools
from src.engines.orchestrator import CognitiveOrchestrator


@pytest.fixture
def mcp_and_orchestrator():
    """Create mocked MCP and orchestrator for health check tests."""
    mcp = FastMCP("test-server")
    orchestrator = MagicMock()
    
    # Mock memory manager
    orchestrator.memory = MagicMock()
    orchestrator.memory.list_sessions.return_value = ["session_1", "session_2"]
    orchestrator.memory.get_session.return_value = None  # For health check ping
    
    register_session_tools(mcp, orchestrator)
    return mcp, orchestrator


class TestHealthCheck:
    """Test health check endpoint functionality."""
    
    def test_health_check_returns_success(self, mcp_and_orchestrator):
        """Test that health check returns healthy status."""
        mcp, orchestrator = mcp_and_orchestrator
        
        tool_func = mcp._tool_manager.get_tool("health_check").fn
        result = tool_func()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "version" in result
        assert result["version"] == "2026.04.12"
    
    def test_health_check_includes_services_status(self, mcp_and_orchestrator):
        """Test that health check includes services status."""
        mcp, orchestrator = mcp_and_orchestrator
        
        tool_func = mcp._tool_manager.get_tool("health_check").fn
        result = tool_func()
        
        assert "services" in result
        assert "database" in result["services"]
        assert "memory_manager" in result["services"]
        assert result["services"]["database"] == "healthy"
        assert result["services"]["memory_manager"] == "healthy"
    
    def test_health_check_includes_metrics(self, mcp_and_orchestrator):
        """Test that health check includes metrics."""
        mcp, orchestrator = mcp_and_orchestrator
        
        tool_func = mcp._tool_manager.get_tool("health_check").fn
        result = tool_func()
        
        assert "metrics" in result
        assert "active_sessions" in result["metrics"]
        assert "response_time_ms" in result["metrics"]
        assert "rate_limit_window" in result["metrics"]
        assert "rate_limit_max" in result["metrics"]
        
        # Verify active sessions count
        assert result["metrics"]["active_sessions"] == 2
    
    def test_health_check_with_db_error(self, mcp_and_orchestrator):
        """Test health check handles database errors gracefully."""
        mcp, orchestrator = mcp_and_orchestrator
        
        # Mock DB error
        orchestrator.memory.get_session.side_effect = Exception("DB Connection Error")
        
        tool_func = mcp._tool_manager.get_tool("health_check").fn
        result = tool_func()
        
        # Should still return but with degraded status
        assert result["status"] == "degraded"
        assert "degraded" in result["services"]["database"].lower()
    
    def test_health_check_response_time_measured(self, mcp_and_orchestrator):
        """Test that response time is measured and included."""
        mcp, orchestrator = mcp_and_orchestrator
        
        tool_func = mcp._tool_manager.get_tool("health_check").fn
        result = tool_func()
        
        response_time = result["metrics"]["response_time_ms"]
        assert isinstance(response_time, (int, float))
        assert response_time >= 0  # Should be non-negative
        assert response_time < 1000  # Should be reasonably fast (< 1 second)
    
    def test_health_check_timestamp_format(self, mcp_and_orchestrator):
        """Test that timestamp is in ISO format."""
        mcp, orchestrator = mcp_and_orchestrator
        
        tool_func = mcp._tool_manager.get_tool("health_check").fn
        result = tool_func()
        
        timestamp = result["timestamp"]
        # Should be valid ISO format
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp {timestamp} is not valid ISO format")
    
    def test_health_check_rate_limit_info(self, mcp_and_orchestrator):
        """Test that rate limiting info is included."""
        mcp, orchestrator = mcp_and_orchestrator
        
        tool_func = mcp._tool_manager.get_tool("health_check").fn
        result = tool_func()
        
        assert result["metrics"]["rate_limit_window"] == 60
        assert result["metrics"]["rate_limit_max"] == 100
