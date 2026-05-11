"""
Integration test for MCP Server workflow.
Tests the complete MCP server initialization, tool registration, and execution flow.
"""
import asyncio
import pytest
from src.core.config import load_settings
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.core.services.analysis.scoring import ScoringService
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.core.services.routing import IntelligenceRouter
from src.core.services.autonomous import AutonomousService
from src.core.services.llm.client import ThoughtGenerationService
from src.core.services.guidance import GuidanceService
from src.core.services.identity import IdentityService

def create_fusion_orchestrator(memory_manager, sequential_engine, scoring):
    """Helper function to create properly initialized FusionOrchestrator."""
    settings = load_settings()
    autonomous = AutonomousService(settings, memory_manager)
    thought_service = ThoughtGenerationService(settings)
    guidance = GuidanceService()
    identity = IdentityService()

    return FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring,
        sequential=sequential_engine,
        orchestration=autonomous,
        thought_service=thought_service,
        guidance=guidance,
        identity=identity
    ), autonomous, thought_service, guidance, identity

def create_registry(memory_manager, sequential_engine, fusion_orchestrator, scoring, autonomous, thought_service, guidance, identity):
    """Helper function to create properly initialized CognitiveEngineRegistry."""
    return CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator,
        autonomous=autonomous,
        thought_service=thought_service,
        guidance=guidance,
        identity=identity,
        scoring_engine=scoring
    )
from src.modes.registry import CognitiveEngineRegistry
from src.engines.orchestrator import CognitiveOrchestrator
from src.tools.cognitive import register_cognitive_tools
from src.tools.session import register_session_tools
from src.tools.export import register_export_tools
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
    scoring = ScoringService()

    assert memory_manager is not None
    assert sequential_engine is not None
    assert scoring is not None


def test_fusion_components_initialization(memory_manager, sequential_engine):
    """Test fusion orchestrator and router initialization."""
    scoring = ScoringService()

    fusion_orchestrator, autonomous, thought_service, guidance, identity = create_fusion_orchestrator(memory_manager, sequential_engine, scoring)

    automatic_router = IntelligenceRouter(
        scoring=scoring
    )

    assert fusion_orchestrator is not None
    assert automatic_router is not None


def test_engine_registry_initialization(memory_manager, sequential_engine):
    """Test cognitive engine registry initialization."""
    scoring = ScoringService()
    fusion_orchestrator, autonomous, thought_service, guidance, identity = create_fusion_orchestrator(memory_manager, sequential_engine, scoring)

    registry = create_registry(memory_manager, sequential_engine, fusion_orchestrator, scoring, autonomous, thought_service, guidance, identity)

    assert registry is not None


def test_master_orchestrator_initialization(memory_manager, sequential_engine):
    """Test master orchestrator initialization."""
    from src.main import bootstrap
    components = bootstrap()
    assert components["orchestrator"] is not None


def test_cognitive_tools_registration():
    from src.main import bootstrap
    from src.tools.simplified import register_simplified_tools

    components = bootstrap()
    mcp_instance = FastMCP("test_cct_server")
    register_simplified_tools(
        mcp=mcp_instance,
        orchestrator=components["orchestrator"],
        settings=components["settings"],
        complexity_service=components["complexity_service"],
    )

    tool_names = set(mcp_instance._tool_manager._tools.keys())
    expected = {
        "start_thinking",
        "continue_thinking",
        "recall_thinking",
        "decompose_thinking",
        "evaluate_thinking",
        "plan_thinking",
        "branch_thought",
        "export_thought",
        "log_thought",
        "health_thought",
    }
    assert tool_names == expected


def test_session_tools_registration():
    pytest.skip("Legacy session tool group replaced by unified simplified tools surface")


def test_export_tools_registration():
    pytest.skip("Legacy export tool group replaced by unified simplified tools surface")


def test_full_mcp_workflow_session_creation(memory_manager, sequential_engine):
    """Test full MCP workflow: session creation through tool execution."""
    pytest.skip("start_thinking executes an engine step and may require LLM connectivity; covered in dedicated workflow tests")


@pytest.mark.skip(reason="Async handling needs investigation")
def test_full_mcp_workflow_thought_execution(memory_manager, sequential_engine):
    """Test full MCP workflow: thought step execution through tool."""
    from src.core.models.enums import ThinkingStrategy

    scoring = ScoringService()
    fusion_orchestrator, autonomous, thought_service, guidance, identity = create_fusion_orchestrator(memory_manager, sequential_engine, scoring)
    automatic_router = IntelligenceRouter(
        scoring=scoring
    )
    registry = create_registry(memory_manager, sequential_engine, fusion_orchestrator, scoring, autonomous, thought_service, guidance, identity)
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router,
        identity=identity,
        autonomous=autonomous
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
    result = think_step_tool.fn(
        session_id=session_id,
        strategy="systematic",
        thought_content="Test thought content",
        thought_type="analysis",
        thought_number=1,
        estimated_total_thoughts=5,
        next_thought_needed=True
    )
    thought_result = asyncio.run(result)

    assert thought_result["status"] == "success"
    assert "generated_thought_id" in thought_result


@pytest.mark.skip(reason="Depends on test_full_mcp_workflow_thought_execution")
def test_full_mcp_workflow_session_export(memory_manager, sequential_engine):
    """Test full MCP workflow: session export through tool."""
    from src.core.models.enums import ThinkingStrategy

    scoring = ScoringService()
    fusion_orchestrator, autonomous, thought_service, guidance, identity = create_fusion_orchestrator(memory_manager, sequential_engine, scoring)
    automatic_router = IntelligenceRouter(
        scoring=scoring
    )
    registry = create_registry(memory_manager, sequential_engine, fusion_orchestrator, scoring, autonomous, thought_service, guidance, identity)
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router,
        identity=identity,
        autonomous=autonomous
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
    result = think_step_tool.fn(
        session_id=session_id,
        strategy="systematic",
        thought_content="Test thought content",
        thought_type="analysis",
        thought_number=1,
        estimated_total_thoughts=5,
        next_thought_needed=False
    )
    asyncio.run(result)

    # Export session
    export_tool = mcp_instance._tool_manager.get_tool("export_thinking_session")
    export_result = export_tool.fn(session_id=session_id, session_token=session_token)

    # Successful export returns steps array directly
    assert "steps" in export_result
    assert len(export_result["steps"]) >= 1  # At least one thought was exported


def test_all_tools_registered():
    """Test that all expected MCP tools are registered."""
    pytest.skip("Covered by test_cognitive_tools_registration, which asserts the unified 10-tool surface")
