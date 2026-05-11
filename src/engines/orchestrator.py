import asyncio
import logging
import uuid
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from src.core.models.enums import ThinkingStrategy, CCTProfile, SessionStatus
from src.core.models.domain import AntiPattern, EnhancedThought
from src.core.services.orchestration.autonomous import AutonomousService
from src.engines.memory.pattern_injector import PatternInjector, InjectionResult
from src.engines.memory.thinking_patterns import PatternArchiver
from src.engines.memory.consolidation import ConsolidationEngine
from src.modes.registry import CognitiveEngineRegistry
from src.engines.memory.manager import MemoryManager
from src.engines.sequential.engine import SequentialEngine
from src.engines.fusion.orchestrator import FusionOrchestrator
from src.core.services.orchestration.adaptive_router import AdaptiveRouter
from src.core.services.analysis.domain_classifier import classify_problem_domain
from src.core.services.loader.skills import SkillsLoader
from src.core.services.analysis.summarization import compress_session_context
from src.utils.pricing import pricing_manager, ForexService
from src.core.services.user.identity import UserIdentityService as IdentityService
from src.core.services.evaluation.clearance import ClearanceService as InternalClearanceService
from src.core.services.analysis.scoring import ScoringService

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
        scoring_engine: ScoringService,
        cognitive_engine_registry: CognitiveEngineRegistry,
        fusion_orchestrator: FusionOrchestrator,
        complexity_service: Any,
        guidance_service: Any,
        autonomous_service: AutonomousService,
        thought_service: Any,
        review_service: Any,
        internal_clearance: Any,
        identity_service: Any,
        digital_hippocampus: Any,
        eval_first_service: Any,
        task_decomposition_service: Any
    ):
        self.memory = memory_manager
        self.sequential = sequential_engine
        self.scoring = scoring_engine
        self.registry = cognitive_engine_registry
        self.fusion = fusion_orchestrator
        self.complexity_service = complexity_service
        self.guidance_service = guidance_service
        self.autonomous = autonomous_service
        self.thought_service = thought_service
        self.review_service = review_service
        self.internal_clearance = internal_clearance
        self.identity = identity_service
        self.digital_hippocampus = digital_hippocampus
        self.eval_first_service = eval_first_service
        self.task_decomposition_service = task_decomposition_service
        self.router = AdaptiveRouter(scoring_engine=scoring_engine)
        self.skills_loader = SkillsLoader()
        self.pattern_archiver = PatternArchiver(memory_manager)
        self.consolidation = ConsolidationEngine(memory_manager)
        self._consolidation_counter = 0
        logger.info("Cognitive Orchestrator (with Identity/Fusion/AdaptiveRouter/Autonomous/Skills/PatternArchiver/Consolidation/InternalClearance/EvalFirst/TaskDecomposition) initialized.")

    async def think(self, session_id: str, payload: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        The autonomous 'Autonomous Think' entry point.
        Determines the next strategy dynamically and executes it.
        """
        session = self.memory.get_session(session_id)
        if not session:
            return {"status": "error", "message": f"Session {session_id} not found."}

        history = self.memory.get_session_history(session_id)

        # 2. Consult the Adaptive Router (wraps IntelligenceRouter with learning)
        strategy = self.router.next_strategy(session, history)

        # [AUTONOMOUS] If the router suggests finishing, wrap up and record outcome
        if self.router.should_finish(session, history):
            # Record successful outcome for adaptive learning
            domain = classify_problem_domain(session.problem_statement)
            if history:
                last_strat = history[-1].strategy.value if history[-1].strategy else "unknown"
                self.router.record_outcome(domain, last_strat, success=True)
            # Trigger consolidation every 5 concluded sessions
            self._consolidation_counter += 1
            if self._consolidation_counter >= 5:
                llm_id = getattr(session, "llm_instance_id", None)
                asyncio.ensure_future(self._run_consolidation(llm_id))
                self._consolidation_counter = 0
            return {
                "status": "success",
                "session_id": session_id,
                "message": "Cognitive goal achieved. Process finishing.",
                "is_concluded": True
            }

        # 3. [ENRICHMENT] Auto-populate payload for Engine Schemas
        # If payload is mostly empty (autonomous), we derive defaults from the session
        if "strategy" not in payload:
            payload["strategy"] = strategy.value
        if "thought_number" not in payload:
            payload["thought_number"] = session.current_thought_number + 1
        if "estimated_total_thoughts" not in payload:
            payload["estimated_total_thoughts"] = session.estimated_total_thoughts
        if "thought_type" not in payload:
            # Default to plan for start, eval for middle, conclusion for end
            if session.current_thought_number == 0:
                payload["thought_type"] = "plan"
            elif session.current_thought_number >= session.estimated_total_thoughts - 1:
                payload["thought_type"] = "conclusion"
            else:
                payload["thought_type"] = "analysis"

        # [INPUT MAPPING] Map custom_instruction to thought_content if missing
        if "thought_content" not in payload and "custom_instruction" in payload:
            payload["thought_content"] = payload["custom_instruction"]
        elif "thought_content" not in payload:
            # Fallback for truly autonomous steps with no prompt
            payload["thought_content"] = f"Proceeding with {strategy.value} strategy based on mission objectives."

        # 4. Execute the detected strategy
        logger.info(f"[AUTONOMOUS] Determined next strategy: {strategy.value}")
        return await self.execute_strategy(session_id, strategy, payload)

    async def execute_strategy(
        self,
        session_id: str,
        strategy: ThinkingStrategy,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Routes the task to the appropriate engine and manages session context.

        [HITL ENFORCEMENT] For HUMAN_IN_THE_LOOP profiles, execution is blocked
        if awaiting human clearance (hard STOP at Phase 7).
        """
        logger.info(f"Orchestrating strategy '{strategy.value}' for session '{session_id}'")

        # [HITL CHECK] Block execution if awaiting human clearance
        hitl_check = self.autonomous.check_execution_allowed(session_id)
        if not hitl_check.get("allowed", True):
            logger.warning(f"[HITL] Execution blocked for session {session_id}: {hitl_check.get('error')}")
            return hitl_check

        # [TOKEN ECONOMY] Reactive Context Compression
        # If history is getting large, compress it before sending to the engine
        history = self.memory.get_session_history(session_id)
        if len(history) > 5:  # Threshold for proactive compression
            logger.info(f"Checking token budget for session {session_id} history (count: {len(history)})")
            # We compress if total tokens exceed a heuristic budget (e.g., 6000)
            # This ensures the LLM doesn't lose current focus
            compression = compress_session_context(history, token_budget=6000)
            if compression.thoughts_summarized > 0:
                logger.warning(f"[IRIT] Context compressed: {compression.original_tokens} -> {compression.compressed_tokens} tokens")
                # We inject the summary into the payload for the engine to consume as historical context
                payload["historical_summary"] = compression.summary
                payload["preserved_context_ids"] = compression.preserved_thoughts

        # [HYBRID KNOWLEDGE] Load Action Skills for strategy
        self.skills_loader.inject_skills_context(strategy, payload)

        # 1. Fetch the correct engine from the Registry
        engine = self.registry.get_engine(strategy)
        if not engine:
            error_msg = f"No engine found for strategy: {strategy.value}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # 2. Hand off execution to the specialized Engine
        try:
            # Inject model_id into payload if not present
            session = self.memory.get_session(session_id)
            if session and "model_id" not in payload:
                payload["model_id"] = session.model_id

            result = await engine.execute(session_id, payload)

            # Refresh once after strategy execution and reuse for all downstream steps.
            updated_history = self.memory.get_session_history(session_id)
            session = self.memory.get_session(session_id)

            # 3. [AUTOMATIC PIPELINE] Adaptive Feedback Loop
            self.check_and_pivot(session_id, history=updated_history)

            # 4. [TRANSPARENCY LAYER] Aggregate usage and cost summary
            if session:
                # Recalculate session totals from history to ensure absolute accuracy.
                total_in = sum(t.metrics.input_tokens for t in updated_history)
                total_out = sum(t.metrics.output_tokens for t in updated_history)
                total_usd = sum(t.metrics.input_cost_usd + t.metrics.output_cost_usd for t in updated_history)
                total_idr = sum(t.metrics.input_cost_idr + t.metrics.output_cost_idr for t in updated_history)

                session.total_prompt_tokens = total_in
                session.total_completion_tokens = total_out
                session.total_cost_usd = round(total_usd, 10)
                session.total_cost_idr = round(total_idr, 5)
                self.memory.update_session(session)

                # 4b. [LTP] Archive only the latest thought candidate.
                # Scanning entire history on every step causes O(n^2) growth across long sessions.
                if updated_history:
                    latest_thought = updated_history[-1]
                    if latest_thought.metrics and latest_thought.metrics.logical_coherence >= 0.9:
                        archive_result = self.pattern_archiver.archive_thought(latest_thought, session_id)
                        if archive_result.archived:
                            logger.info(f"[LTP] Golden pattern archived: {archive_result.pattern_id}")

                # Attach usage block to result for tool output
                live_rate = updated_history[-1].metrics.currency_rate_idr if updated_history else ForexService.DEFAULT_RATE
                result["usage"] = {
                    "model_used": session.model_id,
                    "session_totals": {
                        "tokens": {
                            "input": session.total_prompt_tokens,
                            "output": session.total_completion_tokens,
                            "total": session.total_tokens
                        },
                        "cost_usd": session.total_cost_usd,
                        "cost_idr": session.total_cost_idr
                    },
                    "token_economy": {
                        "proactive_compression": len(updated_history) > 5,
                        "summary_active": "historical_summary" in payload
                    },
                    "currency_meta": {
                        "usd_idr_rate": live_rate,
                        "source": "frankfurter.app (cached 24h)",
                        "projection_year": 2026
                    }
                }

            # 5. [HITL TRIGGER] Evaluation for Clearance Checkpoint
            # If engine finished or converged, and profile is HITL, trigger the stop
            convergence = self.sequential.evaluate_convergence(
                session_id,
                payload.get("next_thought_needed", True),
                metrics=result.get("metrics")
            )
            if convergence.get("is_ready") and session.profile == CCTProfile.HUMAN_IN_THE_LOOP:
                logger.warning(f"[HITL] Session {session_id} converged. Triggering Phase 7 Clearance Checkpoint.")
                # We use the current result summary as the basis for the human stop
                executive_summary = {
                    "last_strategy": strategy.value,
                    "thought_id": result.get("generated_thought_id"),
                    "metrics": result.get("metrics"),
                    "convergence_reason": convergence.get("reason")
                }
                stop_result = self.autonomous.trigger_human_stop(session_id, executive_summary)
                # Merge HITL instructions into the final result
                result.update(stop_result)

            # Record successful outcome for adaptive learning
            try:
                if session:
                    domain = classify_problem_domain(session.problem_statement)
                    self.router.record_outcome(domain, strategy.value, success=True)

                    # Auto-trigger Hippocampus learning on session conclusion
                    if hasattr(self, "digital_hippocampus") and self.digital_hippocampus:
                        try:
                            self.digital_hippocampus.analyze_session(session_id)
                            logger.info(f"[ORCHESTRATOR] Auto-learned from session {session_id}")
                        except Exception as e:
                            logger.warning(f"[ORCHESTRATOR] Auto-learning failed: {e}")
            except Exception:
                pass

            return result
        except Exception as e:
            logger.exception(f"Execution failed for strategy {strategy.value}")
            # Record failure
            try:
                if session:
                    domain = classify_problem_domain(session.problem_statement)
                    self.router.record_outcome(domain, strategy.value, success=False)
            except Exception:
                pass
            return {
                "status": "error",
                "strategy": strategy.value,
                "message": str(e)
            }

    def start_session(self, problem_statement: str, profile: str = "balanced", model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Entry point for starting a cognitive session.

        Phase 0: Meta-Cognitive Routing with Automatic Pattern Injection
        - Initializes the state with 'Automatic Pipeline' recommendation
        - Auto-detects model_id from ENV if not provided
        - Injects relevant Golden Thinking Patterns (Evolutionary Memory)
        - Loads Anti-Patterns to prevent known failures (Immune System)
        """
        logger.info(f"Initializing new CCT session. Profile: {profile}")

        # [PHASE 0] Identity Layer Ignition (Digital Symbiosis)
        identity_context = self.identity.load_identity()

        # [PHASE 0] Model Detection
        if not model_id:
            # Order of priority: ENV[LLM_MODEL] -> ENV[CCT_DEFAULT_MODEL] -> Settings.default_model -> Baseline fallback
            model_id = os.environ.get("LLM_MODEL") or os.environ.get("CCT_DEFAULT_MODEL")

        try:
            try:
                cct_profile = CCTProfile(profile.lower())
            except ValueError:
                cct_profile = CCTProfile.BALANCED
                logger.warning(f"Invalid profile {profile}, defaulting to balanced")

            # 1. DESIGN DYNAMIC PIPELINE (Phase 0 - Meta-Cognitive Routing)
            suggested_pipeline = self.router.determine_initial_pipeline(problem_statement)

            # 2. INITIALIZE SESSION
            session = self.memory.create_session(
                problem_statement,
                cct_profile,
                estimated_thoughts=len(suggested_pipeline)
            )

            # [REASONING TRACE] Initialize unique trace ID (Checklist 0x9)
            session.identity_layer = {
                **(session.identity_layer or {}),
                "reasoning_trace_id": f"trace_{uuid.uuid4().hex[:12]}"
            }

            # Apply detected/provided model_id
            if model_id:
                session.model_id = model_id

            mimic_payload: Dict[str, Any] = {}
            if cct_profile == CCTProfile.MIMIC_USER:
                inference = {}
                if self.digital_hippocampus:
                    inference = self.digital_hippocampus.infer_current_context(
                        problem_statement=problem_statement
                    )

                confidence = float(inference.get("confidence", 0.0) or 0.0)
                decision = str(inference.get("decision", "fallback_balanced"))
                persona = inference.get("persona")
                habit = inference.get("habit")
                behaviour = inference.get("behaviour")

                mimic_payload = {
                    "decision": decision,
                    "confidence": confidence,
                    "persona": persona,
                    "habit": habit,
                    "behaviour": behaviour,
                    "signals": inference.get("signals") or [],
                    "needs_confirmation": bool(inference.get("needs_confirmation", False)),
                    "confirmation_question": inference.get("confirmation_question"),
                    "reasoning_priors": inference.get("reasoning_priors") or "",
                }

            # 3. [PHASE 0] AUTOMATIC PATTERN INJECTION (Evolutionary Memory)
            # Inject relevant Golden Thinking Patterns and Anti-Patterns
            injector = PatternInjector(self.memory)
            injection_result = injector.inject_for_session(
                session_id=session.session_id,
                problem_statement=problem_statement
            )

            # Keep backward-compatible payload shape using the same selected sets.
            injected_patterns = injection_result.selected_patterns
            injected_failures = injection_result.selected_anti_patterns

            # 4. ENRICH SESSION STATE
            session.suggested_pipeline = suggested_pipeline
            session.identity_layer = identity_context
            session.knowledge_injection = {
                "phase_0_injection": injection_result.injection_context,
                "golden_thinking_patterns": [p.model_dump(mode="json") for p in injected_patterns],
                "anti_patterns": [f.model_dump(mode="json") for f in injected_failures],
                "injected_patterns_count": injection_result.patterns_injected,
                "injected_anti_patterns_count": injection_result.anti_patterns_injected,
                "relevance_scores": injection_result.relevance_scores
            }
            if mimic_payload:
                session.identity_layer = {
                    **(session.identity_layer or {}),
                    "persona": mimic_payload.get("persona"),
                    "habit": mimic_payload.get("habit"),
                    "behaviour": mimic_payload.get("behaviour"),
                    "mimic_confidence": mimic_payload.get("confidence"),
                    "mimic_decision": mimic_payload.get("decision"),
                }
                session.knowledge_injection = {
                    **(session.knowledge_injection or {}),
                    "mimic_user": mimic_payload,
                }
            self.memory.update_session(session)

            logger.info(
                f"[Phase 0] Session {session.session_id}: Injected "
                f"{injection_result.patterns_injected} patterns, "
                f"{injection_result.anti_patterns_injected} anti-patterns"
            )

            return {
                "status": "success",
                "session_id": session.session_id,
                "session_token": session.session_token,
                "problem_statement": session.problem_statement,
                "profile": session.profile.value,
                "dynamic_pipeline": [s.value for s in suggested_pipeline],
                "injected_patterns_count": injection_result.patterns_injected,
                "injected_anti_patterns_count": injection_result.anti_patterns_injected,
                "legacy_skills_count": len(injected_patterns),
                "legacy_failures_count": len(injected_failures),
                "mimic": mimic_payload or None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to start session: {str(e)}")
            return {"status": "error", "message": f"Session initialization failed: {str(e)}"}

    def check_and_pivot(self, session_id: str, history: Optional[List[EnhancedThought]] = None) -> None:
        """
        [ROUTER] Evaluation hook to see if the session needs a strategy pivot.
        """
        session = self.memory.get_session(session_id)
        if not session:
            return

        history = history if history is not None else self.memory.get_session_history(session_id)
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

    def log_failure(
        self,
        session_id: str,
        thought_id: str,
        category: str,
        failure_reason: str,
        corrective_action: str
    ) -> Dict[str, Any]:
        """
        [IMMUNE SYSTEM] Bridges the failure logging tool to the persistent archive.
        Ensures cognitive forensics are captured to prevent recurrence.
        """
        try:
            # 1. Fetch context from memory
            session = self.memory.get_session(session_id)
            thought = self.memory.get_thought(thought_id)

            if not session or not thought:
                return {"status": "error", "message": "Session or Thought not found."}

            # 2. Construct AntiPattern domain model
            failure = AntiPattern(
                id=f"failure_{uuid.uuid4().hex[:8]}",
                thought_id=thought_id,
                session_id=session_id,
                category=category,
                failed_strategy=thought.strategy,
                problem_context=session.problem_statement[:200], # Truncated context
                failure_reason=failure_reason,
                corrective_action=corrective_action
            )

            # 3. Persist to Immune System
            self.memory.save_anti_pattern(failure)

            return {
                "status": "success",
                "failure_id": failure.id,
                "category": category,
                "archived": True
            }
        except Exception as e:
            logger.error(f"Failed to log failure: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _run_consolidation(self, llm_instance_id: Optional[str] = None) -> None:
        """
        Background consolidation: episodic → semantic memory transfer.
        Runs async so it doesn't block the main thinking flow.
        """
        try:
            report = self.consolidation.consolidate(llm_instance_id=llm_instance_id)
            logger.info(
                f"[CONSOLIDATION] Background cycle: {report.patterns_promoted} promoted, "
                f"{report.patterns_pruned} pruned, {report.meta_patterns_detected} meta-patterns"
            )
        except Exception as e:
            logger.error(f"[CONSOLIDATION] Background cycle failed: {e}")
