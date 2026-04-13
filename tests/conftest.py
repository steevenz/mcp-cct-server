import pytest
from src.engines.memory.manager import MemoryManager
from src.engines.orchestrator import CognitiveOrchestrator
from src.engines.sequential.engine import SequentialEngine
from src.modes.registry import CognitiveEngineRegistry
from src.analysis.scoring_engine import ScoringEngine
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.engines.fusion.router import AutomaticPipelineRouter
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
def scoring_engine():
    """Provides a ScoringEngine for analysis and metrics."""
    return ScoringEngine()

@pytest.fixture
def fusion_orchestrator(memory_manager, sequential_engine, scoring_engine):
    """Provides a FusionOrchestrator for multi-agent fusion."""
    return FusionOrchestrator(
        memory=memory_manager,
        scoring=scoring_engine,
        sequential=sequential_engine
    )

@pytest.fixture
def automatic_router(scoring_engine):
    """Provides an AutomaticPipelineRouter for dynamic pipeline selection."""
    return AutomaticPipelineRouter(scoring_engine=scoring_engine)

@pytest.fixture
def orchestrator(memory_manager, sequential_engine, fusion_orchestrator, automatic_router):
    """Provides a CognitiveOrchestrator with all components injected."""
    registry = CognitiveEngineRegistry(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        fusion_orchestrator=fusion_orchestrator
    )
    orchestrator = CognitiveOrchestrator(
        memory_manager=memory_manager,
        sequential_engine=sequential_engine,
        registry=registry,
        fusion_engine=fusion_orchestrator,
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
def temp_docs_root(tmp_path):
    """Provides a temporary directory for file-based operations."""
    return str(tmp_path / "test_docs")
