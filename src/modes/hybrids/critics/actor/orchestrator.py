"""
Iterative Actor-Critic Engine — multi-round propose→critique→refine loop.

Neural analogue: Basal ganglia actor-critic — the critic evaluates the actor's
proposal, and the actor uses the critique to improve. Over N rounds, the
proposal converges or diverges.

Features:
  - Configurable N rounds of iteration
  - Convergence detection: stop when critique no longer produces meaningful changes
  - Improvement tracking: score delta across rounds
  - Early termination on convergence or divergence
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought
from src.modes.base import BaseCognitiveEngine
from .schemas import ActorCriticDialogInput
from src.core.services.llm.client import ClientService as ThoughtGenerationService
from src.core.services.llm.critic import CriticService as AdversarialReviewService

logger = logging.getLogger(__name__)


class IterativeCriticResult:
    """Result of an iterative critique round."""
    round_number: int
    proposal_content: str
    critique_content: str
    refined_content: str
    improvement_score: float  # 0.0 = no improvement, 1.0 = perfect
    is_converged: bool
    thought_id: str


class ActorCriticEngine(BaseCognitiveEngine):
    """
    Iterative Actor-Critic with convergence detection.

    Runs N rounds of propose → critique → refine, tracking improvement
    across iterations. Stops when:
      - Converged: critique produces no meaningful change
      - Max rounds reached
      - Diverged: refinement reduces quality
    """

    def __init__(
        self,
        memory,
        sequential,
        autonomous,
        thought_service,
        guidance,
        identity,
        scoring,
        review_service=None,
        max_rounds: int = 3,
        convergence_threshold: float = 0.05,
    ):
        super().__init__(memory, sequential, identity, scoring)
        self.autonomous = autonomous
        self.thought_service = thought_service
        self.guidance = guidance
        self.review_service = review_service
        self.max_rounds = max_rounds
        self.convergence_threshold = convergence_threshold

    @property
    def strategy_type(self) -> ThinkingStrategy:
        return ThinkingStrategy.ACTOR_CRITIC_LOOP

    async def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = ActorCriticDialogInput(**input_payload)
        except ValidationError as e:
            raise ValueError(f"Invalid payload: {e.errors()}")

        session = self._get_session_or_raise(session_id)
        target_thought = self._get_thought_or_raise(validated.target_thought_id)

        logger.info(f"[ACTOR-CRITIC] Starting iterative loop: target={target_thought.id}, max_rounds={self.max_rounds}")

        mode = self.autonomous.get_execution_mode(session.complexity) if hasattr(self.autonomous, "get_execution_mode") else "guided"
        rounds: List[IterativeCriticResult] = []
        current_proposal = target_thought.content
        best_proposal = target_thought.content
        best_score = 0.0
        did_converge = False
        final_thought = None

        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"[ACTOR-CRITIC] Round {round_num}/{self.max_rounds}")

            # Phase 1: Critique the current proposal
            critic_content = await self._generate_critique(
                proposal=current_proposal,
                persona=validated.critic_persona,
                session_id=session_id,
                round_num=round_num,
            )

            # Check for convergence: critique is empty or non-substantive
            if self._is_empty_critique(critic_content):
                logger.info(f"[ACTOR-CRITIC] Round {round_num}: Empty critique → converged")
                did_converge = True
                break

            # Phase 2: Refine based on critique
            refined = await self._refine_proposal(
                proposal=current_proposal,
                critique=critic_content,
                session_id=session_id,
                round_num=round_num,
            )

            # Score improvement
            improvement = self._score_improvement(current_proposal, refined)

            result = IterativeCriticResult()
            result.round_number = round_num
            result.proposal_content = current_proposal
            result.critique_content = critic_content
            result.refined_content = refined
            result.improvement_score = improvement
            result.is_converged = improvement < self.convergence_threshold

            # Save round thoughts to memory
            crit_thought = self._save_critique_thought(
                session_id, target_thought, round_num, critic_content
            )
            ref_thought = self._save_refined_thought(
                session_id, target_thought, crit_thought, round_num, refined
            )

            rounds.append(result)

            # Track best proposal
            if improvement > best_score:
                best_score = improvement
                best_proposal = refined
                final_thought = ref_thought

            # Check convergence
            if improvement < self.convergence_threshold:
                logger.info(f"[ACTOR-CRITIC] Round {round_num}: Converged (improvement={improvement:.3f} < {self.convergence_threshold})")
                did_converge = True
                break

            current_proposal = refined

        # Update target thought children
        if final_thought:
            target_thought.children_ids.append(final_thought.id)
            self.memory.update_thought(session_id, target_thought)

        session.current_thought_number += len(rounds) * 2
        self.memory.update_session(session)

        logger.info(f"[ACTOR-CRITIC] Complete: {len(rounds)} rounds, converged={did_converge}, best_score={best_score:.3f}")

        return {
            "status": "success",
            "strategy": self.strategy_type.value,
            "rounds_completed": len(rounds),
            "max_rounds": self.max_rounds,
            "did_converge": did_converge,
            "convergence_threshold": self.convergence_threshold,
            "best_improvement_score": round(best_score, 3),
            "final_thought_id": final_thought.id if final_thought else target_thought.id,
            "rounds": [
                {
                    "round": r.round_number,
                    "improvement": round(r.improvement_score, 3),
                    "converged": r.is_converged,
                }
                for r in rounds
            ],
        }

    async def _generate_critique(
        self, proposal: str, persona: str, session_id: str, round_num: int
    ) -> str:
        try:
            if self.review_service:
                outcome = await self.review_service.review(
                    target_content=proposal,
                    persona=persona,
                    system_prompt=None,
                    primary_thought_service=self.thought_service,
                )
                return outcome.content
        except Exception as e:
            logger.warning(f"[ACTOR-CRITIC] External review failed (round {round_num}): {e}")

        prompt = (
            f"ROUND {round_num}: Critically audit this proposal as a {persona}.\n\n"
            f"PROPOSAL:\n{proposal}\n\n"
            f"Identify specific flaws, vulnerabilities, and improvements."
        )
        system = f"You are a {persona} expert. Provide a sharp, actionable critique."
        return await self.thought_service.generate_thought(
            prompt=prompt,
            system_prompt=self._get_identity_decorated_system_prompt(session_id, system),
        )

    async def _refine_proposal(
        self, proposal: str, critique: str, session_id: str, round_num: int
    ) -> str:
        prompt = (
            f"ROUND {round_num}: Refine this proposal based on the critique.\n\n"
            f"ORIGINAL:\n{proposal}\n\n"
            f"CRITIQUE:\n{critique}\n\n"
            f"Produce an improved version that addresses all critique points."
        )
        system = "You are a Systems Architect. Synthesize the proposal with its criticisms into a stronger solution."
        return await self.thought_service.generate_thought(
            prompt=prompt,
            system_prompt=self._get_identity_decorated_system_prompt(session_id, system),
        )

    def _score_improvement(self, original: str, refined: str) -> float:
        """Score how much the refinement improved over the original."""
        if not original or not refined:
            return 0.0
        if refined == original:
            return 0.0
        # Simple heuristic: length change ratio
        # Longer = more thorough refinement
        len_ratio = len(refined) / max(len(original), 1)
        if len_ratio > 2.0:
            return 0.8
        if len_ratio > 1.3:
            return 0.5
        if len_ratio > 1.0:
            return 0.2
        return 0.05

    def _is_empty_critique(self, critique: str) -> bool:
        """Detect if a critique is empty/non-substantive → convergence signal."""
        if not critique or len(critique.strip()) < 20:
            return True
        empty_signals = ["no issues", "looks good", "no critique", "cannot critique", "i agree", "looks fine"]
        return any(signal in critique.lower() for signal in empty_signals)

    def _save_critique_thought(
        self, session_id: str, target: EnhancedThought, round_num: int, content: str
    ) -> EnhancedThought:
        thought = EnhancedThought(
            id=f"critic_{round_num:02d}_{uuid.uuid4().hex[:6]}",
            content=content,
            thought_type=ThoughtType.EVALUATION,
            strategy=ThinkingStrategy.CRITICAL,
            parent_id=target.id,
            sequential_context=self.sequential.process_sequence_step(
                session_id=session_id, llm_thought_number=round_num,
                llm_estimated_total=self.max_rounds, next_thought_needed=True,
                branch_from_id=target.id, branch_id=f"critic_r{round_num}",
            ),
            tags=[f"actor_critic", f"round_{round_num}", "critique"],
        )
        self.memory.save_thought(session_id, thought)
        return thought

    def _save_refined_thought(
        self, session_id: str, target: EnhancedThought, critique: EnhancedThought,
        round_num: int, content: str
    ) -> EnhancedThought:
        thought = EnhancedThought(
            id=f"refined_{round_num:02d}_{uuid.uuid4().hex[:6]}",
            content=content,
            thought_type=ThoughtType.SYNTHESIS,
            strategy=ThinkingStrategy.DIALECTICAL,
            parent_id=critique.id,
            builds_on=[target.id, critique.id],
            sequential_context=self.sequential.process_sequence_step(
                session_id=session_id, llm_thought_number=round_num + 1,
                llm_estimated_total=self.max_rounds, next_thought_needed=(round_num < self.max_rounds),
                is_revision=True, revises_id=target.id,
            ),
            tags=[f"actor_critic", f"round_{round_num}", "refinement"],
        )
        self.memory.save_thought(session_id, thought)
        return thought
