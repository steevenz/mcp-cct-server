import pytest
from src.engines.memory.manager import MemoryManager
from src.engines.orchestrator import CognitiveOrchestrator
from src.engines.sequential.engine import SequentialEngine
from src.modes.registry import CognitiveEngineRegistry

import sqlite3

class TestMemoryManager(MemoryManager):
    def __init__(self, *args, **kwargs):
        self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
        super().__init__(*args, **kwargs)
        
    def _get_connection(self):
        return self._shared_conn

@pytest.fixture
def memory_manager():
    """Provides a fresh, isolated in-memory SQLite MemoryManager for each test."""
    manager = TestMemoryManager(db_path=":memory:")
    yield manager
    manager._shared_conn.close()

@pytest.fixture
def sequential_engine(memory_manager):
    return SequentialEngine(memory_manager)

@pytest.fixture
def orchestrator(memory_manager, sequential_engine):
    """Provides a CognitiveOrchestrator injected with the mock in-memory manager."""
    registry = CognitiveEngineRegistry(memory_manager, sequential_engine)
    orchestrator = CognitiveOrchestrator(memory_manager, sequential_engine, registry)
    yield orchestrator
