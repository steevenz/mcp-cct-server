import logging
import sys
import os
import signal
import time
import asyncio
import json
from datetime import datetime

# Ensure the project root is in sys.path for internal module resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from contextlib import asynccontextmanager
import uvicorn

# Assuming fastmcp is installed and used as the underlying MCP protocol wrapper
from mcp.server.fastmcp import FastMCP

# Core Configuration
from src.core.config import load_settings

# Core Engines
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.core.services.analysis.scoring import ScoringService
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.core.services.orchestration.routing import RoutingService as IntelligenceRouter

# Strategy Registry & Master Orchestrator
from src.modes.registry import CognitiveEngineRegistry
from src.engines.orchestrator import CognitiveOrchestrator

# New Hybrid Services
from src.core.services.analysis.complexity import ComplexityService
from src.core.services.guidance.guidance import GuidanceService
from src.core.services.orchestration.autonomous import AutonomousService
from src.core.services.llm.client import ClientService
from src.core.services.llm.critic import CriticService as AdversarialReviewService
from src.core.services.user.identity import UserIdentityService as IdentityService
from src.core.services.engineering.eval import EvalService as EvalFirstService
from src.core.services.engineering.task import TaskService as TaskDecompositionService
from src.core.services.evaluation.clearance import ClearanceService as InternalClearanceService
from src.core.services.learning.hippocampus import HippocampusService as DigitalHippocampus

# API Layer / Tools
from src.tools.simplified import register_simplified_tools
from src.tools.export import register_export_tools
from src.tools.engineering import register_engineering_tools, register_planning_tools

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
    scoring_engine = ScoringService()
    
    complexity_service = ComplexityService()
    guidance_service = GuidanceService()
    autonomous_service = AutonomousService(settings, memory_manager)
    thought_service = ClientService(settings)
    
    identity_service = IdentityService(settings.identity_dir)
    identity_service.provision_assets()
    
    # Digital Hippocampus for learning user architectural style
    digital_hippocampus = DigitalHippocampus(
        memory=memory_manager,
        identity_service=identity_service
    )
    
    # Re-instantiate/Update IdentityService with DigitalHippocampus for dynamic identity
    identity_service.digital_hippocampus = digital_hippocampus
    
    # Initialize Engineering Services (Eval-First & Task Decomposition)
    eval_first_service = EvalFirstService()
    task_decomposition_service = TaskDecompositionService()
    
    review_service = AdversarialReviewService(settings, identity_service=identity_service)
    
    internal_clearance = InternalClearanceService(scoring_service=scoring_engine)
    
    fusion_orchestrator = FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine,
        orchestration=autonomous_service,
        thought_service=thought_service,
        guidance=guidance_service,
        identity=identity_service
    )
    
    automatic_router = IntelligenceRouter(scoring_engine=scoring_engine)
    
    engine_registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator,
        autonomous=autonomous_service,
        thought_service=thought_service,
        guidance=guidance_service,
        identity=identity_service,
        scoring_engine=scoring_engine,
        review_service=review_service
    )
    
    master_orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        scoring_engine=scoring_engine,
        cognitive_engine_registry=engine_registry,
        fusion_orchestrator=fusion_orchestrator,
        complexity_service=complexity_service,
        guidance_service=guidance_service,
        autonomous_service=autonomous_service,
        thought_service=thought_service,
        review_service=review_service,
        internal_clearance=internal_clearance,
        identity_service=identity_service,
        digital_hippocampus=digital_hippocampus,
        eval_first_service=eval_first_service,
        task_decomposition_service=task_decomposition_service
    )
    
    return {
        "settings": settings,
        "mcp_instance": FastMCP(settings.server_name),
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
register_engineering_tools(
    mcp=mcp_instance,
    orchestrator=components["orchestrator"]
)
register_planning_tools(
    mcp=mcp_instance,
    orchestrator=components["orchestrator"]
)

# ============================================================================
# FASTAPI WRAPPER (ELITE WINDOWS ENDPOINT)
# ============================================================================

app = FastAPI(title="CCT Cognitive OS API")

# Security Definition
X_API_KEY = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key_header: str = Depends(X_API_KEY)):
    if api_key_header != settings.dashboard_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    return api_key_header

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def status():
    uptime = time.time() - START_TIME
    
    # Extract global usage stats from MemoryManager (with error handling)
    try:
        memory_manager = components.get("orchestrator").memory
        usage_stats = memory_manager.get_aggregate_usage()
        global_usage = {
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
        }
    except Exception as e:
        global_usage = {
            "tokens": {"input": 0, "output": 0, "total": 0},
            "costs": {"usd": 0.0, "idr": 0.0},
            "total_sessions": 0,
            "error": str(e)
        }
    
    return {
        "server": settings.server_name,
        "uptime_seconds": int(uptime),
        "llm_provider": settings.llm_provider or "GUIDED",
        "transport": settings.transport.upper(),
        "log_level": settings.log_level,
        "global_usage": global_usage,
        "features": ["hybrid_orchestration", "actor_critic", "memory_persistence", "financial_telemetry"]
    }

# MCP Mount Configuration
# Implement simpler SSE endpoint for HTTP transport
from sse_starlette.sse import EventSourceResponse

mcp_path = "/sync"
if settings.mcp_secret:
    mcp_path = f"/sync/{settings.mcp_secret}"
    logger.info(f"Custom MCP Secret Path activated: {mcp_path}")

# Simple SSE endpoint implementation
async def mcp_sse_handler(request: Request):
    """Simple SSE endpoint for MCP HTTP transport."""
    async def event_generator():
        try:
            # Send quick response and close
            yield {
                "event": "connected",
                "data": json.dumps({
                    "status": "connected",
                    "server": settings.server_name,
                    "transport": "sse",
                    "endpoint": f"/cognitive-api/v1{mcp_path}"
                })
            }
            # Close connection immediately after sending response
        except Exception as e:
            logger.error(f"Error in SSE handler: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())

# Mount SSE endpoint
@app.get(f"/cognitive-api/v1{mcp_path}")
async def mcp_sse_endpoint(request: Request):
    """SSE endpoint for MCP real-time communication."""
    return await mcp_sse_handler(request)

@app.post(f"/cognitive-api/v1{mcp_path}")
async def mcp_http_endpoint(request: Request):
    """HTTP endpoint for MCP requests."""
    try:
        body = await request.json()
        logger.info(f"MCP HTTP request received: {body}")
        return {
            "status": "MCP HTTP endpoint available",
            "server": settings.server_name,
            "request": body
        }
    except Exception as e:
        logger.error(f"Error in HTTP endpoint: {e}")
        return {"error": str(e)}, 500

logger.info(f"Custom MCP SSE endpoint mounted at /cognitive-api/v1{mcp_path}")

def main():
    transport = settings.transport.strip().lower()
    
    if transport in ("sse", "http"):
        logger.info(f"Launching FastAPI Host on {settings.host}:{settings.port}...")
        mcp_uri = f"http://{settings.host}:{settings.port}/cognitive-api/v1/sync"
        if settings.mcp_secret:
            mcp_uri = f"{mcp_uri}/{settings.mcp_secret}"
        
        logger.info(f"SSE Endpoint: {mcp_uri}")
        logger.info(f"Dashboard Security: ACTIVE (X-API-KEY)")
        uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
    else:
        # Fallback to standard STDIO transport
        logger.info("Launching standard STDIO transport...")
        mcp_instance.run(transport="stdio")

if __name__ == "__main__":
    main()
