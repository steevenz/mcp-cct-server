"""
Integration test for MCP Server workflow.
Tests the complete MCP server initialization, tool registration, and execution flow.
"""
import asyncio
import pytest
from src.core.config import load_settings
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.analysis.scoring_engine import ScoringEngine
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.engines.fusion.router import AutomaticPipelineRouter
from src.modes.registry import CognitiveEngineRegistry
from src.engines.orchestrator import CognitiveOrchestrator
from src.tools.cognitive_tools import register_cognitive_tools
from src.tools.session_tools import register_session_tools
from src.tools.export_tools import register_export_tools
from mcp.server.fastmcp import FastMCP


def test_mcp_server_initialization():
    """Test complete MCP server initialization workflow."""
    # 1. Load Configuration
    settings = load_settings()
    assert settings.server_name is not None
    assert settings.host is not None
    assert settings.port > 0


def test_core_engines_initialization():
    """Test core engines initialization."""
    memory_manager = MemoryManager()
    sequential_engine = SequentialEngine(memory_manager)
    scoring_engine = ScoringEngine()
    
    assert memory_manager is not None
    assert sequential_engine is not None
    assert scoring_engine is not None


def test_fusion_components_initialization(memory_manager, sequential_engine):
    """Test fusion orchestrator and router initialization."""
    scoring_engine = ScoringEngine()
    
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    
    assert fusion_orchestrator is not None
    assert automatic_router is not None


def test_engine_registry_initialization(memory_manager, sequential_engine):
    """Test cognitive engine registry initialization."""
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    
    assert registry is not None


def test_master_orchestrator_initialization(memory_manager, sequential_engine):
    """Test master orchestrator initialization."""
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    assert master_orchestrator is not None


def test_cognitive_tools_registration():
    """Test cognitive tools registration to MCP server."""
    memory_manager = MemoryManager()
    sequential_engine = SequentialEngine(memory_manager)
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    mcp_instance = FastMCP("test_cct_server")
    register_cognitive_tools(mcp_instance, master_orchestrator)
    
    # Verify tools are registered
    tool_names = list(mcp_instance._tool_manager._tools.keys())
    assert "cct_think_step" in tool_names
    assert "actor_critic_dialog" in tool_names


def test_session_tools_registration():
    """Test session tools registration to MCP server."""
    memory_manager = MemoryManager()
    sequential_engine = SequentialEngine(memory_manager)
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    mcp_instance = FastMCP("test_cct_server")
    register_session_tools(mcp_instance, master_orchestrator)
    
    # Verify tools are registered
    tool_names = list(mcp_instance._tool_manager._tools.keys())
    assert "list_cct_sessions" in tool_names
    assert "get_thinking_path" in tool_names


def test_export_tools_registration():
    """Test export tools registration to MCP server."""
    memory_manager = MemoryManager()
    sequential_engine = SequentialEngine(memory_manager)
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    mcp_instance = FastMCP("test_cct_server")
    register_export_tools(mcp_instance, master_orchestrator)
    
    # Verify tools are registered
    tool_names = list(mcp_instance._tool_manager._tools.keys())
    assert "export_thinking_session" in tool_names
    assert "analyze_session" in tool_names


def test_full_mcp_workflow_session_creation(memory_manager, sequential_engine):
    """Test full MCP workflow: session creation through tool execution."""
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    mcp_instance = FastMCP("test_cct_server")
    register_session_tools(mcp_instance, master_orchestrator)
    
    # Get the start_cct_session tool
    start_session_tool = mcp_instance._tool_manager.get_tool("start_cct_session")
    
    # Execute the tool
    result = start_session_tool.fn(
        problem_statement="Test problem for MCP workflow",
        profile="balanced"
    )
    
    assert result["status"] == "success"
    assert "session_id" in result
    assert result["session_id"] is not None


def test_full_mcp_workflow_thought_execution(memory_manager, sequential_engine):
    """Test full MCP workflow: thought step execution through tool."""
    from src.core.models.enums import ThinkingStrategy
    
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    mcp_instance = FastMCP("test_cct_server")
    register_session_tools(mcp_instance, master_orchestrator)
    register_cognitive_tools(mcp_instance, master_orchestrator)
    
    # First, create a session
    start_session_tool = mcp_instance._tool_manager.get_tool("start_cct_session")
    session_result = start_session_tool.fn(
        problem_statement="Test problem",
        profile="balanced"
    )
    session_id = session_result["session_id"]
    session_token = session_result.get("session_token", "")
    
    # Then execute a thought step (async function requires awaiting)
    think_step_tool = mcp_instance._tool_manager.get_tool("cct_think_step")
    thought_result = asyncio.run(think_step_tool.fn(
        session_id=session_id,
        strategy="systematic",
        thought_content="Test thought content",
        thought_type="analysis",
        thought_number=1,
        estimated_total_thoughts=5,
        next_thought_needed=True
    ))
    
    assert thought_result["status"] == "success"
    assert "generated_thought_id" in thought_result


def test_full_mcp_workflow_session_export(memory_manager, sequential_engine):
    """Test full MCP workflow: session export through tool."""
    from src.core.models.enums import ThinkingStrategy
    
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    mcp_instance = FastMCP("test_cct_server")
    register_session_tools(mcp_instance, master_orchestrator)
    register_cognitive_tools(mcp_instance, master_orchestrator)
    register_export_tools(mcp_instance, master_orchestrator)
    
    # Create session and add thought
    start_session_tool = mcp_instance._tool_manager.get_tool("start_cct_session")
    session_result = start_session_tool.fn(
        problem_statement="Test problem",
        profile="balanced"
    )
    session_id = session_result["session_id"]
    session_token = session_result.get("session_token", "")
    
    think_step_tool = mcp_instance._tool_manager.get_tool("cct_think_step")
    asyncio.run(think_step_tool.fn(
        session_id=session_id,
        strategy="systematic",
        thought_content="Test thought content",
        thought_type="analysis",
        thought_number=1,
        estimated_total_thoughts=5,
        next_thought_needed=False
    ))
    
    # Export session
    export_tool = mcp_instance._tool_manager.get_tool("export_thinking_session")
    export_result = export_tool.fn(session_id=session_id, session_token=session_token)
    
    # Successful export returns steps array directly
    assert "steps" in export_result
    assert len(export_result["steps"]) >= 1  # At least one thought was exported


def test_all_tools_registered():
    """Test that all expected MCP tools are registered."""
    memory_manager = MemoryManager()
    sequential_engine = SequentialEngine(memory_manager)
    scoring_engine = ScoringEngine()
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    mcp_instance = FastMCP("test_cct_server")
    register_cognitive_tools(mcp_instance, master_orchestrator)
    register_session_tools(mcp_instance, master_orchestrator)
    register_export_tools(mcp_instance, master_orchestrator)
    
    # Verify all expected tools are registered
    tool_names = list(mcp_instance._tool_manager._tools.keys())
    
    # Cognitive tools
    assert "cct_think_step" in tool_names
    assert "actor_critic_dialog" in tool_names
    
    # Session tools
    assert "start_cct_session" in tool_names
    assert "list_cct_sessions" in tool_names
    assert "get_thinking_path" in tool_names
    
    # Export tools
    assert "export_thinking_session" in tool_names
    assert "analyze_session" in tool_names
