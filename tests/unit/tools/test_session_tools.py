import pytest
from unittest.mock import MagicMock
from mcp.server.fastmcp import FastMCP
from src.tools.session_tools import register_session_tools
from src.core.models.enums import CCTProfile

@pytest.fixture
def mcp_and_orchestrator():
    mcp = FastMCP("test-server")
    orchestrator = MagicMock()
    register_session_tools(mcp, orchestrator)
    return mcp, orchestrator

def test_start_cct_session_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    
    # Extract the tool function from FastMCP registry
    # FastMCP stores tools in a dictionary-like structure
    tool_func = mcp._tool_manager.get_tool("start_cct_session").fn
    
    orchestrator.start_session.return_value = {"session_id": "sid_123"}
    
    # Execute the tool
    result = tool_func("The problem", "balanced")
    
    orchestrator.start_session.assert_called_once_with("The problem", "balanced")
    assert result["session_id"] == "sid_123"

def test_list_cct_sessions_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool_func = mcp._tool_manager.get_tool("list_cct_sessions").fn
    
    orchestrator.memory.list_sessions.return_value = ["sid_1", "sid_2"]
    
    result = tool_func()
    
    assert result["sessions"] == ["sid_1", "sid_2"]

def test_get_thinking_path_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool_func = mcp._tool_manager.get_tool("get_thinking_path").fn
    
    # Mock session object
    mock_session = MagicMock()
    mock_session.session_id = "sid_1"
    mock_session.problem_statement = "Test"
    mock_session.profile = CCTProfile.BALANCED
    
    orchestrator.memory.get_session.return_value = mock_session
    orchestrator.memory.get_session_history.return_value = []
    
    result = tool_func("sid_1")
    
    assert result["session_id"] == "sid_1"
    assert result["profile"] == "balanced"
    assert result["steps"] == []

def test_get_thinking_path_not_found(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool_func = mcp._tool_manager.get_tool("get_thinking_path").fn
    
    orchestrator.memory.get_session.return_value = None
    
    result = tool_func("ghost")
    assert result == {"error": "session_not_found"}

def test_suggest_cognitive_pipeline_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool_func = mcp._tool_manager.get_tool("suggest_cognitive_pipeline").fn

    result = tool_func("Implement new feature for export tool")
    assert result["category"] in {"DEBUG", "ARCH", "FEAT", "SEC", "BIZ", "GENERIC"}
    assert isinstance(result["pipeline"], list)
    assert isinstance(result["estimated_total_thoughts"], int)
