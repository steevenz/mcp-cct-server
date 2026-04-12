import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from src.core.models.enums import ThinkingStrategy, CCTProfile
from src.core.models.domain import AntiPattern, EnhancedThought
from src.modes.registry import CognitiveEngineRegistry
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.engines.fusion.router import AutomaticPipelineRouter

logger = logging.getLogger(__name__)

class CognitiveOrchestrator:
    """
    The Master Controller (Application Service) for the CCT system.
    Orchestrates the lifecycle of a cognitive task by coordinating the 
    Registry, Memory, Sequential, and Fusion engines.
    """

    def __init__(
        self, 
        memory_manager: MemoryManager, 
        sequential_engine: SequentialEngine, 
        registry: CognitiveEngineRegistry,
        fusion_engine: FusionOrchestrator,
        router: AutomaticPipelineRouter
    ):
        self.memory = memory_manager
        self.sequential = sequential_engine
        self.registry = registry
        self.fusion = fusion_engine
        self.router = router
        logger.info("Cognitive Orchestrator (with Fusion/Router) initialized.")

    def execute_strategy(
        self, 
        session_id: str, 
        strategy: ThinkingStrategy, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Routes the task to the appropriate engine and manages session context.
        """
        logger.info(f"Orchestrating strategy '{strategy.value}' for session '{session_id}'")

        # 1. Fetch the correct engine from the Registry
        engine = self.registry.get_engine(strategy)
        if not engine:
            error_msg = f"No engine found for strategy: {strategy.value}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # 2. Hand off execution to the specialized Engine
        try:
            result = engine.execute(session_id, payload)
            
            # 3. [AUTOMATIC PIPELINE] Adaptive Feedback Loop
            # After each step, we can check if a strategy pivot is necessary
            self.check_and_pivot(session_id)
            
            return result
        except Exception as e:
            logger.exception(f"Execution failed for strategy {strategy.value}")
            return {
                "status": "error", 
                "strategy": strategy.value,
                "message": str(e)
            }

    def start_session(self, problem_statement: str, profile: str = "balanced") -> Dict[str, Any]:
        """
        Entry point for starting a cognitive session.
        Initializes the state with an 'Automatic Pipeline' recommendation.
        """
        logger.info(f"Initializing new CCT session. Profile: {profile}")
        
        try:
            try:
                cct_profile = CCTProfile(profile.lower())
            except ValueError:
                cct_profile = CCTProfile.BALANCED
                logger.warning(f"Invalid profile {profile}, defaulting to balanced")
                
            # 1. DESIGN DYNAMIC PIPELINE (Adaptive Routing)
            suggested_pipeline = self.router.determine_initial_pipeline(problem_statement)
            
            # 2. INJECT HISTORICAL KNOWLEDGE (Self-Improvement)
            knowledge = self.memory.get_relevant_knowledge(problem_statement)
            
            # 3. INITIALIZE SESSION
            session = self.memory.create_session(
                problem_statement, 
                cct_profile, 
                estimated_thoughts=len(suggested_pipeline)
            )
            
            # 4. ENRICH SESSION STATE
            session.suggested_pipeline = suggested_pipeline
            injected_patterns = knowledge.get("thinking_patterns") or []
            injected_failures = knowledge.get("anti_patterns") or []
            session.knowledge_injection = {
                "golden_thinking_patterns": [p.model_dump(mode="json") for p in injected_patterns],
                "anti_patterns": [f.model_dump(mode="json") for f in injected_failures],
            }
            self.memory.update_session(session)
            
            return {
                "status": "success",
                "session_id": session.session_id,
                "session_token": session.session_token,
                "problem_statement": session.problem_statement,
                "profile": session.profile.value,
                "dynamic_pipeline": [s.value for s in suggested_pipeline],
                "injected_skills_count": len(injected_patterns),
                "injected_failures_count": len(injected_failures),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to start session: {str(e)}")
            return {"status": "error", "message": f"Session initialization failed: {str(e)}"}

    def check_and_pivot(self, session_id: str) -> None:
        """
        [ROUTER] Evaluation hook to see if the session needs a strategy pivot.
        """
        session = self.memory.get_session(session_id)
        if not session:
            return

        history = self.memory.get_session_history(session_id)
        if not history:
            return

        next_best_strat = self.router.next_strategy(session, history)
        
        # If the router suggests a strategy different from our next planned one, we log a 'Pivot suggestion'
        planned_index = session.current_thought_number
        if planned_index < len(session.suggested_pipeline):
            current_plan = session.suggested_pipeline[planned_index]
            if next_best_strat != current_plan:
                logger.warning(f"[ORCHESTRATOR] Automatic Pipeline recommending PIVOT from {current_plan.value} to {next_best_strat.value}")
                # In a fully autonomous mode, we would update session.suggested_pipeline here.
