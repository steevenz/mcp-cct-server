import logging
import sys
import os
import signal
import time
import asyncio
import json
import math
import secrets
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

# Ensure the project root is in sys.path for internal module resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status as http_status, Request, Header, Response
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from src.core.rate_limiter import get_rate_limiter
from contextlib import asynccontextmanager
import uuid
import uvicorn

# MCP Resources & Prompts
from src.resources.patterns import list_resources, read_resource
from src.prompts.thinking_prompts import list_prompts, get_prompt

# LLM Instance Store — memory-safe registry of connected LLMs
_llm_registry: Dict[str, Dict[str, Any]] = {}
_llm_registry_lock = threading.Lock()
_mcp_sessions: Dict[str, Dict[str, Any]] = {}  # Mcp-Session-Id → session data
_mcp_session_lock = threading.Lock()

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
from src.core.services.auth import AuthService

# API Layer / Tools
from src.tools.simplified import register_simplified_tools
from src.tools.session import register_session_tools
from src.tools.export import register_export_tools
from src.tools.engineering import register_engineering_tools, register_planning_tools
from src.tools.cognitive import register_cognitive_tools

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
    thought_service = ClientService(settings)  # online fallback

    # SmartLLMService: local Gemma first, online on quality boost
    try:
        from src.core.services.llm.smart import SmartLLMService
        thought_service = SmartLLMService(settings)
        logger.info("[BOOTSTRAP] Using SmartLLMService (local-first, online-boost)")
    except ImportError:
        logger.info("[BOOTSTRAP] SmartLLMService unavailable, using ClientService (online only)")

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
    auth_service = AuthService(
        db_path=settings.db_path,
        bootstrap_api_key=settings.bootstrap_api_key,
        auth_mode=settings.auth_mode,
        default_ttl_days=settings.auth_default_ttl_days,
        legacy_enabled=settings.auth_legacy_enabled,
    )

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
        "complexity_service": complexity_service,
        "auth_service": auth_service,
        "thought_service": thought_service,
        "review_service": review_service,
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

# Activate standalone planning tools (CoT/ToT/ReAct/ReWOO standalone interfaces)
try:
    register_planning_tools(mcp=mcp_instance, settings=settings)
    logger.info("Standalone planning tools registered: execute_react, execute_rewoo, execute_tot, execute_cot, compare_pattern_efficiency")
except Exception as e:
    logger.warning(f"Failed to register planning tools: {e}")

# ============================================================================
# FASTAPI WRAPPER (ELITE WINDOWS ENDPOINT)
# ============================================================================

app = FastAPI(
    title="CCT Cognitive OS API",
    description="Cognitive Computing Toolkit - MCP HTTP API Server",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.on_event("shutdown")
async def shutdown_event():
    thought_service = components.get("thought_service")
    if thought_service and hasattr(thought_service, "aclose"):
        await thought_service.aclose()

    review_service = components.get("review_service")
    if review_service and hasattr(review_service, "aclose"):
        await review_service.aclose()

# Security Definition
X_API_KEY = APIKeyHeader(name="X-API-KEY", auto_error=False)


def _request_id(request: Request) -> str:
    return (request.headers.get("X-Request-ID", "") or "").strip() or f"req_{secrets.token_hex(6)}"


def _client_ip(request: Request) -> str:
    forwarded = (request.headers.get("X-Forwarded-For", "") or "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return (request.client.host if request.client else "unknown") or "unknown"


def _llm_instance_id(request: Request) -> str:
    """Extract LLM instance/IDE origin from request headers for multi-LLM routing."""
    ide = (request.headers.get("X-IDE-ORIGIN", "") or "").strip()
    llm = (request.headers.get("X-LLM-INSTANCE-ID", "") or "").strip()
    if llm:
        return llm
    if ide:
        return f"ide:{ide}"
    host = request.client.host if request.client else "unknown"
    return f"remote:{host}"


def _enforce_tls_policy(request: Request) -> None:
    """Production requires TLS. Local/dev can warn based on settings."""
    scheme = (request.headers.get("X-Forwarded-Proto", "") or request.url.scheme or "").lower()
    secure = scheme == "https"
    is_prod = settings.env in {"prod", "production"}
    if is_prod and not secure:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="TLS is required in production")
    if not is_prod and not secure and settings.auth_tls_dev_warn_only:
        logger.warning("AUTH_TLS_WARNING: insecure http request in local/dev mode")


def _extract_presented_key(
    x_api_key: Optional[str],
    authorization: Optional[str],
) -> str:
    if authorization:
        value = authorization.strip()
        if value.lower().startswith("bearer "):
            token = value[7:].strip()
            if token:
                return token
    return (x_api_key or "").strip()


async def get_api_key(
    request: Request,
    api_key_header: Optional[str] = Depends(X_API_KEY),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    auth_service: AuthService = components["auth_service"]
    _enforce_tls_policy(request)
    presented_key = _extract_presented_key(api_key_header, authorization)
    result = auth_service.validate_api_key(
        presented_key,
        required_scope=None,
        request_id=_request_id(request),
        ip=_client_ip(request),
    )
    if not result.ok:
        code = 403 if result.code not in {404, 409, 410, 429} else result.code
        raise HTTPException(status_code=code, detail="Could not validate credentials")

    # Register LLM instance on successful auth
    principal = result.principal or {"auth_type": "unknown"}
    if principal.get("llm_instance_id"):
        llm_id = principal["llm_instance_id"]
        with _llm_registry_lock:
            _llm_registry[llm_id] = {
                "auth_type": principal.get("auth_type"),
                "scopes": principal.get("scopes", []),
                "first_seen": _llm_registry.get(llm_id, {}).get("first_seen", datetime.now().isoformat()),
                "last_active": datetime.now().isoformat(),
            }

    return principal


def require_scope(scope: str):
    async def _dep(
        request: Request,
        api_key_header: Optional[str] = Depends(X_API_KEY),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        auth_service: AuthService = components["auth_service"]
        _enforce_tls_policy(request)
        presented_key = _extract_presented_key(api_key_header, authorization)
        result = auth_service.validate_api_key(
            presented_key,
            required_scope=scope,
            request_id=_request_id(request),
            ip=_client_ip(request),
        )
        if not result.ok:
            if result.code == 429 and "rate_limited:" in result.message:
                retry = result.message.split("rate_limited:", 1)[1]
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. retry_after={retry}",
                )
            raise HTTPException(status_code=403, detail="Could not validate credentials")
        return result.principal or {}
    return _dep


PRD_ID = "20260509-mcp-spec-compliant"
ALLOWED_DATA_RESOURCES = {"all", "sessions", "thoughts", "thinking_patterns", "anti_patterns"}
SENSITIVE_KEYWORDS = ("token", "secret", "password", "api_key", "apikey", "authorization")
MCP_PROTOCOL_VERSION = "2025-11-25"

# MCP capability declaration — tells clients what this server supports
_MCP_CAPABILITIES = {
    "tools": {"listChanged": True},
    "resources": {"listChanged": True},
    "prompts": {"listChanged": True},
}


def _sanitize_pagination(page: int, page_size: int) -> tuple[int, int]:
    safe_page = page if page > 0 else 1
    safe_page_size = page_size if page_size > 0 else 25
    safe_page_size = min(safe_page_size, 200)
    return safe_page, safe_page_size


def _redact_sensitive(value: Any) -> Any:
    """Redacts sensitive fields from nested dictionaries/lists before API response."""
    if isinstance(value, dict):
        redacted: Dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if any(marker in lowered for marker in SENSITIVE_KEYWORDS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    return value


def _parse_json_blob(raw_blob: str) -> Any:
    try:
        return json.loads(raw_blob)
    except json.JSONDecodeError:
        return {"raw": raw_blob, "parse_error": True}


def _query_table_data(
    table_name: str,
    page: int,
    page_size: int,
    session_id: Optional[str] = None,
    llm_instance_id: Optional[str] = None
) -> Dict[str, Any]:
    """Reads paginated rows from the memory SQLite tables with optional filters."""
    orchestrator = components.get("orchestrator")
    memory_manager = getattr(orchestrator, "memory", None)
    if memory_manager is None:
        raise RuntimeError("Memory manager is not available")

    offset = (page - 1) * page_size
    where_parts: List[str] = []
    params: List[Any] = []
    count_params: List[Any] = []

    if table_name == "thoughts" and session_id:
        where_parts.append("session_id = ?")
        params.append(session_id)
        count_params.append(session_id)

    if table_name == "sessions" and llm_instance_id:
        where_parts.append("llm_instance_id = ?")
        params.append(llm_instance_id)
        count_params.append(llm_instance_id)

    where_clause = ""
    if where_parts:
        where_clause = " WHERE " + " AND ".join(where_parts)

    count_query = f"SELECT COUNT(*) FROM {table_name}{where_clause}"
    data_query = f"SELECT data FROM {table_name}{where_clause} ORDER BY rowid DESC LIMIT ? OFFSET ?"

    with memory_manager._get_connection() as conn:
        total_items = conn.execute(count_query, tuple(count_params)).fetchone()[0]
        params.extend([page_size, offset])
        rows = conn.execute(data_query, tuple(params)).fetchall()

    parsed_items = [_redact_sensitive(_parse_json_blob(row[0])) for row in rows]
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1

    return {
        "items": parsed_items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/cognitive-api/v1/auth/handshake/init")
async def auth_handshake_init(
    request: Request,
    payload: Dict[str, Any],
    bootstrap_key: Optional[str] = Header(default=None, alias="X-BOOTSTRAP-KEY"),
):
    _enforce_tls_policy(request)
    if settings.auth_mode == "legacy_only":
        raise HTTPException(status_code=403, detail="handshake flow is disabled in legacy_only mode")
    if not bootstrap_key or not secrets.compare_digest(bootstrap_key.strip(), settings.bootstrap_api_key):
        raise HTTPException(status_code=403, detail="Invalid bootstrap key")
    llm_instance_id = str(payload.get("llm_instance_id", "")).strip()
    client_nonce = str(payload.get("client_nonce", "")).strip()
    if not llm_instance_id or not client_nonce:
        raise HTTPException(status_code=400, detail="llm_instance_id and client_nonce are required")
    auth_service: AuthService = components["auth_service"]
    result = auth_service.handshake_init(
        llm_instance_id=llm_instance_id,
        client_nonce=client_nonce,
        request_id=_request_id(request),
        ip=_client_ip(request),
    )
    return {"status": "success", "data": result}


@app.post("/cognitive-api/v1/auth/handshake/complete")
async def auth_handshake_complete(
    request: Request,
    payload: Dict[str, Any],
    bootstrap_key: Optional[str] = Header(default=None, alias="X-BOOTSTRAP-KEY"),
):
    _enforce_tls_policy(request)
    if settings.auth_mode == "legacy_only":
        raise HTTPException(status_code=403, detail="handshake flow is disabled in legacy_only mode")
    auth_service: AuthService = components["auth_service"]
    handshake_id = str(payload.get("handshake_id", "")).strip()
    client_proof = str(payload.get("client_proof", "")).strip()
    if not handshake_id or not client_proof:
        raise HTTPException(status_code=400, detail="handshake_id and client_proof are required")
    result = auth_service.handshake_complete(
        handshake_id=handshake_id,
        client_proof=client_proof,
        bootstrap_key=(bootstrap_key or "").strip(),
        request_id=_request_id(request),
        ip=_client_ip(request),
    )
    if not result.ok:
        raise HTTPException(status_code=result.code, detail=result.message)
    return {"status": "success", "data": result.principal}


@app.post("/cognitive-api/v1/auth/keys/rotate")
async def auth_key_rotate(
    request: Request,
    principal: Dict[str, Any] = Depends(require_scope("auth:rotate")),
    api_key_header: Optional[str] = Depends(X_API_KEY),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    del principal
    auth_service: AuthService = components["auth_service"]
    presented = _extract_presented_key(api_key_header, authorization)
    result = auth_service.rotate_key(presented, request_id=_request_id(request), ip=_client_ip(request))
    if not result.ok:
        raise HTTPException(status_code=result.code, detail=result.message)
    return {"status": "success", "data": result.principal}


@app.post("/cognitive-api/v1/auth/keys/revoke")
async def auth_key_revoke(
    request: Request,
    payload: Dict[str, Any],
    principal: Dict[str, Any] = Depends(require_scope("admin:revoke")),
):
    del principal
    key_id = str(payload.get("key_id", "")).strip()
    reason_code = str(payload.get("reason_code", "manual")).strip() or "manual"
    if not key_id:
        raise HTTPException(status_code=400, detail="key_id is required")
    auth_service: AuthService = components["auth_service"]
    result = auth_service.revoke_key(
        key_id=key_id,
        request_id=_request_id(request),
        ip=_client_ip(request),
        reason_code=reason_code,
    )
    if not result.ok:
        raise HTTPException(status_code=result.code, detail=result.message)
    return {"status": "success", "data": result.principal}

@app.get("/status")
async def status(request: Request):
    uptime = time.time() - START_TIME

    llm_id = _llm_instance_id(request)

    try:
        memory_manager = components.get("orchestrator").memory
        usage_stats = memory_manager.get_aggregate_usage(llm_instance_id=llm_id)
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
            "total_sessions": usage_stats["session_count"],
            "llm_instance_id": usage_stats["llm_instance_id"],
        }
    except Exception as e:
        global_usage = {
            "tokens": {"input": 0, "output": 0, "total": 0},
            "costs": {"usd": 0.0, "idr": 0.0},
            "total_sessions": 0,
            "llm_instance_id": llm_id,
        }
        logger.warning(f"Status global usage unavailable: {type(e).__name__}")

    # LLM registry snapshot
    with _llm_registry_lock:
        connected_llms = dict(_llm_registry)

    return {
        "server": settings.server_name,
        "uptime_seconds": int(uptime),
        "llm_provider": settings.llm_provider or "GUIDED",
        "transport": settings.transport.upper(),
        "log_level": settings.log_level,
        "global_usage": global_usage,
        "connected_llms": connected_llms,
        "features": ["multi_ide", "hybrid_orchestration", "actor_critic", "memory_persistence", "financial_telemetry"]
    }


@app.get("/status/llms")
async def status_llms():
    """Return all connected LLM instances."""
    with _llm_registry_lock:
        return {"llms": dict(_llm_registry), "total": len(_llm_registry)}


@app.get("/status/llm/{llm_instance_id}")
async def status_llm_detail(llm_instance_id: str):
    """Return detailed status for a specific LLM instance."""
    with _llm_registry_lock:
        instance = _llm_registry.get(llm_instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"LLM instance '{llm_instance_id}' not found")

    try:
        memory_manager = components.get("orchestrator").memory
        usage = memory_manager.get_aggregate_usage(llm_instance_id=llm_instance_id)
        sessions = memory_manager.list_sessions(llm_instance_id=llm_instance_id, limit=10)
    except Exception as e:
        usage = {"error": str(e)}
        sessions = []

    return {
        "instance": instance,
        "usage": usage,
        "recent_sessions": sessions,
    }


from datetime import datetime, timedelta
from fastapi import Header

@app.get("/cognitive-api/v1/data")
async def get_all_data(
    request: Request,
    resource: str = "all",
    page: int = 1,
    page_size: int = 25,
    session_id: Optional[str] = None,
    api_key: str = Depends(get_api_key),
    x_forwarded_for: str = Header(None)
):
    """
    Secure data observability endpoint with pagination and resource filters.
    Supports multi-LLM scoping via X-IDE-ORIGIN or X-LLM-INSTANCE-ID headers.
    Query params:
      - resource: all|sessions|thoughts|thinking_patterns|anti_patterns
      - page: 1-based page index
      - page_size: max 200
      - session_id: optional filter for thoughts resource
    """
    del api_key  # consumed by Depends(get_api_key)
    llm_id = _llm_instance_id(request)
    requested_resource = resource.strip().lower()
    if requested_resource not in ALLOWED_DATA_RESOURCES:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource '{resource}'. Allowed: {sorted(ALLOWED_DATA_RESOURCES)}"
        )

    safe_page, safe_page_size = _sanitize_pagination(page, page_size)
    table_map = {
        "sessions": "sessions",
        "thoughts": "thoughts",
        "thinking_patterns": "thinking_patterns",
        "anti_patterns": "anti_patterns"
    }

    try:
        with open("database/config/allowed_tables.json") as f:
            allowed_tables = json.load(f).get("allowed_tables", [])

        if requested_resource == "all":
            data_payload = {}
            pagination_payload = {}
            for key, table_name in table_map.items():
                if table_name not in allowed_tables:
                    raise HTTPException(status_code=403, detail=f"Access to table '{table_name}' is not permitted")
                result = _query_table_data(
                    table_name=table_name,
                    page=safe_page,
                    page_size=safe_page_size,
                    session_id=session_id
                )
                data_payload[key] = result["items"]
                pagination_payload[key] = result["pagination"]
        else:
            table_name = table_map[requested_resource]
            if table_name not in allowed_tables:
                raise HTTPException(status_code=403, detail=f"Access to table '{table_name}' is not permitted")
            result = _query_table_data(
                table_name=table_name,
                page=safe_page,
                page_size=safe_page_size,
                session_id=session_id
            )
            data_payload = {requested_resource: result["items"]}
            pagination_payload = {requested_resource: result["pagination"]}

        # Rate limiting per LLM instance
        limiter = get_rate_limiter()
        client_key = llm_id or x_forwarded_for or "unknown"
        allowed, retry_after = limiter.is_allowed(client_key)

        if not allowed:
            headers = {
                "X-RateLimit-Limit": str(limiter.config.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int((time.time() + retry_after) * 1000))
            }
            raise HTTPException(status_code=429, detail="Too many requests", headers=headers)

        remaining = limiter.get_remaining(client_key)
        headers = {
            "X-RateLimit-Limit": str(limiter.config.max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int((time.time() + limiter.config.window_seconds) * 1000))
        }

        response_data = {
            "success": True,
            "data": data_payload,
            "meta": {
                "prd_id": PRD_ID,
                "resource": requested_resource,
                "filters": {"session_id": session_id, "llm_instance_id": llm_id},
                "pagination": pagination_payload,
                "generated_at": datetime.now().isoformat()
            },
            "error": None
        }
        return JSONResponse(content=response_data, headers=headers)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Configuration error - invalid table permissions") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to fetch aggregated data: {exc.__class__.__name__}")
        raise HTTPException(status_code=500, detail="Failed to process request") from exc

# MCP Mount Configuration
# Implement proper MCP JSON-RPC SSE endpoint for multi-AI architecture
from sse_starlette.sse import EventSourceResponse

mcp_path = "/sync"
if settings.mcp_secret:
    mcp_path = f"/sync/{settings.mcp_secret}"
    logger.info(f"Custom MCP Secret Path activated: {mcp_path}")

# Proper MCP SSE endpoint implementation
async def mcp_sse_handler(request: Request):
    """SSE endpoint for MCP stream transport.

    Keep the stream open and avoid emitting non-MCP payloads.
    JSON-RPC request/response remains on the HTTP POST endpoint.
    """
    async def event_generator():
        try:
            # Do not emit synthetic JSON payloads (init/heartbeat) because
            # MCP clients validate event data against JSON-RPC message schemas.
            while True:
                if await request.is_disconnected():
                    logger.info("MCP SSE connection closed by client")
                    return
                await asyncio.sleep(15)
                # Emit SSE comment frames only (not JSON data frames).
                # This preserves the stream without violating MCP JSON-RPC schema.
                yield {"comment": "keepalive"}
        except asyncio.CancelledError:
            logger.info("MCP SSE connection closed by client")
        except Exception as e:
            logger.error(f"Error in MCP SSE handler: {e}")

    return EventSourceResponse(event_generator(), ping=15)

# Mount SSE endpoint
@app.get(f"/cognitive-api/v1{mcp_path}")
async def mcp_sse_endpoint(request: Request, api_key: Dict[str, Any] = Depends(require_scope("mcp:sse"))):
    """SSE endpoint for MCP real-time communication."""
    del api_key
    return await mcp_sse_handler(request)

@app.post(f"/cognitive-api/v1{mcp_path}")
async def mcp_http_endpoint(request: Request, api_key: Dict[str, Any] = Depends(require_scope("mcp:sync"))):
    """HTTP endpoint for MCP JSON-RPC requests. Routes to per-LLM context."""
    del api_key

    # Extract LLM/IDE context from request
    request.state.llm_instance_id = _llm_instance_id(request)
    request.state.ide_origin = (request.headers.get("X-IDE-ORIGIN", "") or "").strip()

    # MCP Session Management (Streamable HTTP)
    mcp_session_id = (request.headers.get("Mcp-Session-Id", "") or "").strip()

    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="JSON body must be an object")

        rpc_id = body.get("id")
        method = str(body.get("method", "")).strip()
        params = body.get("params") or {}
        if not isinstance(params, dict):
            params = {}

        def rpc_ok(result: Dict[str, Any]) -> Dict[str, Any]:
            return {"jsonrpc": "2.0", "id": rpc_id, "result": result}

        def rpc_error(code: int, message: str) -> Dict[str, Any]:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": code, "message": message},
            }

        def build_initialize_payload(requested_protocol_value: Any) -> Dict[str, Any]:
            requested_protocol = requested_protocol_value
            protocol_version = (
                requested_protocol
                if isinstance(requested_protocol, str) and requested_protocol.strip()
                else MCP_PROTOCOL_VERSION
            )
            return {
                "protocolVersion": protocol_version,
                "serverInfo": {"name": settings.server_name, "version": "1.1.0"},
                "capabilities": _MCP_CAPABILITIES,
            }

        def normalize_wire_content(item: Any) -> Dict[str, Any]:
            if hasattr(item, "model_dump"):
                payload = item.model_dump(exclude_none=True)
            elif isinstance(item, dict):
                payload = item
            elif isinstance(item, str):
                payload = {"type": "text", "text": item}
            else:
                payload = {"type": "text", "text": json.dumps(item, ensure_ascii=False, default=str)}

            if not isinstance(payload, dict):
                return {"type": "text", "text": json.dumps(payload, ensure_ascii=False, default=str)}

            if "type" not in payload:
                if "text" in payload:
                    return {"type": "text", "text": str(payload.get("text", ""))}
                return {"type": "text", "text": json.dumps(payload, ensure_ascii=False, default=str)}

            content_type = payload.get("type")
            if not isinstance(content_type, str) or not content_type.strip():
                payload["type"] = "text"

            if payload.get("type") == "text" and "text" not in payload:
                payload["text"] = ""

            return payload

        def normalize_call_tool_result(raw: Any) -> tuple[list[Dict[str, Any]], bool]:
            is_error = False
            content: list[Any] = []
            extra_payload: Any = None

            if hasattr(raw, "content"):
                content = list(getattr(raw, "content", []) or [])
                is_error = bool(getattr(raw, "isError", False) or getattr(raw, "is_error", False))
            elif isinstance(raw, dict):
                content = list(raw.get("content") or [])
                is_error = bool(raw.get("isError") or raw.get("is_error") or False)
                extra_payload = raw.get("result") if "result" in raw else None
            elif isinstance(raw, (list, tuple)):
                if (
                    len(raw) == 2
                    and isinstance(raw[0], list)
                    and isinstance(raw[1], dict)
                ):
                    content = list(raw[0])
                    extra_payload = raw[1]
                else:
                    content = list(raw)
            else:
                content = [{"type": "text", "text": json.dumps(raw, ensure_ascii=False, default=str)}]

            def flatten(items: Any, out: list[Any]) -> None:
                if isinstance(items, (list, tuple)):
                    for sub in items:
                        flatten(sub, out)
                else:
                    out.append(items)

            flattened: list[Any] = []
            flatten(content, flattened)

            normalized = [normalize_wire_content(item) for item in flattened]

            if extra_payload is not None:
                normalized.append(
                    {
                        "type": "text",
                        "text": json.dumps(extra_payload, ensure_ascii=False, default=str),
                    }
                )

            return normalized, is_error

        # Compatibility mode for clients that send plain initialize payloads
        # without JSON-RPC envelope during streamable-http startup.
        if not method and isinstance(body.get("protocolVersion"), str):
            return build_initialize_payload(body.get("protocolVersion"))

        if method == "initialize":
            initialize_payload = build_initialize_payload(params.get("protocolVersion"))
            # Generate MCP session ID for Streamable HTTP compliance
            new_session_id = f"mcp_{secrets.token_hex(16)}"
            with _mcp_session_lock:
                _mcp_sessions[new_session_id] = {
                    "llm_instance_id": request.state.llm_instance_id,
                    "ide_origin": request.state.ide_origin,
                    "created_at": datetime.now().isoformat(),
                    "protocol_version": initialize_payload["protocolVersion"],
                }
            response = rpc_ok(initialize_payload) if rpc_id is not None else initialize_payload
            # Mcp-Session-Id must be returned as a header for Streamable HTTP
            return JSONResponse(content=response, headers={"Mcp-Session-Id": new_session_id})

        if method == "notifications/initialized":
            return rpc_ok({})

        if method == "ping":
            return rpc_ok({})

        # ====================================================================
        # MCP RESOURCES — expose cognitive patterns as browsable resources
        # ====================================================================
        if method == "resources/list":
            cursor = params.get("cursor", "")
            all_resources = list_resources(mcp_instance._memory_manager if hasattr(mcp_instance, "_memory_manager") else components.get("orchestrator").memory)
            page_size = 50
            start = 0
            if cursor:
                try:
                    start = int(cursor)
                except (ValueError, TypeError):
                    start = 0
            page = all_resources[start:start + page_size]
            next_cursor = str(start + page_size) if len(all_resources) > start + page_size else None
            resp = {"resources": page}
            if next_cursor:
                resp["nextCursor"] = next_cursor
            return rpc_ok(resp)

        if method == "resources/read":
            uri = params.get("uri", "")
            if not uri:
                return rpc_error(-32602, "Invalid params: missing uri")
            memory = components.get("orchestrator").memory
            content = read_resource(uri, memory)
            if not content:
                return rpc_error(-32002, f"Resource not found: {uri}")
            return rpc_ok({"contents": [content]})

        # ====================================================================
        # MCP PROMPTS — expose structured thinking templates
        # ====================================================================
        if method == "prompts/list":
            cursor = params.get("cursor", "")
            all_prompts = list_prompts()
            page_size = 20
            start = 0
            if cursor:
                try:
                    start = int(cursor)
                except (ValueError, TypeError):
                    start = 0
            page = all_prompts[start:start + page_size]
            next_cursor = str(start + page_size) if len(all_prompts) > start + page_size else None
            resp = {"prompts": page}
            if next_cursor:
                resp["nextCursor"] = next_cursor
            return rpc_ok(resp)

        if method == "prompts/get":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            if not name:
                return rpc_error(-32602, "Invalid params: missing prompt name")
            prompt = get_prompt(name, arguments)
            if not prompt:
                return rpc_error(-32602, f"Prompt not found: {name}")
            return rpc_ok(prompt)

        # ====================================================================
        # MCP TOOLS — list and call
        # ====================================================================
        if method == "tools/list":
            cursor = params.get("cursor", "")
            tools = await mcp_instance.list_tools()
            serialized = [
                tool.model_dump(exclude_none=True) if hasattr(tool, "model_dump") else dict(tool)
                for tool in tools
            ]
            page_size = 50
            start = 0
            if cursor:
                try:
                    start = int(cursor)
                except (ValueError, TypeError):
                    start = 0
            page = serialized[start:start + page_size]
            next_cursor = str(start + page_size) if len(serialized) > start + page_size else None
            resp = {"tools": page}
            if next_cursor:
                resp["nextCursor"] = next_cursor
            return rpc_ok(resp)

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
            if not tool_name:
                return rpc_error(-32602, "Invalid params: missing tool name")
            def map_tool_call(name: str, args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
                normalized = str(name)
                mapped_args: dict[str, Any] = dict(args or {})

                if normalized == "thinking":
                    return (
                        "start_thinking",
                        {
                            "problem_statement": mapped_args.get("problem_statement", ""),
                            "profile": mapped_args.get("profile", "balanced"),
                            "model_id": mapped_args.get("model_id") or mapped_args.get("llm_model_name") or "",
                            "estimated_thoughts": mapped_args.get("estimated_thoughts", 0),
                        },
                    )

                if normalized == "rethinking":
                    return (
                        "continue_thinking",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "thought_content": mapped_args.get("thought_content", ""),
                            "strategy": mapped_args.get("strategy", "auto"),
                            "thought_number": mapped_args.get("thought_number", 0),
                            "estimated_total_thoughts": mapped_args.get("estimated_total_thoughts", 0),
                            "thought_type": mapped_args.get("thought_type", "analysis"),
                            "is_revision": mapped_args.get("is_revision", False),
                            "revises_thought_id": mapped_args.get("revises_thought_id") or "",
                            "branch_from_id": mapped_args.get("branch_from_id") or "",
                            "branch_id": mapped_args.get("branch_id") or "",
                            "critic_persona": mapped_args.get("critic_persona", "auto"),
                        },
                    )

                if normalized == "list_thinking":
                    return (
                        "recall_thinking",
                        {
                            "limit": mapped_args.get("limit", 10),
                            "include_patterns": False,
                            "include_sessions": True,
                            "include_inferred_context": False,
                        },
                    )

                if normalized == "infer_current_context":
                    return (
                        "recall_thinking",
                        {
                            "query": mapped_args.get("problem_statement", "") or "",
                            "include_patterns": False,
                            "include_sessions": False,
                            "include_inferred_context": True,
                        },
                    )

                if normalized == "confirm_inferred_context":
                    return (
                        "log_thought",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "action": "confirm_context",
                            "persona": mapped_args.get("persona", "") or "",
                            "habit": mapped_args.get("habit", "") or "",
                            "behaviour": mapped_args.get("behaviour", "") or "",
                            "example": mapped_args.get("example", "") or "",
                        },
                    )

                if normalized == "branches":
                    return ("branch_thought", mapped_args)

                if normalized == "export_thinking_session":
                    return (
                        "export_thought",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "session_token": mapped_args.get("session_token", "") or "",
                            "action": "export",
                        },
                    )

                if normalized == "analyze_session":
                    return (
                        "export_thought",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "session_token": mapped_args.get("session_token", "") or "",
                            "action": "analyze",
                        },
                    )

                if normalized == "get_hitl_status":
                    return (
                        "export_thought",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "action": "hitl_status",
                        },
                    )

                if normalized == "grant_human_clearance":
                    return (
                        "export_thought",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "session_token": mapped_args.get("session_token", "") or "",
                            "action": "grant_clearance",
                            "authorized_by": mapped_args.get("authorized_by", "") or "",
                            "authorization_note": mapped_args.get("authorization_note", "") or "",
                        },
                    )

                if normalized == "start_cct_session":
                    return (
                        "start_thinking",
                        {
                            "problem_statement": mapped_args.get("problem_statement", ""),
                            "profile": mapped_args.get("profile", "balanced"),
                            "model_id": mapped_args.get("model_id", "") or "",
                        },
                    )

                if normalized == "list_cct_sessions":
                    return (
                        "recall_thinking",
                        {
                            "include_patterns": False,
                            "include_sessions": True,
                            "limit": 50,
                        },
                    )

                if normalized == "get_thinking_path":
                    return (
                        "export_thought",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "session_token": mapped_args.get("session_token", "") or "",
                            "action": "export",
                        },
                    )

                if normalized == "cct_think_step":
                    return (
                        "continue_thinking",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "thought_content": mapped_args.get("thought_content", ""),
                            "strategy": mapped_args.get("strategy", "auto"),
                            "thought_number": mapped_args.get("thought_number", 0),
                            "estimated_total_thoughts": mapped_args.get("estimated_total_thoughts", 0),
                            "thought_type": mapped_args.get("thought_type", "analysis"),
                            "is_revision": mapped_args.get("is_revision", False),
                            "revises_thought_id": mapped_args.get("revises_thought_id") or "",
                            "branch_from_id": mapped_args.get("branch_from_id") or "",
                            "branch_id": mapped_args.get("branch_id") or "",
                        },
                    )

                if normalized == "cct_log_failure":
                    return (
                        "log_thought",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "action": "failure",
                            "thought_id": mapped_args.get("thought_id", "") or "",
                            "category": mapped_args.get("category", "") or "",
                            "failure_reason": mapped_args.get("failure_reason", "") or "",
                            "corrective_action": mapped_args.get("corrective_action", "") or "",
                        },
                    )

                if normalized in {"decompose_task", "get_next_task", "update_task_status", "validate_decomposition", "get_decomposition_plan"}:
                    action_map = {
                        "decompose_task": "decompose",
                        "get_next_task": "next",
                        "update_task_status": "update",
                        "validate_decomposition": "validate",
                        "get_decomposition_plan": "plan",
                    }
                    return (
                        "decompose_thinking",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "action": action_map[normalized],
                            "task_description": mapped_args.get("task_description", "") or "",
                            "context": mapped_args.get("context") if isinstance(mapped_args.get("context"), dict) else {},
                            "unit_id": mapped_args.get("unit_id", "") or "",
                            "task_status": mapped_args.get("task_status", "") or mapped_args.get("status", "") or "",
                        },
                    )

                if normalized in {"define_eval_criteria", "check_eval_status", "validate_for_implementation"}:
                    action_map = {
                        "define_eval_criteria": "define",
                        "check_eval_status": "check",
                        "validate_for_implementation": "validate",
                    }
                    return (
                        "evaluate_thinking",
                        {
                            "session_id": mapped_args.get("session_id", ""),
                            "action": action_map[normalized],
                            "capability_evals": mapped_args.get("capability_evals") if isinstance(mapped_args.get("capability_evals"), list) else [],
                            "regression_evals": mapped_args.get("regression_evals") if isinstance(mapped_args.get("regression_evals"), list) else [],
                            "success_metrics": mapped_args.get("success_metrics") if isinstance(mapped_args.get("success_metrics"), list) else [],
                            "baseline_snapshot": mapped_args.get("baseline_snapshot", "") or "",
                        },
                    )

                if normalized in {"execute_cot", "execute_tot", "execute_react", "execute_rewoo", "compare_pattern_efficiency"}:
                    pattern_map = {
                        "execute_cot": "cot",
                        "execute_tot": "tot",
                        "execute_react": "react",
                        "execute_rewoo": "rewoo",
                        "compare_pattern_efficiency": "compare",
                    }
                    return (
                        "plan_thinking",
                        {
                            "pattern": pattern_map[normalized],
                            "problem": mapped_args.get("problem", "") or "",
                            "context": mapped_args.get("context") if isinstance(mapped_args.get("context"), dict) else {},
                            "available_actions": mapped_args.get("available_actions") if isinstance(mapped_args.get("available_actions"), list) else None,
                            "max_steps": mapped_args.get("max_steps", 10),
                            "max_depth": mapped_args.get("max_depth", 3),
                            "branch_factor": mapped_args.get("branch_factor", 3),
                        },
                    )

                if normalized == "health_check":
                    return ("health_thought", {"check": mapped_args.get("check", "all") or "all"})

                if normalized == "consolidate":
                    return ("consolidate_thinking", {"llm_instance_id": mapped_args.get("_llm_instance_id", "") or ""})

                if normalized == "reframe":
                    return ("reframe_problem", {
                        "problem_statement": mapped_args.get("problem_statement", ""),
                        "reframe_technique": mapped_args.get("reframe_technique", "invert"),
                        "session_id": mapped_args.get("session_id", ""),
                    })

                if normalized == "brainstorm":
                    return ("brainstorm_alternatives", {
                        "problem_statement": mapped_args.get("problem_statement", ""),
                        "count": mapped_args.get("count", 4),
                        "diversity": mapped_args.get("diversity", "high"),
                        "session_id": mapped_args.get("session_id", ""),
                    })

                if normalized == "review":
                    return ("review_thinking", {
                        "session_id": mapped_args.get("session_id", ""),
                        "action": mapped_args.get("action", "reflect"),
                    })

                return (normalized, mapped_args)

            mapped_name, mapped_arguments = map_tool_call(str(tool_name), arguments)
            # Inject LLM instance context into arguments for MemoryManager isolation
            if isinstance(mapped_arguments, dict):
                mapped_arguments.setdefault("_llm_instance_id", request.state.llm_instance_id)
                mapped_arguments.setdefault("_ide_origin", request.state.ide_origin)
            call_result = await mcp_instance.call_tool(mapped_name, mapped_arguments)
            normalized_content, is_error = normalize_call_tool_result(call_result)
            return rpc_ok({"content": normalized_content, "isError": is_error})

        return rpc_error(-32601, f"Method not found: {method}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in HTTP endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to process MCP HTTP request") from e

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
