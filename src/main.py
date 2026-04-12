import asyncio
import logging
import sys
import os

# Ensure the project root is in sys.path for internal module resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Assuming fastmcp is installed and used as the underlying MCP protocol wrapper
from mcp.server.fastmcp import FastMCP

# Core Configuration
from src.core.config import load_settings

# Core Engines
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.analysis.scoring_engine import ScoringEngine
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.engines.fusion.router import AutomaticPipelineRouter

# Strategy Registry & Master Orchestrator
from src.modes.registry import CognitiveEngineRegistry
from src.engines.orchestrator import CognitiveOrchestrator

# API Layer / Tools
from src.tools.cognitive_tools import register_cognitive_tools
from src.tools.session_tools import register_session_tools
from src.tools.export_tools import register_export_tools

# ============================================================================
# ENTERPRISE LOGGING CONFIGURATION
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("cct-mcp-server")

def main():
    """
    Application Entry Point.
    Bootstraps the dependencies, initializes the Cognitive Engine Registry,
    registers all MCP tools (Cognitive, Session, Export), and starts the server.
    """
    logger.info("Bootstrapping Creative Critical Thinking (CCT) MCP Server...")

    # 1. Load Configuration from Environment
    settings = load_settings()
    logger.info(f"Configuration loaded: {settings.server_name} @ {settings.host}:{settings.port}")

    # 2. Initialize the MCP Server Instance
    mcp_instance = FastMCP(settings.server_name, host=settings.host, port=settings.port)

    # 3. Dependency Injection: Instantiate Core Engines
    logger.info("Initializing Core Cognitive Infrastructure...")
    memory_manager = MemoryManager()
    sequential_engine = SequentialEngine(memory_manager)
    scoring_engine = ScoringEngine()  # NEW: Handles performance metrics
    
    # 4. Dependency Injection: Initialize Fusion & Routing Services
    logger.info("Initializing Fusion Orchestrator and Dynamic Router...")
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )
    automatic_router = AutomaticPipelineRouter(
        scoring_engine=scoring_engine
    )

    # 5. Dependency Injection: Initialize the Central Engine Registry
    logger.info("Loading Cognitive Strategies into Registry...")
    engine_registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )

    # 6. Expose the MCP Tools to the exterior via the Master Orchestrator
    logger.info("Initializing Master Orchestrator Facade...")
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=engine_registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )

    logger.info("Registering API boundaries (MCP Tools)...")

    # 6a. Register Cognitive Logic Tools (The Brains)
    register_cognitive_tools(
        mcp=mcp_instance,
        orchestrator=master_orchestrator
    )

    # 6b. Register Session Navigation Tools (The Memory Dashboard)
    register_session_tools(
        mcp=mcp_instance,
        orchestrator=master_orchestrator
    )

    # 6c. Register Export & Metacognitive Analysis Tools (The Auditor)
    register_export_tools(
        mcp=mcp_instance,
        orchestrator=master_orchestrator
    )

    logger.info("======================================================")
    logger.info(f"CCT MCP Server is LIVE.")
    logger.info(f"Server Name: {settings.server_name}")
    logger.info(f"Transport Protocol -> {settings.transport.upper()}")
    logger.info(f"Max Sessions: {settings.max_sessions}")
    logger.info("Ready for JSON-RPC over stdin/stdout.")
    logger.info("Press Ctrl+C to gracefully shut down.")
    logger.info("======================================================")

    try:
        # Start the FastMCP server (defaults to stdio if transport not specified)
        mcp_instance.run()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Terminating gracefully...")
    except Exception as e:
        logger.exception("A fatal runtime error occurred during server execution.")
        sys.exit(1)

if __name__ == "__main__":
    main()
