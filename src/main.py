import logging
import sys
import os
import signal
import time
from datetime import datetime

# Ensure the project root is in sys.path for internal module resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

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

# New Hybrid Services
from src.core.services.complexity import ComplexityService
from src.core.services.guidance import GuidanceService
from src.core.services.orchestration import OrchestrationService
from src.infrastructure.llm.client import LLMClient

# API Layer / Tools
from src.tools.simplified_tools import register_simplified_tools
from src.tools.export_tools import register_export_tools

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

START_TIME = time.time()

def bootstrap():
    """
    Bootstraps the dependencies and initializes the central orchestrator.
    Returns a dictionary of initialized components.
    """
    logger.info("Bootstrapping CCT Cognitive Infrastructure...")
    
    settings = load_settings()
    logging.getLogger().setLevel(getattr(logging, settings.log_level))
    
    memory_manager = MemoryManager()
    sequential_engine = SequentialEngine(memory_manager)
    scoring_engine = ScoringEngine()
    
    complexity_service = ComplexityService()
    guidance_service = GuidanceService()
    orchestration_service = OrchestrationService(settings)
    llm_client = LLMClient(settings)
    
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine,
        orchestration=orchestration_service,
        llm=llm_client,
        guidance=guidance_service
    )
    
    automatic_router = AutomaticPipelineRouter(scoring_engine=scoring_engine)
    
    engine_registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator,
        orchestration=orchestration_service,
        llm=llm_client,
        guidance=guidance_service
    )
    
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=engine_registry,
        fusion_engine=fusion_orchestrator,
        router=automatic_router
    )
    
    return {
        "settings": settings,
        "mcp_instance": FastMCP(settings.server_name, host=settings.host, port=settings.port),
        "orchestrator": master_orchestrator,
        "complexity_service": complexity_service
    }

# Bootstrap once
components = bootstrap()
mcp_instance = components["mcp_instance"]
settings = components["settings"]

# Register Tools
register_simplified_tools(
    mcp=mcp_instance,
    orchestrator=components["orchestrator"],
    settings=settings,
    complexity_service=components["complexity_service"]
)
register_export_tools(
    mcp=mcp_instance,
    orchestrator=components["orchestrator"],
    settings=settings
)

# ============================================================================
# FASTAPI WRAPPER (ELITE WINDOWS ENDPOINT)
# ============================================================================

app = FastAPI(title="CCT Cognitive OS API")

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def status():
    uptime = time.time() - START_TIME
    
    # Extract global usage stats from MemoryManager
    memory_manager = components.get("orchestrator").memory_manager
    usage_stats = memory_manager.get_aggregate_usage()
    
    return {
        "server": settings.server_name,
        "uptime_seconds": int(uptime),
        "llm_provider": settings.llm_provider or "GUIDED",
        "transport": settings.transport.upper(),
        "log_level": settings.log_level,
        "global_usage": {
            "tokens": {
                "input": usage_stats["prompt_tokens"],
                "output": usage_stats["completion_tokens"],
                "total": usage_stats["total_tokens"]
            },
            "costs": {
                "usd": usage_stats["cost_usd"],
                "idr": usage_stats["cost_idr"]
            },
            "total_sessions": usage_stats["session_count"]
        },
        "features": ["hybrid_orchestration", "actor_critic", "memory_persistence", "financial_telemetry"]
    }

# MCP Mount Configuration
# The http_app() provides the Starlette/ASGI app for modern HTTP/SSE
mcp_app = mcp_instance.http_app(path="/sync")
app.mount("/cognitive-api/v1", mcp_app)
# Sync the lifespan for session initialization
app.router.lifespan_context = mcp_app.lifespan

def main():
    transport = settings.transport.strip().lower()
    
    if transport in ("sse", "http"):
        logger.info(f"Launching FastAPI Host on {settings.host}:{settings.port}...")
        logger.info(f"SSE Endpoint: http://{settings.host}:{settings.port}/cognitive-api/v1/sync")
        uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
    else:
        # Fallback to standard STDIO transport
        logger.info("Launching standard STDIO transport...")
        mcp_instance.run(transport="stdio")

if __name__ == "__main__":
    main()
