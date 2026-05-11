"""
Simplified CCT Tools - Hybrid Orchestration System

Unified simplified CCT tool surface (Draft Concept #6):
- start_thinking
- continue_thinking
- recall_thinking
- decompose_thinking
- evaluate_thinking
- plan_thinking
- branch_thought
- export_thought
- log_thought
- health_thought
"""
from __future__ import annotations
from typing import Any, Dict, Optional, List, Tuple
import logging
import time
import sqlite3
import uuid
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP

from src.core.models.enums import ThinkingStrategy, ThoughtType, CCTProfile, SessionStatus
from src.core.models.domain import EnhancedThought
from src.core.validators import validate_session_id, validate_thought_content, validate_problem_statement
from src.core.rate_limiter import rate_limited
from src.core.rate_limiter import get_rate_limiter
from src.engines.orchestrator import CognitiveOrchestrator
from src.core.services.orchestration.policy import PolicyService as PipelineSelector
from src.core.services.analysis import ComplexityService
from src.core.models.analysis import TaskComplexity
from src.core.services.analysis.scoring import IncrementalSessionAnalyzer
from src.core.models.domain import SessionMetrics

logger = logging.getLogger(__name__)

def _parse_profile(profile: str) -> CCTProfile:
    normalized = (profile or "balanced").strip().lower()
    if normalized in {"creative", "creative_first"}:
        return CCTProfile.CREATIVE_FIRST
    if normalized in {"critical", "critical_first"}:
        return CCTProfile.CRITICAL_FIRST
    if normalized in {"human_in_the_loop", "hitl"}:
        return CCTProfile.HUMAN_IN_THE_LOOP
    if normalized in {"deep_recursive"}:
        return CCTProfile.DEEP_RECURSIVE
    if normalized in {"mimic_user", "mimic"}:
        return CCTProfile.MIMIC_USER
    return CCTProfile.BALANCED


def _parse_thought_type(thought_type: str) -> ThoughtType:
    normalized = (thought_type or "analysis").strip().lower()
    try:
        return ThoughtType(normalized)
    except ValueError:
        return ThoughtType.ANALYSIS


_STRATEGY_ALIASES: Dict[str, ThinkingStrategy] = {
    "auto": ThinkingStrategy.SYSTEMATIC,
    "chain_of_thought": ThinkingStrategy.CHAIN_OF_THOUGHT,
    "cot": ThinkingStrategy.CHAIN_OF_THOUGHT,
    "tree_of_thoughts": ThinkingStrategy.TREE_OF_THOUGHTS,
    "tot": ThinkingStrategy.TREE_OF_THOUGHTS,
    "react": ThinkingStrategy.REACT,
    "rewoo": ThinkingStrategy.REWOO,
    "actor_critic": ThinkingStrategy.ACTOR_CRITIC_LOOP,
    "actor_critic_loop": ThinkingStrategy.ACTOR_CRITIC_LOOP,
    "council_of_critics": ThinkingStrategy.COUNCIL_OF_CRITICS,
    "council": ThinkingStrategy.COUNCIL_OF_CRITICS,
    "lateral_pivot": ThinkingStrategy.UNCONVENTIONAL_PIVOT,
    "temporal_horizon": ThinkingStrategy.LONG_TERM_HORIZON,
}


def _map_strategy(strategy: str) -> Optional[ThinkingStrategy]:
    normalized = (strategy or "auto").strip().lower()
    if normalized == "auto":
        return None
    if normalized in _STRATEGY_ALIASES:
        return _STRATEGY_ALIASES[normalized]
    try:
        return ThinkingStrategy(normalized)
    except ValueError:
        return None


def _score_match(query: str, text: str) -> float:
    if not query:
        return 0.0
    q = query.lower().strip()
    t = (text or "").lower()
    if not t:
        return 0.0
    if q in t:
        return 1.0
    terms = [p for p in q.split() if p]
    if not terms:
        return 0.0
    hits = sum(1 for term in terms if term in t)
    return hits / max(len(terms), 1)


def register_simplified_tools(
    mcp: FastMCP,
    orchestrator: CognitiveOrchestrator,
    settings: Any,
    complexity_service: ComplexityService
):
    """
    Register simplified tools to MCP server.
    """
    pipeline_selector = PipelineSelector(complexity_service)

    @mcp.tool()
    @rate_limited(max_requests=10, window_seconds=60)
    async def start_thinking(
        problem_statement: str,
        profile: str = "balanced",
        model_id: str = "",
        estimated_thoughts: int = 0,
        project_name: str = "",
        topic: str = "",
        tags: Optional[List[str]] = None,
        persona: str = "",
        habit: str = "",
        behaviour: str = "",
    ) -> Dict[str, Any]:
        """
        START HERE: Initialize a structured thinking session. Use FIRST for any non-trivial problem.

        Creates session with automatic pipeline selection, golden pattern injection,
        anti-pattern warnings, and identity layer.

        Args:
            problem_statement: Core problem to think through (be specific)
            profile: 'balanced' (default), 'creative_first', 'critical_first', 'deep_recursive', 'human_in_the_loop', 'mimic_user'
            model_id: LLM model identifier (auto-detected if empty)
            estimated_thoughts: Rough step estimate (0 = auto)
            project_name: For grouping sessions
            topic: Category label
            tags: Categorization tags
            persona: Persona override
            habit: Habit pattern (mimic_user)
            behaviour: Behavioral pattern (mimic_user)

        Returns: session_id (for subsequent calls), session_token, profile, injected pattern counts
        """
        start_time = time.time()

        if error := validate_problem_statement(problem_statement):
            return {"status": "error", "error": error}

        profile_enum = _parse_profile(profile)
        complexity = complexity_service.detect_complexity(problem_statement)
        complexity_value = complexity.value if isinstance(complexity, TaskComplexity) else str(complexity)
        primary_category = PipelineSelector.detect_category(problem_statement)
        categories = PipelineSelector.detect_categories(problem_statement)

        try:
            pipeline = pipeline_selector.select_pipeline(problem_statement, complexity_value)

            session_result = orchestrator.start_session(
                problem_statement=problem_statement,
                profile=profile_enum.value,
                model_id=model_id or getattr(settings, "default_model", "") or "",
            )
            if session_result.get("status") != "success":
                return {"status": "error", "error": session_result.get("message") or "session_creation_failed"}

            session_id = str(session_result.get("session_id") or "")
            session = orchestrator.memory.get_session(session_id)
            if not session:
                return {"status": "error", "error": "session_not_found_after_creation"}

            if estimated_thoughts and estimated_thoughts > 0:
                session.estimated_total_thoughts = int(estimated_thoughts)

            session.complexity = complexity_value
            session.detected_categories = categories
            session.primary_category = primary_category
            session.suggested_pipeline = pipeline
            session.identity_layer = {
                **(session.identity_layer or {}),
                "project_name": project_name or None,
                "topic": topic or None,
                "tags": (tags or []) if tags is not None else [],
                "persona": persona or session.identity_layer.get("persona"),
                "habit": habit or session.identity_layer.get("habit"),
                "behaviour": behaviour or session.identity_layer.get("behaviour"),
            }

            if profile_enum == CCTProfile.MIMIC_USER:
                recall_snapshot = _internal_recall(
                    orchestrator=orchestrator,
                    query=problem_statement,
                    persona=persona,
                    habit=habit,
                    behaviour=behaviour,
                    project_name=project_name,
                    topic=topic,
                    tags=tags or [],
                    limit=5,
                    include_patterns=True,
                    include_sessions=True,
                    include_inferred_context=False,
                )
                session.knowledge_injection = {
                    **(session.knowledge_injection or {}),
                    "mimic_user_request": {
                        "persona": persona or None,
                        "habit": habit or None,
                        "behaviour": behaviour or None,
                        "project_name": project_name or None,
                        "topic": topic or None,
                        "tags": (tags or []) if tags is not None else [],
                    },
                    "mimic_user_recall": {
                        "patterns_count": len(recall_snapshot.get("patterns") or []),
                        "sessions_count": len(recall_snapshot.get("sessions") or []),
                    },
                }

            orchestrator.memory.update_session(session)
        except Exception as e:
            logger.error(f"start_thinking failed: {e}", exc_info=True)
            return {"status": "error", "error": "session_creation_failed"}

        first_strategy = pipeline[0] if pipeline else ThinkingStrategy.EMPIRICAL_RESEARCH

        try:
            payload = {
                "thought_content": problem_statement,
                "thought_type": ThoughtType.ANALYSIS,
                "strategy": first_strategy,
                "thought_number": 1,
                "estimated_total_thoughts": session.estimated_total_thoughts,
                "next_thought_needed": session.estimated_total_thoughts > 1
            }

            thought_result = await orchestrator.execute_strategy(session_id, first_strategy, payload)

            total_time = time.time() - start_time
            return {
                "status": "success",
                "session_id": session_id,
                "session_token": session.session_token,
                "complexity": complexity_value,
                "pipeline": [s.value for s in pipeline],
                "injected_patterns_count": int(session.knowledge_injection.get("injected_patterns_count", 0) or 0),
                "first_thought": thought_result,
                "processing_time": round(total_time, 4),
            }

        except Exception as e:
            logger.error(f"start_thinking first step failed: {e}", exc_info=True)
            return {"status": "partial_success", "session_id": session_id, "session_token": session.session_token}


    # Helper for reframe_problem / brainstorm_alternatives to create quick sequential context
    def _quick_seq(sid: str) -> Any:
        try:
            from src.core.models.contexts import SequentialContext
            session = orchestrator.memory.get_session(sid)
            num = (session.current_thought_number + 1) if session else 1
            return SequentialContext(thought_number=num, estimated_total_thoughts=num + 5, next_thought_needed=True)
        except Exception:
            from src.core.models.contexts import SequentialContext
            return SequentialContext(thought_number=1, estimated_total_thoughts=5, next_thought_needed=True)

    @mcp.tool()
    @rate_limited(max_requests=30, window_seconds=60)
    async def reframe_problem(
        problem_statement: str,
        reframe_technique: str = "invert",
        session_id: str = "",
    ) -> Dict[str, Any]:
        """
        FRAME: Reframe a problem to escape fixed thinking and discover new angles. Use when stuck or exploring.

        Cognitive technique: reframing changes the way a problem is perceived without changing its essence.
        Techniques:
        - 'invert': Ask "How could I achieve the OPPOSITE of my goal?" (default)
        - 'assumption_reversal': List assumptions, then reverse each one
        - 'expand': Zoom out to see the bigger system context
        - 'constrain': Zoom in to find the core constraint
        - 'analogy': Compare to a completely different domain

        Args:
            problem_statement: The current problem statement to reframe
            reframe_technique: Technique: 'invert', 'assumption_reversal', 'expand', 'constrain', 'analogy'
            session_id: Optional session to attach this reframe as a thought step

        Returns:
            Dict with original problem, reframed versions (one per technique aspect), and insights
        """
        original = problem_statement.strip()
        if not original:
            return {"status": "error", "error": "problem_statement_required"}

        results = {"original": original}

        if reframe_technique == "invert":
            results["reframes"] = [
                {"frame": f"How do we achieve the opposite of: {original}?", "technique": "inversion"},
                {"frame": f"What would make this problem worse?", "technique": "reverse_goal"},
                {"frame": f"If we couldn't use any existing solutions, how would we solve it?", "technique": "tabula_rasa"},
            ]
        elif reframe_technique == "assumption_reversal":
            results["reframes"] = [
                {"frame": f"List 5 assumptions in '{original}', then reverse each", "technique": "assumption_reversal"},
                {"frame": f"What if the opposite of each assumption is true?", "technique": "assumption_test"},
            ]
        elif reframe_technique == "expand":
            results["reframes"] = [
                {"frame": f"What is the larger system that contains this problem?", "technique": "zoom_out"},
                {"frame": f"Who else is affected by this problem?", "technique": "stakeholder_expand"},
                {"frame": f"How does this problem look in 5 years?", "technique": "temporal_expand"},
            ]
        elif reframe_technique == "constrain":
            results["reframes"] = [
                {"frame": f"What is the SINGLE core constraint that makes this hard?", "technique": "core_constraint"},
                {"frame": f"If we had unlimited budget/time, what would change?", "technique": "remove_resource_constraint"},
            ]
        elif reframe_technique == "analogy":
            results["reframes"] = [
                {"frame": f"How would nature solve this problem?", "technique": "biomimicry"},
                {"frame": f"How would a completely different industry solve this?", "technique": "cross_domain"},
                {"frame": f"How did we solve a similar problem before?", "technique": "historical_analogy"},
            ]

        results["insight"] = "Choose one reframe above and use continue_thinking to explore it with CoT or ToT scaffold."

        # Optionally save to session
        if session_id:
            try:
                from src.core.models.enums import ThoughtType
                thought = orchestrator.memory.get_session(session_id)
                if thought:
                    reframe_content = "\n\n".join([f"Reframe ({r['technique']}): {r['frame']}" for r in results.get("reframes", [])])
                    combined = f"Original: {original}\n\nReframing Technique: {reframe_technique}\n\n{reframe_content}"
                    orchestrator.memory.save_thought(session_id, EnhancedThought(
                        id=f"reframe_{uuid.uuid4().hex[:6]}",
                        content=combined,
                        thought_type=ThoughtType.METACOGNITION,
                        strategy=ThinkingStrategy.METACOGNITIVE,
                        parent_id=None,
                        sequential_context=_quick_seq(session_id),
                        tags=["reframe_problem", reframe_technique],
                    ))
                    results["saved_to_session"] = session_id
            except Exception as e:
                logger.warning(f"Failed to save reframe to session: {e}")

        return {"status": "success", **results}

    @mcp.tool()
    @rate_limited(max_requests=30, window_seconds=60)
    async def brainstorm_alternatives(
        problem_statement: str,
        count: int = 4,
        diversity: str = "high",
        session_id: str = "",
    ) -> Dict[str, Any]:
        """
        DIVERGE: Generate diverse alternative approaches. Use after reframe_problem to explore the solution space.

        Forces cognitive diversity by generating approaches from different angles:
        - Conventional (baseline)
        - Opposite (invert assumptions)
        - Cross-domain (analogy from different field)
        - Constraint-violating (break the rules)

        Args:
            problem_statement: The problem to brainstorm alternatives for
            count: Number of alternatives to generate (2-6, default 4)
            diversity: 'high' (default) forces very different approaches; 'medium' allows related ones
            session_id: Optional session to attach alternatives as ToT branches

        Returns:
            Dict with alternatives array (each with title, description, pros, cons, risk_level)
        """
        if not problem_statement.strip():
            return {"status": "error", "error": "problem_statement_required"}
        count = max(2, min(count or 4, 6))

        alternatives = [
            {
                "title": "Conventional Approach",
                "description": f"Standard solution for: {problem_statement}",
                "technique": "baseline",
                "pros": ["Proven patterns", "Team familiarity", "Predictable outcomes"],
                "cons": ["May miss opportunities", "Competitive disadvantage"],
                "risk_level": "low",
            },
            {
                "title": "Inverse Approach",
                "description": f"Do the opposite of conventional wisdom for: {problem_statement}",
                "technique": "inversion",
                "pros": ["Unique positioning", "Potential breakthrough"],
                "cons": ["Unproven", "Higher uncertainty"],
                "risk_level": "high",
            },
            {
                "title": "Cross-Domain Analogy",
                "description": f"Solve {problem_statement} using patterns from a different field",
                "technique": "analogy",
                "pros": ["Novel insights", "Creative leap"],
                "cons": ["May not translate directly", "Harder to validate"],
                "risk_level": "medium",
            },
            {
                "title": "Constraint-Violating",
                "description": f"What if we removed the biggest constraint from: {problem_statement}",
                "technique": "constraint_release",
                "pros": ["Breakthrough potential", "Questions assumptions"],
                "cons": ["May be impractical", "Requires paradigm shift"],
                "risk_level": "high",
            },
            {
                "title": "Minimum Viable",
                "description": f"The simplest possible solution to: {problem_statement}",
                "technique": "minimalist",
                "pros": ["Fast to implement", "Easy to iterate"],
                "cons": ["May not fully solve", "Scope creep risk"],
                "risk_level": "low",
            },
            {
                "title": "Future-Back",
                "description": f"Assume {problem_statement} is solved in 5 years. How did we get there?",
                "technique": "future_back",
                "pros": ["Long-term thinking", "Avoids short-term bias"],
                "cons": ["Speculative", "Hard to execute immediately"],
                "risk_level": "medium",
            },
        ]

        selected = alternatives[:count]
        if diversity == "high" and count >= 3:
            selected = [alternatives[0], alternatives[1], alternatives[3], alternatives[5]][:count]

        result = {
            "status": "success",
            "alternatives": selected,
            "count": len(selected),
            "diversity": diversity,
            "recommendation": "Use continue_thinking(strategy='tree_of_thoughts') to explore each alternative as a branch, then branch_thought(action='compare') to evaluate.",
        }

        # Save as ToT branches if session provided
        if session_id:
            try:
                session = orchestrator.memory.get_session(session_id)
                if session:
                    parent_id = session.history_ids[-1] if session.history_ids else None
                    for i, alt in enumerate(selected):
                        orchestrator.memory.save_thought(session_id, EnhancedThought(
                            id=f"alt_{i}_{uuid.uuid4().hex[:4]}",
                            content=f"Alternative {i+1}: {alt['title']}\n\n{alt['description']}",
                            thought_type=ThoughtType.HYPOTHESIS,
                            strategy=ThinkingStrategy.DIVERGENT,
                            parent_id=parent_id,
                            sequential_context=_quick_seq(session_id),
                            tags=["brainstorm_alternative", alt["technique"], f"risk_{alt['risk_level']}"],
                        ))
                    result["saved_to_session"] = session_id
            except Exception as e:
                logger.warning(f"Failed to save alternatives: {e}")

        return result

    @mcp.tool()
    @rate_limited(max_requests=60, window_seconds=60)
    async def continue_thinking(
        session_id: str,
        thought_content: str,
        strategy: str = "auto",
        thought_number: int = 0,
        estimated_total_thoughts: int = 0,
        thought_type: str = "analysis",
        is_revision: bool = False,
        revises_thought_id: str = "",
        branch_from_id: str = "",
        branch_id: str = "",
        critic_persona: str = "auto",
        specialized_personas: Optional[List[str]] = None,
        provocation_method: str = "REVERSE_ASSUMPTION",
        projection_scale: str = "LONG_TERM",
    ) -> Dict[str, Any]:
        """
        NEXT STEP: Add a reasoning step to an existing session. Use after start_thinking.

        Auto-selects best strategy unless specified. Supports chains (CoT), trees (ToT), 
        agent loops (ReAct), plans (ReWOO), stress-tests (actor_critic), multi-audit (council).

        Args:
            session_id: From start_thinking response
            thought_content: Your reasoning or analysis for this step
            strategy: 'auto' (default), 'chain_of_thought', 'tree_of_thoughts', 'react', 'rewoo', 'actor_critic', 'council_of_critics', 'lateral_pivot', 'temporal_horizon'
            thought_number: Current step (0 = auto)
            estimated_total_thoughts: Total steps estimate (0 = session default)
            thought_type: 'analysis', 'synthesis', 'evaluation', 'conclusion', 'plan', 'question', 'hypothesis', 'metacognition', 'implementation', 'review', 'root_cause'
            is_revision: True if revising a flawed thought
            revises_thought_id: Required if is_revision=True
            branch_from_id: Parent thought ID for branching
            branch_id: Branch name (e.g. 'alternative_approach')
            critic_persona: For actor_critic: 'Security Expert', 'Performance Engineer', 'Principal Architect'
            specialized_personas: For council: ['Security Expert', 'UX Designer', 'DB Architect']
            provocation_method: For lateral_pivot: 'REVERSE_ASSUMPTION', 'EXAGGERATION', 'DISTORTION'
            projection_scale: For temporal: 'SHORT_TERM', 'MID_TERM', 'LONG_TERM'

        Returns: status, thought_id, strategy used, metrics (clarity/coherence/evidence), convergence status
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "error": error}

        if error := validate_thought_content(thought_content):
            return {"status": "error", "error": error}

        session = orchestrator.memory.get_session(session_id)
        if not session:
            return {"status": "error", "error": "session_not_found"}

        history = orchestrator.memory.get_session_history(session_id)
        selected_strategy = _map_strategy(strategy)
        if selected_strategy is None:
            selected_strategy = orchestrator.router.next_strategy(session, history)

        resolved_thought_number = int(thought_number) if thought_number and thought_number > 0 else (len(history) + 1)
        resolved_total = (
            int(estimated_total_thoughts)
            if estimated_total_thoughts and estimated_total_thoughts > 0
            else int(session.estimated_total_thoughts)
        )
        next_needed = resolved_thought_number < resolved_total

        payload = {
            "thought_content": thought_content,
            "thought_type": _parse_thought_type(thought_type),
            "strategy": selected_strategy,
            "thought_number": resolved_thought_number,
            "estimated_total_thoughts": resolved_total,
            "next_thought_needed": next_needed,
            "is_revision": bool(is_revision),
        }

        if revises_thought_id:
            payload["revises_thought_id"] = revises_thought_id
        if branch_from_id:
            payload["branch_from_id"] = branch_from_id
        if branch_id:
            payload["branch_id"] = branch_id

        target_thought_id = history[-1].id if history else ""
        if selected_strategy in {ThinkingStrategy.ACTOR_CRITIC_LOOP, ThinkingStrategy.COUNCIL_OF_CRITICS, ThinkingStrategy.LONG_TERM_HORIZON}:
            if not target_thought_id:
                return {"status": "error", "error": "no_target_thought"}

        if selected_strategy == ThinkingStrategy.ACTOR_CRITIC_LOOP:
            payload["target_thought_id"] = target_thought_id
            if critic_persona and critic_persona != "auto":
                payload["critic_persona"] = critic_persona
            else:
                category = getattr(session, "primary_category", "GENERIC")
                payload["critic_persona"] = PipelineSelector.DOMAIN_PERSONAS.get(category, "Critical Reviewer")

        if selected_strategy == ThinkingStrategy.COUNCIL_OF_CRITICS:
            payload["target_thought_id"] = target_thought_id
            if specialized_personas:
                payload["personas"] = specialized_personas
            else:
                detected = getattr(session, "detected_categories", {}) or {}
                payload["personas"] = PipelineSelector.get_personas_for_domains(detected) if detected else ["Critical Reviewer"]

        if selected_strategy == ThinkingStrategy.UNCONVENTIONAL_PIVOT:
            payload = {
                "current_paradigm": thought_content,
                "provocation_method": provocation_method,
            }

        if selected_strategy == ThinkingStrategy.LONG_TERM_HORIZON:
            payload["target_thought_id"] = target_thought_id
            payload["projection_scale"] = projection_scale

        if selected_strategy == ThinkingStrategy.MULTI_AGENT_FUSION:
            payload["target_thought_id"] = target_thought_id
            detected = getattr(session, "detected_categories", {}) or {}
            payload["personas"] = PipelineSelector.get_personas_for_domains(detected) if detected else ["Critical Reviewer"]

        result = await orchestrator.execute_strategy(session_id, selected_strategy, payload)

        is_complete = not next_needed
        return {
            "status": "success",
            "session_id": session_id,
            "thought_number": resolved_thought_number,
            "is_complete": is_complete,
            "strategy_used": selected_strategy.value,
            "thought_result": result,
            "next_action": "continue_thinking" if not is_complete else "complete",
        }

    @mcp.tool()
    async def critical_analyze(
        session_id: str,
        thought_content: str,
        critic_persona: str = "auto"
    ) -> Dict[str, Any]:
        """
        CRITICAL (0x2): Identify weaknesses, contradictions, and hidden assumptions.
        Forces the AI into a hostile or skeptical mindset to find flaws in reasoning.
        """
        return await continue_thinking(
            session_id=session_id,
            thought_content=thought_content,
            strategy="actor_critic",
            thought_type="evaluation",
            critic_persona=critic_persona
        )

    @mcp.tool()
    async def evaluate_options(
        session_id: str,
        options_description: str,
        diversity: str = "high"
    ) -> Dict[str, Any]:
        """
        DECISION (0x6): Compare alternatives, perform tradeoff analysis, and scoring.
        Helps in making informed engineering decisions by looking at multiple angles.
        """
        return await brainstorm_alternatives(
            problem_statement=options_description,
            diversity=diversity,
            session_id=session_id
        )

    @mcp.tool()
    async def reflect_reasoning(
        session_id: str
    ) -> Dict[str, Any]:
        """
        REFLECTION (0x5): Self-evaluate reasoning, identify mistakes, and propose improvements.
        Runs a meta-cognitive audit of the session's thought process.
        """
        return await review_thinking(
            session_id=session_id,
            action="reflect"
        )

    @mcp.tool()
    async def verify_output(
        session_id: str,
        output_to_verify: str
    ) -> Dict[str, Any]:
        """
        VERIFICATION (0x4): Check logical consistency, completeness, and hallucination risk.
        Gatekeeper tool to ensure output meets defined criteria and requirements.
        """
        return await evaluate_thinking(
            session_id=session_id,
            action="validate",
            baseline_snapshot=output_to_verify
        )

    @mcp.tool()
    async def generate_plan(
        session_id: str,
        goal_description: str
    ) -> Dict[str, Any]:
        """
        PLANNING (0x3): Create step-by-step execution plans with priority and sequencing.
        """
        return await continue_thinking(
            session_id=session_id,
            thought_content=goal_description,
            strategy="rewoo",
            thought_type="plan"
        )

    @mcp.tool()
    async def review_architecture(
        session_id: str,
        arch_description: str
    ) -> Dict[str, Any]:
        """
        ENGINEERING (ARCH): Detect bad architecture, coupling issues, and technical debt.
        Uses specialized System Architect persona and systemic reasoning.
        """
        return await continue_thinking(
            session_id=session_id,
            thought_content=arch_description,
            strategy="council_of_critics",
            thought_type="review",
            specialized_personas=["System Architect", "Principal Specialist", "Performance Engineer"]
        )

    @mcp.tool()
    async def review_security(
        session_id: str,
        code_or_design: str
    ) -> Dict[str, Any]:
        """
        ENGINEERING (SEC): Identify security flaws, injection risks, and vulnerabilities.
        """
        return await continue_thinking(
            session_id=session_id,
            thought_content=code_or_design,
            strategy="actor_critic",
            thought_type="review",
            critic_persona="Security Expert"
        )

    @mcp.tool()
    async def review_scalability(
        session_id: str,
        system_description: str
    ) -> Dict[str, Any]:
        """
        ENGINEERING (SCALING): Identify bottlenecks and scaling limits across timeframes.
        """
        return await continue_thinking(
            session_id=session_id,
            thought_content=system_description,
            strategy="temporal_horizon",
            thought_type="review",
            projection_scale="LONG_TERM"
        )

    @mcp.tool()
    async def recall_thinking(
        query: str = "",
        session_id: str = "",
        persona: str = "",
        habit: str = "",
        behaviour: str = "",
        project_name: str = "",
        topic: str = "",
        tags: Optional[List[str]] = None,
        limit: int = 10,
        include_patterns: bool = True,
        include_sessions: bool = True,
        include_inferred_context: bool = False,
    ) -> Dict[str, Any]:
        """
        RETRIEVE: Search past sessions and patterns. Use for context from previous work.

        Like episodic memory recall. Supports keyword search, session history, and identity filtering.

        Args:
            query: Search keywords
            session_id: Get full history for specific session
            persona: Filter by persona
            habit: Filter by habit
            behaviour: Filter by behaviour
            project_name: Filter by project
            topic: Filter by topic
            tags: Filter by tags (must have ALL)
            limit: Max results (1-50, default 10)
            include_patterns: Include golden patterns
            include_sessions: Include sessions
            include_inferred_context: Use Hippocampus for context inference

        Returns: matching patterns (id, usage_count), sessions, optional inferred context
        """
        tags = tags or []
        limit = max(1, min(int(limit or 10), 50))

        if session_id:
            if error := validate_session_id(session_id):
                return {"status": "error", "error": error}
            session = orchestrator.memory.get_session(session_id)
            if not session:
                return {"status": "error", "error": "session_not_found"}
            history = orchestrator.memory.get_session_history(session_id)
            criteria = None
            eval_service = getattr(orchestrator, "eval_first_service", None)
            if eval_service:
                criteria_obj = eval_service.get_criteria(session_id)
                criteria = criteria_obj.to_dict() if criteria_obj else None
            return {
                "status": "success",
                "session": {
                    "session_id": session.session_id,
                    "problem_statement": session.problem_statement,
                    "profile": session.profile.value,
                    "complexity": session.complexity,
                    "suggested_pipeline": [s.value for s in session.suggested_pipeline],
                    "identity_layer": session.identity_layer,
                    "knowledge_injection": session.knowledge_injection,
                },
                "steps": [step.model_dump(mode="json") for step in history],
                "evaluation_criteria": criteria,
            }

        patterns: List[Dict[str, Any]] = []
        sessions_out: List[Dict[str, Any]] = []
        inferred_context: Optional[Dict[str, Any]] = None

        if include_patterns:
            if query:
                ranked: List[Tuple[float, Any]] = []
                for p in orchestrator.memory.get_global_patterns():
                    score = max(_score_match(query, p.summary), _score_match(query, p.original_problem))
                    if score > 0:
                        ranked.append((score, p))
                ranked.sort(key=lambda x: (x[0], getattr(x[1], "usage_count", 0)), reverse=True)
                top = [p for _, p in ranked[:limit]]
            else:
                top = orchestrator.memory.get_thinking_patterns_by_usage(limit=limit)
            patterns = [
                {
                    "id": p.id,
                    "content_summary": p.summary,
                    "usage_count": p.usage_count,
                    "session_id": p.session_id,
                    "thought_id": p.thought_id,
                }
                for p in top
            ]

        if include_sessions:
            all_session_ids = orchestrator.memory.list_sessions()
            ranked_sessions: List[Tuple[float, Any]] = []
            for sid in all_session_ids:
                s = orchestrator.memory.get_session(sid)
                if not s:
                    continue
                if persona and (s.identity_layer or {}).get("persona") != persona:
                    continue
                if habit and (s.identity_layer or {}).get("habit") != habit:
                    continue
                if behaviour and (s.identity_layer or {}).get("behaviour") != behaviour:
                    continue
                if project_name and (s.identity_layer or {}).get("project_name") != project_name:
                    continue
                if topic and (s.identity_layer or {}).get("topic") != topic:
                    continue
                if tags:
                    s_tags = (s.identity_layer or {}).get("tags") or []
                    if any(tag not in s_tags for tag in tags):
                        continue
                score = _score_match(query, s.problem_statement) if query else 0.0
                ranked_sessions.append((score, s))
            ranked_sessions.sort(key=lambda x: (x[0], x[1].created_at), reverse=True)
            selected = [s for _, s in ranked_sessions[:limit]]
            for s in selected:
                history = orchestrator.memory.get_session_history(s.session_id)
                status = getattr(s, "status", SessionStatus.ACTIVE)
                sessions_out.append(
                    {
                        "session_id": s.session_id,
                        "problem_statement": s.problem_statement,
                        "completed_at": s.cleared_at or None,
                        "status": status.value if hasattr(status, "value") else str(status),
                        "steps": f"{len(history)}/{s.estimated_total_thoughts}",
                        "complexity": s.complexity,
                    }
                )

        if include_inferred_context:
            hippocampus = getattr(orchestrator, "digital_hippocampus", None)
            if hippocampus:
                inferred_context = hippocampus.infer_current_context(problem_statement=query or "")
            else:
                inferred_context = {"error": "digital_hippocampus_not_initialized"}

        return {
            "status": "success",
            "patterns": patterns,
            "sessions": sessions_out,
            "inferred_context": inferred_context,
        }

    @mcp.tool()
    def decompose_thinking(
        session_id: str,
        action: str = "decompose",
        task_description: str = "",
        context: Optional[Dict[str, Any]] = None,
        unit_id: str = "",
        task_status: str = "",
    ) -> Dict[str, Any]:
        """
        BREAK DOWN: Decompose complex tasks into agent-sized (<=15 min) subtasks.

        Actions:
        - 'decompose': Break task into subtasks with dependencies
        - 'next': Get next ready-to-execute subtask
        - 'update': Mark subtask status (completed/in_progress/pending)
        - 'validate': Check all subtasks are <= 15 min
        - 'plan': Get full decomposition plan + critical path

        Args:
            session_id: Active session ID
            action: 'decompose', 'next', 'update', 'validate', 'plan'
            task_description: Required for 'decompose'
            context: Optional additional context
            unit_id: Required for 'update'
            task_status: For 'update': 'completed', 'in_progress', 'pending'

        Returns: decomposition plan, subtask list, critical path, estimated minutes
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "error": error}
        if not orchestrator.task_decomposition_service:
            return {"status": "error", "error": "task_decomposition_service_not_initialized"}

        normalized_action = (action or "decompose").strip().lower()
        svc = orchestrator.task_decomposition_service

        if normalized_action == "decompose":
            if not task_description.strip():
                return {"status": "error", "error": "task_description_required"}
            plan = svc.decompose_task(session_id=session_id, task_description=task_description, context=context or {})
            return {"status": "success", "session_id": session_id, "decomposition": plan.to_dict()}

        if normalized_action == "next":
            unit = svc.get_next_task(session_id)
            return {
                "status": "success",
                "session_id": session_id,
                "next_task": (
                    {
                        "id": unit.id,
                        "description": unit.description,
                        "estimated_minutes": unit.estimated_minutes,
                        "dependencies": unit.dependencies,
                        "verification_criteria": unit.verification_criteria,
                        "dominant_risk": unit.dominant_risk,
                        "status": unit.status,
                    }
                    if unit
                    else None
                ),
            }

        if normalized_action == "update":
            if not unit_id.strip() or not task_status.strip():
                return {"status": "error", "error": "unit_id_and_task_status_required"}
            return svc.update_task_status(session_id=session_id, unit_id=unit_id, status=task_status)

        if normalized_action == "validate":
            return svc.validate_decomposition(session_id)

        if normalized_action == "plan":
            plan = svc.get_decomposition_plan(session_id)
            return {"status": "success", "session_id": session_id, "decomposition": plan.to_dict() if plan else None}

        return {"status": "error", "error": f"unknown_action:{normalized_action}"}

    @mcp.tool()
    def evaluate_thinking(
        session_id: str,
        action: str = "define",
        capability_evals: Optional[List[str]] = None,
        regression_evals: Optional[List[str]] = None,
        success_metrics: Optional[List[str]] = None,
        baseline_snapshot: str = "",
    ) -> Dict[str, Any]:
        """
        EVALUATE: Define/check evaluation criteria before implementing. "No Code Without Criteria".

        Actions:
        - 'define': Set capability evals, regression evals, success metrics
        - 'check': Check if criteria defined
        - 'validate': Validate against criteria

        Args:
            session_id: Active session ID
            action: 'define', 'check', 'validate'
            capability_evals: Requirements (e.g. ["handles_1000_users"])
            regression_evals: Must-keep-passing tests
            success_metrics: Measurable success criteria
            baseline_snapshot: Optional baseline reference

        Returns: status, criteria lists, validation results
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "error": error}
        if not orchestrator.eval_first_service:
            return {"status": "error", "error": "eval_first_service_not_initialized"}

        normalized_action = (action or "define").strip().lower()
        svc = orchestrator.eval_first_service

        if normalized_action == "define":
            return svc.define_criteria(
                session_id=session_id,
                capability_evals=capability_evals or [],
                regression_evals=regression_evals or [],
                success_metrics=success_metrics or [],
                baseline_snapshot=baseline_snapshot or None,
            )

        if normalized_action == "check":
            status = svc.check_eval_status(session_id)
            criteria_obj = svc.get_criteria(session_id)
            return {
                "status": "success",
                "session_id": session_id,
                "eval_status": status.value if hasattr(status, "value") else str(status),
                "criteria": criteria_obj.to_dict() if criteria_obj else None,
            }

        if normalized_action == "validate":
            return svc.validate_before_implementation(session_id)

        return {"status": "error", "error": f"unknown_action:{normalized_action}"}

    @mcp.tool()
    def plan_thinking(
        pattern: str = "cot",
        problem: str = "",
        context: Optional[Dict[str, Any]] = None,
        available_actions: Optional[List[str]] = None,
        max_steps: int = 10,
        max_depth: int = 3,
        branch_factor: int = 3,
    ) -> Dict[str, Any]:
        """
        PLAN: Generate structured reasoning using explicit patterns (CoT, ToT, ReAct, ReWOO).

        Use standalone (no session needed). Patterns:
        - 'cot': Step-by-step (debugging, analysis)
        - 'tot': Multi-branch exploration (design)
        - 'react': Reason → Act loop (agentic tasks)
        - 'rewoo': Plan → Execute (complex multi-step)
        - 'compare': Compare pattern efficiency

        Args:
            pattern: 'cot' (default), 'tot', 'react', 'rewoo', 'compare'
            problem: Problem to reason about
            context: Optional dict with additional context
            available_actions: For ReAct: available tools/actions
            max_steps: For ReAct (default 10)
            max_depth: For ToT (default 3)
            branch_factor: For ToT (default 3)

        Returns: Dict with reasoning trace, actions, branches, and conclusion
        """
        if not problem.strip():
            return {"status": "error", "error": "problem_required"}

        normalized = (pattern or "cot").strip().lower()
        ctx = context or {}

        if normalized == "react":
            from src.engines.planning.react import ReActEngine
            engine = ReActEngine(max_steps=max_steps)
            return engine.process(problem, ctx, available_actions)

        if normalized == "rewoo":
            from src.engines.planning.rewoo import ReWOOEngine
            engine = ReWOOEngine()
            return engine.process(problem, ctx, available_actions)

        if normalized == "tot":
            from src.engines.planning.threeofthoughts import ToTEngine
            engine = ToTEngine(max_depth=max_depth, branch_factor=branch_factor)
            return engine.process(problem, ctx)

        if normalized == "cot":
            from src.engines.planning.chainofthought import CoTEngine
            engine = CoTEngine(max_steps=max_steps)
            return engine.process(problem, ctx)

        if normalized == "compare":
            from src.engines.planning.react import ReActEngine
            from src.engines.planning.rewoo import ReWOOEngine
            from src.engines.planning.threeofthoughts import ToTEngine
            from src.engines.planning.chainofthought import CoTEngine

            react_engine = ReActEngine(max_steps=min(max_steps, 5))
            rewoo_engine = ReWOOEngine()
            tot_engine = ToTEngine(max_depth=min(max_depth, 2), branch_factor=min(branch_factor, 2))
            cot_engine = CoTEngine(max_steps=min(max_steps, 3))

            react_engine.process(problem, ctx, available_actions)
            rewoo_engine.process(problem, ctx, available_actions)
            tot_engine.process(problem, ctx)
            cot_engine.process(problem, ctx)

            comparison = {
                "react": {"efficiency_score": react_engine.get_token_efficiency_score()},
                "rewoo": {"efficiency_score": rewoo_engine.get_token_efficiency_score()},
                "tot": {"efficiency_score": tot_engine.get_token_efficiency_score()},
                "cot": {"efficiency_score": cot_engine.get_token_efficiency_score()},
            }
            recommended = max(comparison.items(), key=lambda x: x[1]["efficiency_score"])[0]
            return {"status": "success", "comparison": comparison, "recommended": recommended}

        return {"status": "error", "error": f"unknown_pattern:{normalized}"}

    @mcp.tool()
    async def branch_thought(
        session_id: str,
        action: str = "get_tree",
        thought_id: str = "",
        branch_ids: Optional[List[str]] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        BRANCH: Manage Tree-of-Thoughts branching. Explore alternatives, compare paths, prune dead ends.

        Actions:
        - 'get_tree': Visualize full branch tree
        - 'compare': Compare 2+ branches with quality metrics
        - 'prune': Delete dead-end branch + children
        - 'promote': Promote branch to mainline

        Args:
            session_id: Active session ID
            action: 'get_tree', 'compare' (need 2+ branch_ids), 'prune' (need thought_id), 'promote' (need thought_id)
            thought_id: Branch root ID (for prune/promote)
            branch_ids: Branch IDs to compare (for compare, min 2)
            reason: Prune reason (audit log)

        Returns: tree structure, comparison metrics, or prune/promote result
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "action": action, "error": error}

        branch_ids = branch_ids or []

        if action == "get_tree":
            result = orchestrator.memory.get_branch_tree(session_id, thought_id if thought_id else None)
            return {
                "status": "success" if "error" not in result else "error",
                "action": "get_tree",
                **result
            }

        elif action == "compare":
            if len(branch_ids) < 2:
                return {
                    "status": "error",
                    "action": "compare",
                    "error": "Need at least 2 branch_ids to compare"
                }
            result = orchestrator.memory.compare_branches(session_id, branch_ids)
            return {
                "status": "success" if "error" not in result else "error",
                "action": "compare",
                **result
            }

        elif action == "prune":
            if not thought_id:
                return {
                    "status": "error",
                    "action": "prune",
                    "error": "thought_id required for prune action"
                }
            result = orchestrator.memory.prune_branch(session_id, thought_id, reason or "pruned")
            return {
                "status": "success" if result.get("success") else "error",
                "action": "prune",
                **result
            }

        elif action == "promote":
            if not thought_id:
                return {
                    "status": "error",
                    "action": "promote",
                    "error": "thought_id required for promote action"
                }
            result = orchestrator.memory.promote_branch(session_id, thought_id)
            return {
                "status": "success" if result.get("success") else "error",
                "action": "promote",
                **result
            }

        else:
            return {
                "status": "error",
                "action": action,
                "error": f"Unknown action: {action}. Use: get_tree, compare, prune, promote"
            }

    @mcp.tool()
    def export_thought(
        session_id: str,
        session_token: str = "",
        action: str = "export",
        authorized_by: str = "",
        authorization_note: str = "",
    ) -> Dict[str, Any]:
        """
        EXPORT: Retrieve session data, run analysis, or manage clearance. Requires session_token.

        Actions:
        - 'export': Full session history (auth required)
        - 'analyze': Cognitive analysis (clarity, bias, consistency)
        - 'hitl_status': Check clearance status
        - 'grant_clearance': Approve HITL session (auth required)
        - 'get_eval_results': Evaluation criteria results

        Args:
            session_id: Session to export/analyze
            session_token: Bearer token from start_thinking. REQUIRED for export/analyze.
            action: 'export', 'analyze', 'hitl_status', 'grant_clearance', 'get_eval_results'
            authorized_by: Required for grant_clearance
            authorization_note: Optional clearance note

        Returns: session history, analysis metrics, or clearance status. 403 if token invalid.
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "error": error}
        session = orchestrator.memory.get_session(session_id)
        if not session:
            return {"status": "error", "error": "session_not_found"}

        normalized_action = (action or "export").strip().lower()

        if normalized_action in {"export", "analyze", "grant_clearance"}:
            if not orchestrator.memory.validate_session_token(session_id, session_token or ""):
                return {"status": "error", "code": 403, "error": "invalid_or_missing_session_token"}

        if normalized_action == "export":
            history = orchestrator.memory.get_session_history(session_id)
            return {
                "status": "success",
                "session_id": session_id,
                "problem_statement": session.problem_statement,
                "profile": session.profile.value,
                "steps": [h.model_dump(mode="json") for h in history],
            }

        if normalized_action == "analyze":
            history = orchestrator.memory.get_session_history(session_id)
            if not history:
                metrics = SessionMetrics(clarity_score=0.0, bias_flags=[], consistency_score=0.0)
                return {"status": "success", "session_id": session_id, "metrics": metrics.model_dump(mode="json")}

            analyzer = IncrementalSessionAnalyzer()
            for thought in history:
                analyzer.add_thought(thought.content)
            final_metrics = analyzer.get_final_metrics()
            metrics = SessionMetrics(
                clarity_score=round(final_metrics["clarity_score"], 4),
                bias_flags=final_metrics["bias_flags"],
                consistency_score=round(final_metrics["consistency_score"], 4),
            )
            return {
                "status": "success",
                "session_id": session_id,
                "metrics": metrics.model_dump(mode="json"),
            }

        if normalized_action == "hitl_status":
            return orchestrator.autonomous.get_hitl_status(session_id)

        if normalized_action == "grant_clearance":
            return orchestrator.autonomous.grant_clearance(
                session_id=session_id,
                authorized_by=authorized_by,
                note=authorization_note,
            )

        return {"status": "error", "error": f"unknown_action:{normalized_action}"}

    @mcp.tool()
    def log_thought(
        session_id: str,
        action: str,
        thought_id: str = "",
        category: str = "",
        failure_reason: str = "",
        corrective_action: str = "",
        persona: str = "",
        habit: str = "",
        behaviour: str = "",
        example: str = "",
    ) -> Dict[str, Any]:
        """
        LOG: Record cognitive failures, confirm user context, or log observations. Immune System.

        Actions:
        - 'failure': Log a thinking failure as anti-pattern (requires thought_id, category, failure_reason, corrective_action)
        - 'confirm_context': Confirm user identity context (mimic_user profile)
        - 'observation': Log a general observation

        Args:
            session_id: Active session ID
            action: 'failure', 'confirm_context', 'observation'
            thought_id: Required for 'failure'
            category: Failure category: 'Logic', 'Evidence', 'Bias', 'Security', 'Performance', 'Architecture'
            failure_reason: What went wrong (required for 'failure')
            corrective_action: How to avoid (required for 'failure')
            persona: For 'confirm_context'
            habit: For 'confirm_context'
            behaviour: For 'confirm_context'
            example: For 'confirm_context'

        Returns: status and failure_id (if action=failure) for immune system tracking
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "error": error}
        session = orchestrator.memory.get_session(session_id)
        if not session:
            return {"status": "error", "error": "session_not_found"}

        normalized_action = (action or "observation").strip().lower()

        if normalized_action == "failure":
            if not thought_id or not category or not failure_reason or not corrective_action:
                return {"status": "error", "error": "thought_id_category_failure_reason_corrective_action_required"}
            return orchestrator.log_failure(
                session_id=session_id,
                thought_id=thought_id,
                category=category,
                failure_reason=failure_reason,
                corrective_action=corrective_action,
            )

        if normalized_action == "confirm_context":
            try:
                session.identity_layer["persona"] = persona or session.identity_layer.get("persona", "")
                session.identity_layer["habit"] = habit or session.identity_layer.get("habit", "")
                session.identity_layer["behaviour"] = behaviour or session.identity_layer.get("behaviour", "")
                orchestrator.memory.update_session(session)
                return {
                    "status": "success",
                    "persona_confirmed": persona,
                    "habit_confirmed": habit,
                    "behaviour_confirmed": behaviour,
                    "has_example": bool(example),
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

        return {"status": "error", "error": f"unknown_action:{normalized_action}"}

    @mcp.tool()
    def health_thought(check: str = "all") -> Dict[str, Any]:
        """
        CHECK: Server health status. Verifies DB, sessions, and rate limiter are operational.

        Args:
            check: What to check: 'all' (default), 'db', 'sessions', 'rate_limit'

        Returns:
            Dict with overall status ('healthy' or 'degraded'), per-service status, and metrics
        """
        started = datetime.now(timezone.utc)
        normalized = (check or "all").strip().lower()

        db_status = "skipped"
        if normalized in {"all", "db"}:
            try:
                with sqlite3.connect(orchestrator.memory.db_path) as conn:
                    conn.execute("SELECT 1")
                db_status = "ok"
            except Exception:
                db_status = "error"

        active_sessions = None
        if normalized in {"all", "sessions"}:
            try:
                active_sessions = len(orchestrator.memory.list_sessions())
            except Exception:
                active_sessions = -1

        rate_limit = None
        if normalized in {"all", "rate_limit"}:
            limiter = get_rate_limiter()
            rate_limit = {"window_seconds": limiter.config.window_seconds, "max_requests": limiter.config.max_requests}

        elapsed_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000.0

        services = {}
        if db_status != "skipped":
            services["database"] = db_status
        services["memory_manager"] = "ok" if active_sessions is None or active_sessions >= 0 else "error"

        metrics = {"response_time_ms": round(elapsed_ms, 2)}
        if active_sessions is not None:
            metrics["active_sessions"] = active_sessions
        if rate_limit is not None:
            metrics["rate_limit"] = rate_limit

        overall = "healthy"
        if db_status == "error" or (active_sessions is not None and active_sessions < 0):
            overall = "degraded"

        return {"status": overall, "services": services, "metrics": metrics}

    @mcp.tool()
    async def consolidate_thinking(llm_instance_id: str = "") -> Dict[str, Any]:
        """
        CONSOLIDATE: Run memory consolidation (episodic→semantic transfer) to optimize pattern memory.

        Promotes frequently-used patterns to long-term memory, prunes stale patterns,
        detects meta-patterns from strategy co-occurrence, and removes redundant anti-patterns.
        Neural analogue: hippocampal replay during sleep.

        Args:
            llm_instance_id: Optional LLM instance ID to scope consolidation (empty = all)

        Returns:
            Dict with counts of patterns promoted/demoted/pruned, anti-patterns pruned, and meta-patterns detected
        """
        try:
            consolidator = getattr(orchestrator, "consolidation", None)
            if consolidator:
                report = consolidator.consolidate(llm_instance_id=llm_instance_id or None)
            else:
                from src.engines.memory.consolidation import ConsolidationEngine
                consolidator = ConsolidationEngine(orchestrator.memory)
                report = consolidator.consolidate(llm_instance_id=llm_instance_id or None)
            return {
                "status": "success",
                "session_count": report.session_count,
                "patterns_promoted": report.patterns_promoted,
                "patterns_demoted": report.patterns_demoted,
                "patterns_pruned": report.patterns_pruned,
                "anti_patterns_pruned": report.anti_patterns_pruned,
                "meta_patterns_detected": report.meta_patterns_detected,
                "consolidated_at": report.consolidated_at,
            }
        except Exception as e:
            logger.error(f"consolidate_thinking failed: {e}")
            return {"status": "error", "error": str(e)}

    @mcp.tool()
    async def review_thinking(
        session_id: str,
        action: str = "reflect",
    ) -> Dict[str, Any]:
        """
        META: Review and reflect on a completed thinking session. Use AFTER thinking is done to consolidate learning.

        Actions:
        - 'reflect': Analyze what strategies worked, where you got stuck, and what you'd do differently
        - 'patterns': Extract golden patterns and anti-patterns from the session
        - 'summary': Generate an executive summary of the thinking过程 and outcomes

        Args:
            session_id: The completed session to review
            action: Operation: 'reflect' (default), 'patterns', 'summary'

        Returns:
            Dict with review findings, identified patterns, and consolidation recommendations
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "error": error}

        session = orchestrator.memory.get_session(session_id)
        if not session:
            return {"status": "error", "error": "session_not_found"}

        history = orchestrator.memory.get_session_history(session_id)
        norm_action = (action or "reflect").strip().lower()

        # Auto-trigger Hippocampus learning on every review
        try:
            hippocampus = getattr(orchestrator, "digital_hippocampus", None)
            if hippocampus:
                learned = hippocampus.analyze_session(session_id)
                logger.info(f"[REVIEW] Hippocampus analyzed session: "
                           f"{len(learned.learned_preferences)} prefs, "
                           f"{len(learned.learned_rejections)} rejections, "
                           f"{len(learned.learned_patterns)} patterns")
        except Exception as e:
            logger.warning(f"[REVIEW] Hippocampus analysis failed: {e}")

        base = {
            "session_id": session_id,
            "problem": session.problem_statement,
            "total_thoughts": len(history),
            "profile": session.profile.value if hasattr(session.profile, "value") else str(session.profile),
        }

        if norm_action == "summary":
            strategies_used = list(set(h.strategy.value for h in history if h.strategy))
            avg_coherence = sum(h.metrics.logical_coherence for h in history if h and h.metrics) / max(len([h for h in history if h and h.metrics]), 1)
            return {
                **base,
                "action": "summary",
                "strategies_used": strategies_used,
                "avg_coherence": round(avg_coherence, 3),
                "thought_count": len(history),
                "status": session.status.value if hasattr(session.status, "value") else str(session.status),
                "token_usage": {
                    "prompt": session.total_prompt_tokens,
                    "completion": session.total_completion_tokens,
                    "total": session.total_tokens,
                },
                "cost_usd": session.total_cost_usd,
            }

        if norm_action == "patterns":
            patterns = orchestrator.memory.get_all_thinking_patterns()
            anti_patterns = orchestrator.memory.get_all_anti_patterns()
            session_patterns = [p for p in patterns if p.get("session_id") == session_id]
            session_anti = [ap for ap in anti_patterns if ap.get("session_id") == session_id]
            return {
                **base,
                "action": "patterns",
                "session_patterns_count": len(session_patterns),
                "global_patterns_count": len(patterns),
                "session_anti_patterns_count": len(session_anti),
                "global_anti_patterns_count": len(anti_patterns),
            }

        # default: reflect
        strategies_used = list(set(h.strategy.value for h in history if h.strategy))
        stuck_points = [h for h in history if h.metrics and h.metrics.clarity_score < 0.3]
        high_quality = [h for h in history if h.metrics and h.metrics.logical_coherence > 0.8]

        return {
            **base,
            "action": "reflect",
            "strategies_used": strategies_used,
            "stuck_count": len(stuck_points),
            "high_quality_count": len(high_quality),
            "convergence_status": "converged" if session.status in (SessionStatus.COMPLETED, "completed") else "in_progress",
        }

    logger.info(
        "Simplified Tools registered: start_thinking, reframe_problem, brainstorm_alternatives, continue_thinking, "
        "critical_analyze, evaluate_options, reflect_reasoning, verify_output, generate_plan, "
        "review_architecture, review_security, review_scalability, "
        "recall_thinking, decompose_thinking, evaluate_thinking, plan_thinking, branch_thought, export_thought, "
        "log_thought, health_thought, consolidate_thinking, review_thinking"
    )


def _internal_recall(
    orchestrator: CognitiveOrchestrator,
    query: str,
    persona: str,
    habit: str,
    behaviour: str,
    project_name: str,
    topic: str,
    tags: List[str],
    limit: int,
    include_patterns: bool,
    include_sessions: bool,
    include_inferred_context: bool,
) -> Dict[str, Any]:
    patterns: List[Dict[str, Any]] = []
    sessions_out: List[Dict[str, Any]] = []

    if include_patterns:
        if query:
            ranked: List[Tuple[float, Any]] = []
            for p in orchestrator.memory.get_global_patterns():
                score = max(_score_match(query, p.summary), _score_match(query, p.original_problem))
                if score > 0:
                    ranked.append((score, p))
            ranked.sort(key=lambda x: (x[0], getattr(x[1], "usage_count", 0)), reverse=True)
            top = [p for _, p in ranked[:limit]]
        else:
            top = orchestrator.memory.get_thinking_patterns_by_usage(limit=limit)
        patterns = [{"id": p.id, "usage_count": p.usage_count} for p in top]

    if include_sessions:
        for sid in orchestrator.memory.list_sessions():
            s = orchestrator.memory.get_session(sid)
            if not s:
                continue
            if persona and (s.identity_layer or {}).get("persona") != persona:
                continue
            if habit and (s.identity_layer or {}).get("habit") != habit:
                continue
            if behaviour and (s.identity_layer or {}).get("behaviour") != behaviour:
                continue
            if project_name and (s.identity_layer or {}).get("project_name") != project_name:
                continue
            if topic and (s.identity_layer or {}).get("topic") != topic:
                continue
            if tags:
                s_tags = (s.identity_layer or {}).get("tags") or []
                if any(tag not in s_tags for tag in tags):
                    continue
            sessions_out.append({"session_id": s.session_id})
            if len(sessions_out) >= limit:
                break

    inferred_context = None
    if include_inferred_context:
        hippocampus = getattr(orchestrator, "digital_hippocampus", None)
        inferred_context = hippocampus.infer_current_context(problem_statement=query or "") if hippocampus else None

    return {"patterns": patterns, "sessions": sessions_out, "inferred_context": inferred_context}
