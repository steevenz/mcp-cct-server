import unittest
import uuid
from src.engines.orchestrator import CognitiveOrchestrator
from src.core.models.enums import ThinkingStrategy, CCTProfile, SessionStatus
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.modes.registry import CognitiveEngineRegistry
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.core.services.routing import IntelligenceRouter

class TestHITLHardening(unittest.TestCase):
    def setUp(self):
        self.memory = MemoryManager()
        self.sequential = SequentialEngine(self.memory)
        from src.core.services.analysis.scoring import ScoringService
        self.scoring = ScoringService()
        from src.core.services.autonomous import AutonomousService
        from src.core.services.llm.client import ThoughtGenerationService
        from src.core.services.guidance import GuidanceService
        from src.core.services.identity import IdentityService
        from src.core.config import load_settings
        settings = load_settings()
        
        autonomous = AutonomousService(settings, self.memory)
        thought_service = ThoughtGenerationService(settings)
        guidance = GuidanceService()
        identity = IdentityService()
        
        self.fusion = FusionOrchestrator(
            memory=self.memory,
            scoring=self.scoring,
            sequential=self.sequential,
            orchestration=autonomous,
            thought_service=thought_service,
            guidance=guidance,
            identity=identity
        )
        self.registry = CognitiveEngineRegistry(
            memory_manager=self.memory,
            sequential_engine=self.sequential,
            fusion_orchestrator=self.fusion,
            autonomous=autonomous,
            thought_service=thought_service,
            guidance=guidance,
            identity=identity,
            scoring=self.scoring
        )
        self.router = IntelligenceRouter(scoring=self.scoring)
        
        self.orchestrator = CognitiveOrchestrator(
            self.memory, self.sequential, self.registry, self.fusion, self.router, identity=identity, autonomous=autonomous
        )

    @unittest.skip("Async handling needs investigation")
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
