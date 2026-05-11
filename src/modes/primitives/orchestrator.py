"""
Dynamic Primitive Engine: Differentiated cognitive processing per strategy.

Each primitive strategy gets a distinct cognitive scaffold:
  - CoT → step-by-step decomposition
  - ToT → branching exploration 
  - ReAct → think-act-observe loop
  - ReWOO → plan-execute structure
  - Others → domain-specific frameworks
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from pydantic import ValidationError

from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought
from src.core.models.schemas import CCTThinkStepInput
from src.core.constants import DEFAULT_TP_THRESHOLD, MAX_ANALYSIS_TOKEN_BUDGET
from src.modes.base import BaseCognitiveEngine
from src.engines.memory.thinking_patterns import PatternArchiver

logger = logging.getLogger(__name__)


def _build_cot_scaffold(content: str) -> str:
    """Chain of Thought: step-by-step decomposition scaffold."""
    return (
        f"{content}\n\n"
        f"## Step-by-Step Reasoning\n"
        f"1. First principles: What do we know for certain?\n"
        f"2. Decomposition: What are the sub-problems?\n"
        f"3. Analysis: Work through each sub-problem\n"
        f"4. Synthesis: Combine findings\n"
        f"5. Conclusion: What is the answer?\n"
    )


def _build_tot_scaffold(content: str) -> str:
    """Tree of Thoughts: branching exploration scaffold."""
    return (
        f"{content}\n\n"
        f"## Branching Exploration\n"
        f"Path A (Conventional): The standard approach\n"
        f"  - Pros:\n  - Cons:\n  - Risks:\n"
        f"Path B (Alternative): A different angle\n"
        f"  - Pros:\n  - Cons:\n  - Risks:\n"
        f"Path C (Creative): An unconventional approach\n"
        f"  - Pros:\n  - Cons:\n  - Risks:\n"
        f"\nEvaluation: Which path scores highest on trade-offs?\n"
    )


def _build_react_scaffold(content: str) -> str:
    """ReAct: reason-act-observe loop scaffold."""
    return (
        f"{content}\n\n"
        f"## Think → Act → Observe\n"
        f"Thought: What is the current state and what needs to happen?\n"
        f"Action: What specific step should be taken?\n"
        f"  - Expected outcome:\n"
        f"  - Success criteria:\n"
        f"Observation: What was the actual result?\n"
        f"  - Did it work?\n"
        f"  - What changed?\n"
        f"Next Thought: Based on observation, what is the revised understanding?\n"
    )


def _build_rewoo_scaffold(content: str) -> str:
    """ReWOO: plan-execute scaffold."""
    return (
        f"{content}\n\n"
        f"## Plan → Execute\n"
        f"### Phase 1: Plan\n"
        f"Step 1:\n  - Action:\n  - Expected:\n"
        f"Step 2:\n  - Action:\n  - Expected:\n"
        f"Step 3:\n  - Action:\n  - Expected:\n"
        f"### Phase 2: Execute\n"
        f"Results:\n"
        f"  - Step 1 outcome:\n"
        f"  - Step 2 outcome:\n"
        f"  - Step 3 outcome:\n"
        f"### Final Assessment:\n"
    )


def _build_first_principles_scaffold(content: str) -> str:
    return (
        f"{content}\n\n"
        f"## First Principles Decomposition\n"
        f"1. What are the fundamental truths/axioms?\n"
        f"2. What assumptions are we making?\n"
        f"3. Strip away all assumptions. What remains?\n"
        f"4. Rebuild from first principles:\n"
        f"5. Compare rebuild with original approach\n"
    )


def _build_adversarial_scaffold(content: str) -> str:
    return (
        f"{content}\n\n"
        f"## Adversarial Simulation\n"
        f"Position: The proposed approach\n"
        f"Counter-position: What could go wrong?\n"
        f"  - Security vulnerability:\n"
        f"  - Performance bottleneck:\n"
        f"  - Scalability limit:\n"
        f"Rebuttal: How to address each counter-point\n"
        f"Final position: Strengthened approach\n"
    )


def _build_analogical_scaffold(content: str) -> str:
    return (
        f"{content}\n\n"
        f"## Analogical Transfer\n"
        f"Target domain: The current problem\n"
        f"Source domain: Known solution from another field\n"
        f"  - What is the analogous structure?\n"
        f"  - What maps directly?\n"
        f"  - What needs adaptation?\n"
        f"Transfer: Apply source solution to target problem\n"
    )


_STRATEGY_SCAFFOLDS = {
    ThinkingStrategy.CHAIN_OF_THOUGHT: _build_cot_scaffold,
    ThinkingStrategy.TREE_OF_THOUGHTS: _build_tot_scaffold,
    ThinkingStrategy.REACT: _build_react_scaffold,
    ThinkingStrategy.REWOO: _build_rewoo_scaffold,
    ThinkingStrategy.FIRST_PRINCIPLES: _build_first_principles_scaffold,
    ThinkingStrategy.ADVERSARIAL_SIMULATION: _build_adversarial_scaffold,
    ThinkingStrategy.ANALOGICAL_TRANSFER: _build_analogical_scaffold,
    ThinkingStrategy.DEDUCTIVE_VALIDATION: lambda c: c + "\n\n## Deductive Validation\nPremise:\nEvidence:\nConclusion:\nLogical validity:\n",
    ThinkingStrategy.ABDUCTIVE: lambda c: c + "\n\n## Abductive Reasoning\nObservation:\nBest explanation:\nAlternative explanations:\nWhy this one fits best:\n",
    ThinkingStrategy.COUNTERFACTUAL: lambda c: c + "\n\n## Counterfactual Analysis\nWhat if we did nothing?\nWhat if we did the opposite?\nWhat if constraints were removed?\nBest counterfactual insight:\n",
    ThinkingStrategy.SYNTHESIS: lambda c: c + "\n\n## Synthesis\nFindings from each perspective:\nCommon patterns:\nKey disagreements:\nIntegrated conclusion:\n",
    ThinkingStrategy.DIVERGENT: lambda c: c + "\n\n## Divergent Exploration\nIdea 1 (Safe):\nIdea 2 (Bold):\nIdea 3 (Wild):\nUnconventional insight:\n",
    ThinkingStrategy.CONVERGENT: lambda c: c + "\n\n## Convergent Selection\nCriteria:\nOption scores:\nBest option:\nRationale:\n",
    ThinkingStrategy.METACOGNITIVE: lambda c: c + "\n\n## Metacognitive Reflection\nWhat did I assume?\nWhat did I miss?\nHow confident am I?\nWhat would I change?\n",
    ThinkingStrategy.CRITICAL: lambda c: c + "\n\n## Critical Analysis\nClaim:\nEvidence for:\nEvidence against:\nGaps/Weaknesses:\nRevised claim:\n",
}


class DynamicPrimitiveEngine(BaseCognitiveEngine):
    """
    Differentiated primitive engine: each strategy provides a unique cognitive scaffold.

    Stage 1: Scaffold — inject strategy-specific thinking structure
    Stage 2: Validate — score and analyze thought quality
    Stage 3: Archive — promote elite thoughts to golden patterns
    Stage 4: Converge — detect early convergence
    """

    def __init__(self, memory_manager, sequential_engine, identity_service, scoring_engine, strategy: ThinkingStrategy):
        super().__init__(memory_manager, sequential_engine, identity_service, scoring_engine)
        self._dynamic_strategy = strategy
        self.archiver = PatternArchiver(memory_manager)

    @property
    def strategy_type(self) -> ThinkingStrategy:
        return self._dynamic_strategy

    async def execute(self, session_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated_input = CCTThinkStepInput(**input_payload)
        except ValidationError as e:
            raise ValueError(f"Invalid payload: {e.errors()}")

        session = self._get_session_or_raise(session_id)

        # Stage 1: Inject cognitive scaffold based on strategy
        scaffold_fn = _STRATEGY_SCAFFOLDS.get(self._dynamic_strategy)
        if scaffold_fn:
            scaffolded_content = scaffold_fn(validated_input.thought_content)
            logger.info(f"[PRIMITIVE] Applied {self._dynamic_strategy.value} scaffold to thought")
        else:
            scaffolded_content = validated_input.thought_content

        seq_context = self.sequential.process_sequence_step(
            session_id=session_id,
            llm_thought_number=validated_input.thought_number,
            llm_estimated_total=validated_input.estimated_total_thoughts,
            next_thought_needed=validated_input.next_thought_needed,
            is_revision=validated_input.is_revision,
            revises_id=validated_input.revises_thought_id,
            branch_from_id=validated_input.branch_from_id,
            branch_id=validated_input.branch_id,
        )

        determined_parent_id = validated_input.branch_from_id
        if not determined_parent_id and session.history_ids:
            determined_parent_id = session.history_ids[-1]

        prefix = self._dynamic_strategy.value[:3]
        thought = EnhancedThought(
            id=self._generate_thought_id(prefix),
            content=scaffolded_content,
            thought_type=validated_input.thought_type,
            strategy=self.strategy_type,
            parent_id=determined_parent_id,
            sequential_context=seq_context,
            tags=["primitive_step", self._dynamic_strategy.value],
        )

        # Stage 2: Scoring & Validation
        history = self.memory.get_session_history(session_id)
        thought.metrics = self.scoring.analyze_thought(thought, history, token_budget=MAX_ANALYSIS_TOKEN_BUDGET)
        thought.summary = self.scoring.generate_summary(thought.content)

        if validated_input.is_revision and validated_input.revises_thought_id:
            thought.contradicts.append(validated_input.revises_thought_id)
        elif thought.parent_id:
            thought.builds_on.append(thought.parent_id)

        self.memory.save_thought(session_id, thought)
        if thought.parent_id:
            parent = self.memory.get_thought(thought.parent_id)
            if parent:
                parent.children_ids.append(thought.id)
                self.memory.update_thought(session_id, parent)

        # Stage 3: Pattern archiving (LTP)
        pattern = self.archiver.process_thought(session, thought)

        # Stage 4: Convergence detection
        early_convergence = bool(
            pattern and thought.metrics and thought.metrics.logical_coherence > DEFAULT_TP_THRESHOLD
        )

        return {
            "status": "success",
            "orchestration_mode": self.strategy_type.value,
            "generated_thought_id": thought.id,
            "scaffold_applied": scaffold_fn is not None,
            "is_thinking_pattern": pattern is not None,
            "early_convergence_suggested": early_convergence,
            "current_step": seq_context.thought_number,
            "estimated_total": seq_context.estimated_total_thoughts,
            "metrics": {
                "clarity": thought.metrics.clarity_score if thought.metrics else 0,
                "coherence": thought.metrics.logical_coherence if thought.metrics else 0,
                "novelty": thought.metrics.novelty_score if thought.metrics else 0,
                "evidence": thought.metrics.evidence_strength if thought.metrics else 0,
            },
        }
