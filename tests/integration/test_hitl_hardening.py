import unittest
import uuid
from src.engines.orchestrator import CognitiveOrchestrator
from src.core.models.enums import ThinkingStrategy, CCTProfile, SessionStatus
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.modes.registry import CognitiveEngineRegistry
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.engines.fusion.router import AutomaticPipelineRouter

class TestHITLHardening(unittest.TestCase):
    def setUp(self):
        self.memory = MemoryManager()
        self.sequential = SequentialEngine(self.memory)
        from src.analysis.scoring_engine import ScoringEngine
        self.scoring = ScoringEngine()
        self.fusion = FusionOrchestrator(self.memory, self.scoring, self.sequential)
        self.registry = CognitiveEngineRegistry(self.memory, self.sequential, self.fusion)
        self.router = AutomaticPipelineRouter(self.scoring)
        
        self.orchestrator = CognitiveOrchestrator(
            self.memory, self.sequential, self.registry, self.fusion, self.router
        )

    def test_hitl_execution_blockade(self):
        """Verify that a session in AWAITING_HUMAN_CLEARANCE is strictly blocked."""
        # 1. Start a session with HITL profile
        start_result = self.orchestrator.start_session(
            "Verify HITL blockade", profile="human_in_the_loop"
        )
        session_id = start_result["session_id"]
        
        # 2. Manually set state to AWAITING_HUMAN_CLEARANCE (simulating a Phase 7 stop)
        session = self.memory.get_session(session_id)
        session.status = SessionStatus.AWAITING_HUMAN_CLEARANCE
        self.memory.update_session(session)
        
        # 3. Attempt to execute a strategy
        result = self.orchestrator.execute_strategy(
            session_id, ThinkingStrategy.LINEAR, {"thought": "This should be blocked"}
        )
        
        # 4. Assert blocking
        self.assertFalse(result.get("allowed", True))
        self.assertEqual(result.get("status"), "awaiting_human_clearance")
        self.assertIn("Human clearance required", result.get("error", ""))

if __name__ == "__main__":
    unittest.main()
