from __future__ import annotations

import logging
import uuid
from typing import List, Dict, Any, Optional

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought, CCTSessionState
from src.engines.memory.manager import MemoryManager
from src.analysis.scoring_engine import ScoringEngine
from src.engines.sequential.engine import SequentialEngine

logger = logging.getLogger(__name__)

class FusionOrchestrator:
    """
    FusionOrchestrator: Convergent Cognitive Synthesis Service.
    
    This engine extracts insights from multiple divergent thoughts (e.g., persona nodes)
    and synthesizes them into a unified, high-density conclusion.
    
    Adheres to the 'Lego' Principle: Modular, reusable across different hybrid modes.
    """

    def __init__(
        self,
        memory: MemoryManager,
        scoring: ScoringEngine,
        sequential: SequentialEngine
    ):
        self.memory = memory
        self.scoring = scoring
        self.sequential = sequential

    def fuse_thoughts(
        self,
        session_id: str,
        thought_ids: List[str],
        synthesis_goal: str,
        model_id: str,
        model_tier: str = "efficiency"
    ) -> EnhancedThought:
        """
        Synthesizes multiple thoughts into one unified 'EnhancedThought'.
        
        Args:
            session_id: Active session identifier.
            thought_ids: List of thoughts to merge.
            synthesis_goal: The specific objective of the fusion.
            model_tier: Preference for LLM (economy/fast vs precision).
            
        Returns:
            A new synthesis EnhancedThought.
        """
        logger.info(f"Fusing {len(thought_ids)} thoughts in session {session_id} (Tier: {model_tier})")
        
        # 1. Retrieve subject thoughts
        thoughts = []
        for tid in thought_ids:
            t = self.memory.get_thought(tid)
            if t:
                thoughts.append(t)
        
        if not thoughts:
            raise ValueError("No valid thoughts found for fusion.")

        # 2. Context Construction (Convergent Data)
        source_context = "\n\n".join([
            f"--- Thought {t.id} ({t.strategy.value}) ---\n{t.content}" 
            for t in thoughts
        ])

        # 3. Prompt Synthesis (Simulated logic for synthesis)
        # In a real environment, this would call a cheap/fast LLM completion.
        # [LEGO] This part is designed to be copy-pasteable into an LLM bridge.
        fusion_prompt = (
            f"GOAL: {synthesis_goal}\n"
            f"Tier: {model_tier}\n"
            f"CONSTITUENT THOUGHTS:\n{source_context}\n\n"
            "INSTRUCTION: Synthesize the above perspectives into a single cohesive conclusion. "
            "Remove redundancies, resolve contradictions, and identify common patterns."
        )
        
        # [AUTOMATIC PIPELINE] Creating the synthesis thought
        session = self.memory.get_session(session_id)
        thought_number = session.current_thought_number + 1
        
        seq_context = self.sequential.process_sequence_step(
            session_id=session_id,
            llm_thought_number=thought_number,
            llm_estimated_total=session.estimated_total_thoughts,
            next_thought_needed=True,
            is_revision=True,
            revises_id=thought_ids[0] if thought_ids else None
        )

        # Build content (placeholder for actual LLM result)
        # In actual implementation, we'd wait for the LLM result here.
        fusion_content = f"[FUSION SYNTHESIS]\n{fusion_prompt}\n\n[RESULT]: Unified Cognitive Conclusion based on {len(thoughts)} inputs."

        fusion_thought = EnhancedThought(
            id=f"fusion_{uuid.uuid4().hex[:8]}",
            content=fusion_content,
            thought_type=ThoughtType.SYNTHESIS,
            strategy=ThinkingStrategy.INTEGRATIVE,
            parent_id=thought_ids[-1],
            builds_on=thought_ids,
            sequential_context=seq_context,
            tags=["fusion", "synthesis", model_tier]
        )

        # 4. Scoring Validation & Cost Analysis (Automatic Quality Gate)
        from src.core.constants import MAX_ANALYSIS_TOKEN_BUDGET
        metrics = self.scoring.analyze_thought(
            fusion_thought, 
            thoughts,
            token_budget=MAX_ANALYSIS_TOKEN_BUDGET,
            model_id=model_id
        )
        fusion_thought.metrics = metrics
        
        # 5. Persist
        self.memory.save_thought(session_id, fusion_thought)
        
        return fusion_thought

    def check_convergence(self, session_id: str, threshold: float = 0.85) -> bool:
        """
        Determines if the session's thinking path has converged sufficiently.
        """
        history = self.memory.get_session_history(session_id)
        if len(history) < 2:
            return False
            
        # Analysis based on recent thoughts scoring
        recent = history[-3:]
        avg_coherence = sum(t.metrics.logical_coherence for t in recent) / len(recent)
        
        return avg_coherence >= threshold
