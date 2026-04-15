import pytest
from src.engines.memory.manager import MemoryManager
from src.engines.orchestrator import CognitiveOrchestrator
from src.engines.sequential.engine import SequentialEngine
from src.modes.registry import CognitiveEngineRegistry
from src.core.services.analysis.scoring import ScoringService
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.core.services.routing import IntelligenceRouter
from src.core.models.domain import EnhancedThought, CCTSessionState, ThoughtMetrics
from src.core.models.enums import ThoughtType, ThinkingStrategy, CCTProfile
from src.core.models.contexts import SequentialContext

import sqlite3

class TestMemoryManager(MemoryManager):
    def __init__(self, *args, **kwargs):
        self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
        super().__init__(*args, **kwargs)
        
    def _get_connection(self):
        return self._shared_conn
    
    def get_thinking_pattern(self, pattern_id):
        """Override to return None for tests that don't need pattern retrieval."""
        return None
    
    def clear_all(self):
        """Clear all data from the in-memory database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM thoughts")
        cursor.execute("DELETE FROM sessions")
        cursor.execute("DELETE FROM thinking_patterns")
        cursor.execute("DELETE FROM anti_patterns")
        conn.commit()

@pytest.fixture
def memory_manager():
    """Provides a fresh, isolated in-memory SQLite MemoryManager for each test."""
    manager = TestMemoryManager(db_path=":memory:")
    yield manager
    manager._shared_conn.close()

@pytest.fixture
def sequential_engine(memory_manager):
    """Provides a SequentialEngine with test memory manager."""
    return SequentialEngine(memory_manager)

@pytest.fixture
def scoring():
    """Provides a ScoringService for analysis and metrics."""
    return ScoringService()

@pytest.fixture
def fusion_orchestrator_base(memory_manager, sequential_engine, scoring):
    """Provides a properly initialized FusionOrchestrator with all required parameters."""
    from src.core.services.autonomous import AutonomousService
    from src.core.services.llm.client import ThoughtGenerationService
    from src.core.services.guidance import GuidanceService
    from src.core.services.identity import IdentityService
    from src.core.config import load_settings
    
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
    )

@pytest.fixture
def automatic_router(scoring):
    """Provides an IntelligenceRouter for dynamic pipeline selection."""
    return IntelligenceRouter(scoring=scoring)

@pytest.fixture
def full_registry(memory_manager, sequential_engine, fusion_orchestrator_base, scoring):
    """Provides a CognitiveEngineRegistry with all required services."""
    from src.core.services.autonomous import AutonomousService
    from src.core.services.llm.client import ThoughtGenerationService
    from src.core.services.guidance import GuidanceService
    from src.core.services.identity import IdentityService
    from src.core.config import load_settings
    
    settings = load_settings()
    autonomous = AutonomousService(settings, memory_manager)
    thought_service = ThoughtGenerationService(settings)
    guidance = GuidanceService()
    identity = IdentityService()
    
    return CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator_base,
        autonomous=autonomous,
        thought_service=thought_service,
        guidance=guidance,
        identity=identity,
        scoring=scoring
    )

@pytest.fixture
def orchestrator(memory_manager, sequential_engine, fusion_orchestrator_base, automatic_router, full_registry):
    """Provides a CognitiveOrchestrator with all components injected."""
    orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=full_registry,
        fusion_engine=fusion_orchestrator_base,
        router=automatic_router
    )
    yield orchestrator

@pytest.fixture
def sample_session(memory_manager):
    """Provides a sample CCT session for testing."""
    return memory_manager.create_session(
        problem_statement="Design a scalable microservices architecture",
        profile=CCTProfile.BALANCED,
        estimated_thoughts=10
    )

@pytest.fixture
def sample_thought(sample_session):
    """Provides a sample enhanced thought for testing."""
    return EnhancedThought(
        id="thought_1",
        session_id=sample_session.session_id,
        content="Implement event-driven architecture with message brokers for loose coupling",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=10),
        summary="Event-driven architecture pattern",
        metrics=ThoughtMetrics(
            logical_coherence=0.95,
            evidence_strength=0.85,
            clarity_score=0.9
        ),
        tags=["architecture", "scalability"]
    )

@pytest.fixture
def temp_docs_root():
    """Provides a temporary directory for file-based operations using designated temp folder."""
    # Use designated temp folder
    temp_base = Path("tests/verifications/temp")
    temp_base.mkdir(parents=True, exist_ok=True)
    temp_dir = temp_base / f"test_docs_{os.getpid()}"
    temp_dir.mkdir(exist_ok=True)
    yield str(temp_dir)
    # Cleanup
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

@pytest.fixture
def fusion_orchestrator(memory_manager, sequential_engine, scoring):
    """Provides a properly initialized FusionOrchestrator with all required parameters."""
    from src.core.services.autonomous import AutonomousService
    from src.core.services.llm.client import ThoughtGenerationService
    from src.core.services.guidance import GuidanceService
    from src.core.services.identity import IdentityService
    from src.core.config import load_settings
    
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
    )
