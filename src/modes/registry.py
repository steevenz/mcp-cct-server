import logging
from typing import Dict, Optional, Type, Any

from src.core.models.enums import ThinkingStrategy
from src.modes.base import BaseCognitiveEngine
from src.modes.primitives.orchestrator import DynamicPrimitiveEngine

# Import Hybrids
from src.modes.hybrids.actor_critic.orchestrator import ActorCriticEngine
from src.modes.hybrids.lateral.orchestrator import LateralEngine
from src.modes.hybrids.temporal.orchestrator import LongTermHorizonEngine
from src.modes.hybrids.multi_agent.orchestrator import MultiAgentFusionEngine

from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.engines.fusion.orchestrator import FusionOrchestrator

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
        fusion_orchestrator: FusionOrchestrator
    ):
        self.memory = memory_manager
        self.sequential = sequential_engine
        self.fusion = fusion_orchestrator
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
                    self.fusion
                )
                logger.info(f"Registry: Specialized Hybrid registered [{strategy.value}]")
                continue

            # Mapping for other Hybrids
            hybrid_mapping = {
                ThinkingStrategy.ACTOR_CRITIC_LOOP: ActorCriticEngine,
                ThinkingStrategy.UNCONVENTIONAL_PIVOT: LateralEngine,
                ThinkingStrategy.LONG_TERM_HORIZON: LongTermHorizonEngine,
            }

            if strategy in hybrid_mapping:
                # Initialize specific hybrids
                engine_class = hybrid_mapping[strategy]
                self._engines[strategy] = engine_class(self.memory, self.sequential)
                logger.info(f"Registry: Specialized Hybrid registered [%s]", strategy.value)
            else:
                # Wrap all primitives into the Dynamic Engine
                self._engines[strategy] = DynamicPrimitiveEngine(
                    self.memory, self.sequential, strategy
                )
                logger.debug(f"Registry: Adaptive Primitive registered [%s]", strategy.value)

        logger.info("Cognitive Engine Registry initialized with %d engines.", len(self._engines))

    def get_engine(self, strategy: ThinkingStrategy) -> Optional[BaseCognitiveEngine]:
        """Retrieves the cognitive engine based on the strategy."""
        return self._engines.get(strategy)