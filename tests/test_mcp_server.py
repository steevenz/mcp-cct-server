"""
MCP Server Test for Windsurf Compatibility
Tests the CCT MCP server with simplified tools.
"""
import sys
import os
import json
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import load_settings
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.core.services.analysis.scoring import ScoringService
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.modes.registry import CognitiveEngineRegistry
from src.engines.orchestrator import CognitiveOrchestrator
from src.tools.simplified import register_simplified_tools

# Mock FastMCP for testing
class MockFastMCP:
    def __init__(self, name):
        self.name = name
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

async def run_server_smoke():
    """Test the MCP server initialization and tool registration."""
    print("=" * 60)
    print("CCT MCP Server Test - Windsurf Compatibility")
    print("=" * 60)

    # 1. Load settings
    try:
        settings = load_settings()
        print(f"✅ Settings loaded: {settings.server_name}")
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return False

    # 2. Initialize core engines
    try:
        memory_manager = MemoryManager()
        sequential_engine = SequentialEngine(memory_manager)
        scoring = ScoringService()
        print("✅ Core engines initialized")
    except Exception as e:
        print(f"❌ Failed to initialize engines: {e}")
        return False

    # 3. Initialize fusion services
    try:
        fusion_orchestrator = FusionOrchestrator(
            memory=memory_manager,
            scoring=scoring,
            sequential=sequential_engine
        )
        automatic_router = AutomaticPipelineRouter(scoring=scoring)
        print("✅ Fusion services initialized")
    except Exception as e:
        print(f"❌ Failed to initialize fusion services: {e}")
        return False

    # 4. Initialize engine registry
    try:
        engine_registry = CognitiveEngineRegistry(
            memory_manager=memory_manager,
            sequential_engine=sequential_engine,
            fusion_orchestrator=fusion_orchestrator
        )
        print("✅ Engine registry initialized")
    except Exception as e:
        print(f"❌ Failed to initialize registry: {e}")
        return False

    # 5. Initialize master orchestrator
    try:
        master_orchestrator = CognitiveOrchestrator(
            memory_manager=memory_manager,
            sequential_engine=sequential_engine,
            registry=engine_registry,
            fusion_engine=fusion_orchestrator,
            router=automatic_router
        )
        print("✅ Master orchestrator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        return False

    # 6. Test tool registration
    try:
        mock_mcp = MockFastMCP("test-server")
        register_simplified_tools(
            mcp=mock_mcp,
            orchestrator=master_orchestrator,
            settings=settings
        )
        print(f"✅ Tools registered: {list(mock_mcp.tools.keys())}")
    except Exception as e:
        print(f"❌ Failed to register tools: {e}")
        return False

    # 7. Test session_start
    try:
        session_start = mock_mcp.tools.get('session_start')
        if session_start:
            result = await session_start(
                problem_statement="Design a simple API for user authentication",
                profile="balanced",
                model_id="test-model"
            )
            print(f"✅ session_start works: {result.get('detected_complexity', 'N/A')}")
            session_id = result.get('session_id')
        else:
            print("❌ session_start not found")
            return False
    except Exception as e:
        print(f"❌ session_start failed: {e}")
        return False

    # 8. Test session_think (if session created)
    if session_id:
        try:
            session_think = mock_mcp.tools.get('session_think')
            if session_think:
                result = await session_think(
                    session_id=session_id,
                    thought_content="Analyze the authentication requirements",
                    thought_number=1,
                    estimated_total_thoughts=3,
                    strategy="auto"
                )
                meta = result.get('_meta', {})
                print(f"✅ session_think works: strategy={meta.get('strategy_used', 'N/A')}, complexity={meta.get('complexity_level', 'N/A')}")
            else:
                print("❌ session_think not found")
        except Exception as e:
            print(f"❌ session_think failed: {e}")

    # 9. Test session_list
    try:
        session_list = mock_mcp.tools.get('session_list')
        if session_list:
            result = await session_list()
            print(f"✅ session_list works: {result.get('total', 0)} sessions")
        else:
            print("❌ session_list not found")
    except Exception as e:
        print(f"❌ session_list failed: {e}")

    print("=" * 60)
    print("MCP Server Test Complete - Ready for Windsurf!")
    print("=" * 60)
    return True


def test_mcp_http_tools_call_returns_flat_wirecontent(monkeypatch, tmp_path):
    monkeypatch.setenv("CCT_BOOTSTRAP_API_KEY", "test-bootstrap-key")
    monkeypatch.setenv("CCT_SERVER_NAME", "test-cct-mcp-server")
    monkeypatch.setenv("CCT_TRANSPORT", "sse")
    monkeypatch.setenv("CCT_HOST", "127.0.0.1")
    monkeypatch.setenv("CCT_PORT", "8019")
    monkeypatch.setenv("CCT_DB_PATH", str(tmp_path / "cct_test.db"))
    monkeypatch.setenv("CCT_IDENTITY_PATH", str(tmp_path / "identity"))
    monkeypatch.setenv("CCT_LLM_PROVIDER", "")

    import importlib

    if "src.main" in sys.modules:
        del sys.modules["src.main"]

    module = importlib.import_module("src.main")

    from fastapi.testclient import TestClient

    client = TestClient(module.app)
    headers = {"X-API-KEY": "test-bootstrap-key"}

    init_response = client.post(
        "/cognitive-api/v1/sync",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        },
    )
    assert init_response.status_code == 200
    init_payload = init_response.json()
    assert init_payload["result"]["protocolVersion"] == "2024-11-05"

    call_response = client.post(
        "/cognitive-api/v1/sync",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "recall_thinking", "arguments": {"include_patterns": False, "include_sessions": True}},
        },
    )
    assert call_response.status_code == 200
    payload = call_response.json()

    assert payload["jsonrpc"] == "2.0"
    assert payload["id"] == 2
    assert "result" in payload
    assert isinstance(payload["result"]["content"], list)
    assert isinstance(payload["result"]["isError"], bool)

    for item in payload["result"]["content"]:
        assert isinstance(item, dict)
        assert isinstance(item.get("type"), str)
        assert item["type"].strip()
        if item["type"] == "text":
            assert isinstance(item.get("text"), str)

    if "src.main" in sys.modules:
        del sys.modules["src.main"]


if __name__ == "__main__":
    success = asyncio.run(run_server_smoke())
    sys.exit(0 if success else 1)
