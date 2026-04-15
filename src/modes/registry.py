import logging
from typing import Dict, Optional, Type, Any

from src.core.models.enums import ThinkingStrategy
from src.modes.base import BaseCognitiveEngine
from src.modes.primitives.orchestrator import DynamicPrimitiveEngine

# Import Hybrids
from src.modes.hybrids.critics.actor.orchestrator import ActorCriticEngine
from src.modes.hybrids.critics.council.orchestrator import CouncilOfCriticsEngine
from src.modes.hybrids.lateral.orchestrator import LateralEngine
from src.modes.hybrids.temporal.orchestrator import LongTermHorizonEngine
from src.modes.hybrids.multiagents.orchestrator import MultiAgentFusionEngine

from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.engines.fusion.orchestrator import FusionOrchestrator

# New Services
from src.core.services.orchestration.autonomous import AutonomousService
from src.core.services.llm.client import ClientService as ThoughtGenerationService
from src.core.services.llm.critic import CriticService as AdversarialReviewService
from src.core.services.guidance.guidance import GuidanceService
from src.core.services.user.identity import UserIdentityService as IdentityService
from src.core.services.analysis.scoring import ScoringService
from src.core.models.analysis import AnalysisConfig

logger = logging.getLogger(__name__)

class CognitiveEngineRegistry:
    """
    Central registry for mapping thinking strategies to cognitive engines.
    Uses the Dynamic Factory pattern for Primitives.
    """
    
    def __init__(
        self, 
        memory_manager: MemoryManager, 
        sequential_engine: SequentialEngine,
        fusion_orchestrator: FusionOrchestrator,
        autonomous: AutonomousService,
        thought_service: ThoughtGenerationService,
        guidance: GuidanceService,
        identity: IdentityService,
        scoring_engine: ScoringService,
        review_service: AdversarialReviewService = None
    ):
        self.memory = memory_manager
        self.sequential = sequential_engine
        self.fusion = fusion_orchestrator
        self.autonomous = autonomous
        self.thought_service = thought_service
        self.guidance = guidance
        self.identity = identity
        self.scoring = scoring_engine
        # If review_service not provided, create it with identity_service for Digital Twin
        from src.core.config import load_settings
        settings = load_settings()
        self.review_service = review_service or AdversarialReviewService(settings, identity_service=identity)
        self._engines: Dict[ThinkingStrategy, BaseCognitiveEngine] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        """Maps hybrids manually and the rest automatically to the factory."""
        
        # 1. Iterate All Strategies
        for strategy in ThinkingStrategy:
            # Special logic for Multi-Agent Fusion which needs the Fusion Engine
            if strategy == ThinkingStrategy.MULTI_AGENT_FUSION:
                self._engines[strategy] = MultiAgentFusionEngine(
                    self.memory, 
                    self.sequential, 
                    self.fusion,
                    self.autonomous,
                    self.thought_service,
                    self.guidance,
                    self.identity,
                    self.scoring
                )
                logger.info(f"Registry: Specialized Hybrid registered [{strategy.value}]")
                continue

            # Mapping for other Hybrids
            hybrid_mapping = {
                ThinkingStrategy.ACTOR_CRITIC_LOOP: ActorCriticEngine,
                ThinkingStrategy.COUNCIL_OF_CRITICS: CouncilOfCriticsEngine,
                ThinkingStrategy.UNCONVENTIONAL_PIVOT: LateralEngine,
                ThinkingStrategy.LONG_TERM_HORIZON: LongTermHorizonEngine,
            }

            if strategy in hybrid_mapping:
                # Initialize specific hybrids
                engine_class = hybrid_mapping[strategy]
                
                # [LEGO] Specialized injection for Hybrid modes that require LLM services
                if strategy == ThinkingStrategy.ACTOR_CRITIC_LOOP:
                    self._engines[strategy] = engine_class(
                        self.memory, 
                        self.sequential,
                        self.autonomous,
                        self.thought_service,
                        self.guidance,
                        self.identity,
                        self.scoring,
                        self.review_service  # Pass external review service for cross-model audit
                    )
                elif strategy == ThinkingStrategy.COUNCIL_OF_CRITICS:
                    self._engines[strategy] = engine_class(
                        self.memory, 
                        self.sequential,
                        self.autonomous,
                        self.thought_service,
                        self.guidance,
                        self.identity,
                        self.scoring,
                        self.review_service
                    )
                else:
                    self._engines[strategy] = engine_class(self.memory, self.sequential, self.identity, self.scoring)
                    
                logger.info(f"Registry: Specialized Hybrid registered [%s]", strategy.value)
            else:
                # Wrap all primitives into the Dynamic Engine
                self._engines[strategy] = DynamicPrimitiveEngine(
                    self.memory, self.sequential, self.identity, self.scoring, strategy
                )
                logger.debug(f"Registry: Adaptive Primitive registered [%s]", strategy.value)

        logger.info("Cognitive Engine Registry initialized with %d engines.", len(self._engines))

    def get_engine(self, strategy: ThinkingStrategy) -> Optional[BaseCognitiveEngine]:
        """Retrieves the cognitive engine based on the strategy."""
        return self._engines.get(strategy)
