import pytest
from unittest.mock import MagicMock, AsyncMock
from mcp.server.fastmcp import FastMCP
from src.tools.cognitive_tools import register_cognitive_tools
from src.core.models.enums import ThinkingStrategy, ThoughtType

@pytest.fixture
def mcp_and_orchestrator():
    mcp = FastMCP("test-server")
    orchestrator = MagicMock()
    register_cognitive_tools(mcp, orchestrator)
    return mcp, orchestrator

@pytest.mark.asyncio
async def test_cct_think_step_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool = mcp._tool_manager.get_tool("cct_think_step").fn
    
    orchestrator.execute_strategy.return_value = {"status": "success"}
    
    result = await tool(
        session_id="sid_1",
        thought_content="Thinking...",
        strategy="systematic",
        thought_type="analysis"
    )
    
    # Verify Enum conversion and payload wrapping
    orchestrator.execute_strategy.assert_called_once()
    args, kwargs = orchestrator.execute_strategy.call_args
    assert args[0] == "sid_1"
    assert args[1] == ThinkingStrategy.SYSTEMATIC
    assert args[2]["thought_content"] == "Thinking..."
    assert args[2]["thought_type"] == ThoughtType.ANALYSIS
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_actor_critic_dialog_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool = mcp._tool_manager.get_tool("actor_critic_dialog").fn
    
    orchestrator.execute_strategy.return_value = {"status": "success"}
    
    result = await tool(session_id="sid_1", target_thought_id="tt_1")
    
    orchestrator.execute_strategy.assert_called_once_with(
        "sid_1", 
        ThinkingStrategy.ACTOR_CRITIC_LOOP, 
        {"target_thought_id": "tt_1", "critic_persona": "Security Expert"}
    )
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_lateral_pivot_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool = mcp._tool_manager.get_tool("lateral_pivot_brainstorm").fn
    
    orchestrator.execute_strategy.return_value = {"status": "success"}
    
    result = await tool(session_id="sid_1", current_paradigm="Local local")
    
    orchestrator.execute_strategy.assert_called_once_with(
        "sid_1",
        ThinkingStrategy.UNCONVENTIONAL_PIVOT,
        {"current_paradigm": "Local local", "provocation_method": "REVERSE_ASSUMPTION"}
    )

@pytest.mark.asyncio
async def test_temporal_horizon_tool(mcp_and_orchestrator):
    mcp, orchestrator = mcp_and_orchestrator
    tool = mcp._tool_manager.get_tool("temporal_horizon_projection").fn
    
    orchestrator.execute_strategy.return_value = {"status": "success"}
    
    result = await tool(session_id="sid_1", target_thought_id="tt_1")
    
    orchestrator.execute_strategy.assert_called_once_with(
        "sid_1",
        ThinkingStrategy.LONG_TERM_HORIZON,
        {"target_thought_id": "tt_1", "projection_scale": "LONG_TERM"}
    )
