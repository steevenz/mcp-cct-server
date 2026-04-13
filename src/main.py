import logging
import sys
import os
import signal

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
# Simplified Tools: Hanya 3 tools dengan automatic strategy selection
from src.tools.simplified_tools import register_simplified_tools
from src.tools.export_tools import register_export_tools
# Legacy tools (disabled untuk simplifikasi):
# from src.tools.cognitive_tools import register_cognitive_tools
# from src.tools.session_tools import register_session_tools

# ============================================================================
# ENTERPRISE LOGGING CONFIGURATION
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
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
    try:
        settings = load_settings()
        logger.info(f"Configuration loaded: {settings.server_name} @ {settings.host}:{settings.port}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Reconfigure logging level based on settings
    logging.getLogger().setLevel(getattr(logging, settings.log_level))

    # Setup signal handlers for graceful shutdown (SIGTERM for Docker/systemd)
    def _signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # 2. Initialize the MCP Server Instance
    mcp_instance = FastMCP(settings.server_name, host=settings.host, port=settings.port)

    # 3. Dependency Injection: Instantiate Core Engines
    logger.info("Initializing Core Cognitive Infrastructure...")
    try:
        memory_manager = MemoryManager()
        sequential_engine = SequentialEngine(memory_manager)
        scoring_engine = ScoringEngine()  # NEW: Handles performance metrics
        
        # Validate critical components
        if not memory_manager or not sequential_engine or not scoring_engine:
            raise RuntimeError("Failed to initialize critical engine components")
            
        logger.info("Core engines initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize core engines: {e}")
        sys.exit(1)
    
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

    # 6a. Register Simplified Tools (Hanya 3 tools dengan automatic strategy)
    # session_start, session_think, session_list
    register_simplified_tools(
        mcp=mcp_instance,
        orchestrator=master_orchestrator,
        settings=settings
    )

    # 6b. Register Export & Metacognitive Analysis Tools (The Auditor)
    register_export_tools(
        mcp=mcp_instance,
        orchestrator=master_orchestrator,
        settings=settings
    )


    logger.info("======================================================")
    logger.info(f"CCT MCP Server is LIVE (Simplified Mode).")
    logger.info(f"Server Name: {settings.server_name}")
    logger.info(f"Transport Protocol -> {settings.transport.upper()}")
    logger.info(f"Max Sessions: {settings.max_sessions}")
    logger.info("Simplified Toolset: thinking, rethinking, list_thinking")
    logger.info("Automatic Strategy: Enabled (Simple/Moderate/Complex detection)")
    
    # Transport-specific readiness message
    if settings.transport.strip().lower() in {"sse", "http"}:
        logger.info(f"Ready for HTTP/SSE at http://{settings.host}:{settings.port}/sse")
        logger.info(f"Messages endpoint at http://{settings.host}:{settings.port}/messages")
    else:
        logger.info("Ready for JSON-RPC over stdin/stdout.")
        
    logger.info("Press Ctrl+C to gracefully shut down.")
    logger.info("======================================================")

    try:
        transport = settings.transport.strip().lower()
        if transport == "http":
            transport = "sse"
        mcp_instance.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Terminating gracefully...")
    except Exception as e:
        logger.exception("A fatal runtime error occurred during server execution.")
        sys.exit(1)

if __name__ == "__main__":
    main()
