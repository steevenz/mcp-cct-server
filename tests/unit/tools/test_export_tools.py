import pytest
from unittest.mock import MagicMock
from mcp.server.fastmcp import FastMCP
from src.tools.export_tools import register_export_tools
from src.core.models.enums import CCTProfile

@pytest.fixture
def mcp_and_orchestrator():
    mcp = FastMCP("test-server")
    orchestrator = MagicMock()
    register_export_tools(mcp, orchestrator)
    return mcp, orchestrator

def test_export_thinking_session_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool = mcp._tool_manager.get_tool("export_thinking_session").fn
    
    mock_thought = MagicMock()
    mock_thought.model_dump.return_value = {"id": "1", "content": "note"}
    orchestrator.memory.get_session_history.return_value = [mock_thought]
    
    result = tool("sid_1")
    assert len(result["steps"]) == 1
    assert result["steps"][0]["id"] == "1"

def test_analyze_session_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool = mcp._tool_manager.get_tool("analyze_session").fn
    
    mock_session = MagicMock()
    mock_session.problem_statement = "Test"
    orchestrator.memory.get_session.return_value = mock_session
    
    mock_thought = MagicMock()
    mock_thought.content = "This is a very clear and distinct architectural proposal with no bias."
    orchestrator.memory.get_session_history.return_value = [mock_thought]
    
    result = tool("sid_1")
    assert result["session_id"] == "sid_1"
    assert "metrics" in result
    assert result["metrics"]["clarity_score"] > 0
