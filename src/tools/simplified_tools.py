"""
Simplified CCT Tools - Auto-Start Thinking System

Ultra-simple 3-tool API with auto session management:
- thinking: Start new session + execute first thinking step automatically
- rethinking: Continue thinking from existing session (step 2, 3, etc.)
- list_thinking: List all thinking sessions with metadata

No manual session_start needed - sessions auto-create on first thinking call.
Automatic Strategy Selection based on detected complexity:
- SIMPLE (1-3 steps): Linear, Analytical
- MODERATE (4-6 steps): + Systemic, First Principles  
- COMPLEX (7+ steps): + Actor-Critic, Council, Lateral Pivot, Temporal Horizon
"""
from __future__ import annotations
from typing import Any, Dict, Optional, List
import logging
from enum import Enum
from mcp.server.fastmcp import FastMCP

from src.core.models.enums import ThinkingStrategy, ThoughtType, CCTProfile, SessionStatus
from src.core.validators import validate_session_id, validate_thought_content, validate_problem_statement
from src.core.rate_limiter import rate_limited
from src.engines.orchestrator import CognitiveOrchestrator
from src.utils.pipelines import PipelineSelector
from src.analysis.bias import detect_bias_flags, has_critical_bias

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity for determining pipeline depth."""
    SIMPLE = "simple"      # 1-3 steps: Linear strategies
    MODERATE = "moderate"  # 4-6 steps: + Systemic, First Principles
    COMPLEX = "complex"    # 7+ steps: + Hybrid strategies (Actor-Critic, Council, etc)


def _detect_complexity(problem_statement: str, estimated_thoughts: int = 0) -> Tuple[TaskComplexity, str]:
    """
    Detect task complexity and category from problem statement using multi-factor analysis.
    
    Heuristics (weighted scoring system):
    - Category baseline (ARCH, SEC = +25, BIZ/DEBUG = +15)
    - Word count & sentence depth
    - Technical domain density (expanded keyword set)
    - Bias Detection: (Oversimplification flags increase rigor requirement)
    - Structural markers (lists, questions)
    """
    import re
    
    text_lower = problem_statement.lower()
    words = problem_statement.split()
    word_count = len(words)
    sentences = re.split(r'[.!?]+', problem_statement)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 0. Detect Category Baseline (from PipelineSelector)
    category = PipelineSelector.detect_category(problem_statement)
    complexity_score = 0
    
    if category == "ARCH":
        complexity_score += 25
    elif category == "SEC":
        complexity_score += 30
    elif category == "DEBUG":
        complexity_score += 15
    elif category == "BIZ":
        complexity_score += 20
        
    # 1. Word count scoring (0-20 points)
    if word_count >= 150:
        complexity_score += 20
    elif word_count >= 100:
        complexity_score += 15
    elif word_count >= 50:
        complexity_score += 10
    
    # 2. Sentence complexity (0-15 points)
    if sentences:
        avg_words_per_sentence = word_count / len(sentences)
        if avg_words_per_sentence > 25:
            complexity_score += 15
        elif avg_words_per_sentence > 20:
            complexity_score += 10
            
    # 3. Technical keyword density (expanded mapping)
    technical_domains = {
        "architecture": ["architecture", "refactor", "framework", "microservices", "modular", "distributed"],
        "security": ["vulnerability", "auth", "encrypt", "sanitize", "hardened", "adversarial"],
        "performance": ["optimization", "latency", "throughput", "concurrency", "bottleneck"],
        "infrastructure": ["kubernetes", "docker", "terraform", "ci/cd", "deployment", "cloud"]
    }
    
    detected_domains = sum(1 for d, kws in technical_domains.items() if any(kw in text_lower for kw in kws))
    complexity_score += detected_domains * 8
    
    # 4. Bias/Oversimplification Flag (Rigor requirement increase)
    # If the user says "just", "simple", "it's easy", we INCREASE complexity score 
    # to force more critical evaluation.
    bias_markers = ["just", "simple", "easy", "obviously", "minimal", "quick fix", "trivial"]
    detected_biases = sum(1 for m in bias_markers if f" {m} " in f" {text_lower} ")
    if detected_biases > 0:
        logger.info(f"[COMPLEXITY] Oversimplification markers detected ({detected_biases}). Increasing rigor score.")
        complexity_score += min(detected_biases * 10, 20)

    # 5. Dependency & Decision indicators
    dependency_count = sum(1 for p in [r"\bdepends?\s+on\b", r"\brequires?\b", r"\bif\b.*\bthen\b"] if re.search(p, text_lower))
    complexity_score += min(dependency_count * 5, 15)
    
    # 6. Structural indicators (Lists/Questions)
    question_count = problem_statement.count('?')
    complexity_score += min(question_count * 3, 10)
    
    # List detection logic (simplified regex to avoid encoding issues)
    list_indicators = len(re.findall(r'^[\s]*[-*\d+]', problem_statement, re.MULTILINE))
    complexity_score += min(list_indicators * 2, 8)
    
    # 7. Weighted Category Scoring
    categories = PipelineSelector.detect_categories(problem_statement)
    primary_category = PipelineSelector.detect_category(problem_statement)
    
    # Category baseline boost: add 5 points for every identified domain
    complexity_score += len(categories) * 5
    
    # Override with estimated_thoughts if explicitly provided
    if estimated_thoughts > 0:
        if estimated_thoughts >= 7:
            return TaskComplexity.COMPLEX, primary_category, categories
        elif estimated_thoughts >= 4:
            return TaskComplexity.MODERATE, primary_category, categories
        else:
            return TaskComplexity.SIMPLE, primary_category, categories
    
    logger.info(f"[COMPLEXITY] Score: {complexity_score}/100, Primary: {primary_category}, Multi: {categories}")
    
    result = TaskComplexity.SIMPLE
    if complexity_score >= 75:
        result = TaskComplexity.COMPLEX
    elif complexity_score >= 40:
        result = TaskComplexity.MODERATE
        
    return result, primary_category, categories


def _get_strategy_pipeline(complexity: TaskComplexity, current_step: int, 
                           last_clarity: float = 0.8, last_coherence: float = 0.8,
                           category: str = "GENERIC") -> ThinkingStrategy:
    """
    Determine next strategy based on category (templates) or fallback complexity.
    """
    # 1. Quality-Based Pivot (Automatic Guardrail)
    if last_clarity < 0.6 or last_coherence < 0.6:
        logger.warning(f"[ROUTER] Quality drop detected (clarity={last_clarity}, coherence={last_coherence}). Triggering UNCONVENTIONAL_PIVOT.")
        return ThinkingStrategy.UNCONVENTIONAL_PIVOT
    
    # 2. COMPLEX: Always use the Sovereign 8-Step Pipeline for high-rigor tasks
    if complexity == TaskComplexity.COMPLEX:
        pipeline = PipelineSelector.SOVEREIGN_PIPELINE
        if 0 <= current_step < len(pipeline):
            return pipeline[current_step]
        return ThinkingStrategy.MULTI_AGENT_FUSION
    
    # 3. Category-Based Template Logic (Moderate/Simple)
    if category != "GENERIC":
        template = PipelineSelector.PIPELINE_TEMPLATES.get(category, [])
        if template and 0 <= current_step < len(template):
            return template[current_step]
    
    # 4. Fallback Complexity-Based Logic
    if complexity == TaskComplexity.SIMPLE:
        if current_step == 0: return ThinkingStrategy.LINEAR
        if current_step == 1: return ThinkingStrategy.ANALYTICAL
        return ThinkingStrategy.INTEGRATIVE
    
    else:  # MODERATE Generic
        if current_step == 0: return ThinkingStrategy.EMPIRICAL_RESEARCH
        if current_step == 1: return ThinkingStrategy.FIRST_PRINCIPLES
        if current_step == 2: return ThinkingStrategy.SYSTEMIC
        return ThinkingStrategy.INTEGRATIVE


def register_simplified_tools(mcp: FastMCP, orchestrator: CognitiveOrchestrator, settings: Any):
    """
    Register simplified tools to MCP server.
    Only 3 tools: thinking, rethinking, list_thinking
    """
    
    @mcp.tool()
    @rate_limited(max_requests=10, window_seconds=60)
    async def thinking(
        problem_statement: str,
        thought_content: str = "",
        profile: str = "balanced",
        model_id: str = "",
        estimated_thoughts: int = 0
    ) -> Dict[str, Any]:
        """
        [THINKING] Start new cognitive session + execute first thinking step automatically.
        
        NO need to call session_start first - this tool auto-creates session on first call!
        Automatically detects complexity and executes step 1 with appropriate strategy.
        
        Args:
            problem_statement: The problem/task to think through (creates new session)
            thought_content: Content for first thinking step (optional, auto-generated if empty)
            profile: Cognitive profile - "balanced", "creative", "critical", "human_in_the_loop"
            model_id: Active model ID for token tracking (e.g., 'gemini-1.5-flash')
            estimated_thoughts: Estimated thinking steps (0 = auto-detect based on complexity)
            
        Returns:
            Combined result: session created + first thinking step executed
            {
                "session_id": "sess_xxx",
                "detected_complexity": "moderate",
                "step_1_result": {...},
                "next_step": "Call rethinking with step=2"
            }
            
        Rate Limit: 10 requests per 60 seconds
        """
        import time
        start_time = time.time()
        
        if error := validate_problem_statement(problem_statement):
            return {"status": "error", "error": error}
        
        # Step 1: Detect complexity & category
        complexity, primary_category, category_map = _detect_complexity(problem_statement, estimated_thoughts)
        logger.info(f"[THINKING] New session - Complexity: {complexity.value}, Primary: {primary_category}")
        
        # Step 2: Create session
        try:
            profile_enum = CCTProfile(profile.lower()) if profile.lower() in ["balanced", "creative", "critical", "human_in_the_loop"] else CCTProfile.BALANCED
            
            # Select initial pipeline based on category/complexity
            pipeline = PipelineSelector.select_pipeline(problem_statement, complexity.value)
            
            # Adjust estimated thoughts based on pipeline length if COMPLEX
            final_est = estimated_thoughts if estimated_thoughts > 0 else (8 if complexity == TaskComplexity.COMPLEX else 5)
            
            session = orchestrator.memory.create_session(
                problem_statement=problem_statement,
                profile=profile_enum,
                estimated_thoughts=final_est,
                model_id=model_id if model_id else "claude-3-5-sonnet-20240620",
                complexity=complexity.value
            )
            session_id = session.session_id
            
            # Persist multi-domain context and pipeline
            session.detected_categories = category_map
            session.primary_category = primary_category
            session.suggested_pipeline = pipeline
            session.complexity = complexity.value
            orchestrator.memory.update_session(session)
            
        except Exception as e:
            logger.error(f"[THINKING] Failed to create session: {e}")
            return {"status": "error", "error": f"Session creation failed: {str(e)}"}
        
        # Step 3: Execute first thinking step
        if not thought_content:
            thought_content = f"Initial analysis of: {problem_statement[:100]}..."
        
        try:
            # Determine strategy for step 1
            strategy = _get_strategy_pipeline(complexity, 0, 0.8, 0.8)
            logger.info(f"[THINKING] Step 1 using strategy: {strategy.value}")
            
            # Execute first thought
            payload = {
                "thought_content": thought_content,
                "thought_type": ThoughtType.ANALYSIS,
                "strategy": strategy,
                "thought_number": 1,
                "estimated_total_thoughts": session.estimated_total_thoughts,
                "next_thought_needed": session.estimated_total_thoughts > 1
            }
            
            thought_result = orchestrator.execute_strategy(session_id, strategy, payload)
            
            total_time = time.time() - start_time
            logger.info(f"[THINKING] Session {session_id} - Step 1 complete (total: {total_time:.3f}s)")
            
            # Extract usage/financial telemetry for premium output
            usage = thought_result.get("usage", {})
            
            return {
                "status": "success",
                "session_id": session_id,
                "session_token": session.session_token,
                "detected_complexity": complexity.value,
                "detected_category": primary_category,
                "total_steps": session.estimated_total_thoughts,
                "step_1_completed": True,
                "strategy_used": strategy.value,
                "thought_result": thought_result,
                "financial_telemetry": usage.get("session_totals", {}),
                "token_economy": usage.get("token_economy", {}),
                "next_action": "Call rethinking" if session.estimated_total_thoughts > 1 else "Session complete",
                "processing_time": f"{total_time:.3f}s"
            }
            
        except Exception as e:
            logger.error(f"[THINKING] Step 1 failed: {e}")
            return {
                "status": "partial_success",
                "session_id": session_id,
                "detected_complexity": complexity.value,
                "session_created": True,
                "step_1_error": str(e),
                "note": "Session created but first thinking step failed"
            }


    @mcp.tool()
    @rate_limited(max_requests=60, window_seconds=60)
    async def rethinking(
        session_id: str,
        thought_content: str,
        thought_number: int = 2,
        estimated_total_thoughts: int = 5,
        next_thought_needed: bool = True,
        thought_type: str = "analysis",
        strategy: str = "auto",
        is_revision: bool = False,
        revises_thought_id: Optional[str] = None,
        branch_from_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        critic_persona: str = "auto",
        specialized_personas: Optional[List[str]] = None,
        provocation_method: str = "REVERSE_ASSUMPTION",
        projection_scale: str = "LONG_TERM"
    ) -> Dict[str, Any]:
        """
        [RETHINKING] Continue thinking from existing session (step 2, 3, etc.)
        
        Use this after calling 'thinking' to continue the cognitive process.
        Auto-detects complexity from session and selects appropriate strategy.
        
        Args:
            session_id: Session ID from previous 'thinking' call
            thought_content: Content to process in this step
            thought_number: Current step number (start from 2)
            estimated_total_thoughts: Total expected steps
            next_thought_needed: Whether more steps are needed after this one
            thought_type: Type of thought (analysis, observation, conclusion)
            strategy: "auto" for automatic selection or specific strategy name
            is_revision: Whether this is revising a previous thought
            revises_thought_id: ID of thought being revised (if is_revision=True)
            
        Auto-Selection Strategy:
        - Step 1: empirical_research
        - Step 2: first_principles
        - Step 3 (COMPLEX): actor_critic_loop
        - Step 4 (COMPLEX): council_of_critics
        - Step 5 (COMPLEX): unconventional_pivot
        - Step 6 (COMPLEX): long_term_horizon
        
        Rate Limit: 60 requests per 60 seconds per session
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "error": error}
        
        if error := validate_thought_content(thought_content):
            return {"status": "error", "error": error}
        
        # Get session info for complexity detection
        session = orchestrator.memory.get_session(session_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        # Get history for quality metrics
        history = orchestrator.memory.get_session_history(session_id)
        last_clarity = 0.8
        last_coherence = 0.8
        if history:
            last = history[-1]
            last_clarity = last.metrics.clarity_score
            last_coherence = last.metrics.logical_coherence
        
        # Determine complexity & category from session metadata
        complexity_val = getattr(session, 'complexity', 'simple')
        complexity = TaskComplexity(complexity_val)
        
        # Re-detect category for routing (or store it in future schema)
        category = PipelineSelector.detect_category(session.problem_statement)
        
        # Determine strategy
        selected_strategy = None
        if strategy.lower() == "auto":
            # Automatic strategy selection
            selected_strategy = _get_strategy_pipeline(
                complexity, 
                thought_number - 1,  # 0-indexed
                last_clarity,
                last_coherence,
                category=category
            )
            logger.info(f"[AUTO-STRATEGY] Step {thought_number}/{estimated_total_thoughts}, Category={category}, Complexity={complexity.value}, Selected={selected_strategy.value}")
        else:
            # Manual override
            try:
                selected_strategy = ThinkingStrategy(strategy.lower())
            except ValueError:
                return {"error": f"Strategy '{strategy}' not supported. Use 'auto' or valid strategy name."}
        
        # Build payload based on strategy type
        payload = {
            "thought_content": thought_content,
            "thought_type": ThoughtType(thought_type),
            "strategy": selected_strategy,
            "thought_number": thought_number,
            "estimated_total_thoughts": estimated_total_thoughts,
            "next_thought_needed": next_thought_needed,
            "is_revision": is_revision,
            "revises_thought_id": revises_thought_id,
            "branch_from_id": branch_from_id,
            "branch_id": branch_id,
        }
        
        # Add adaptive candidate parameters for hybrid debate strategies
        if selected_strategy == ThinkingStrategy.ACTOR_CRITIC_LOOP:
            payload["target_thought_id"] = history[-1].id if history else None
            # Adaptive persona for Critic
            critic_name = PipelineSelector.DOMAIN_PERSONAS.get(category, "Critical Reviewer")
            payload["critic_persona"] = critic_name if critic_persona == "auto" else critic_persona
            
        elif selected_strategy == ThinkingStrategy.COUNCIL_OF_CRITICS:
            payload["target_thought_id"] = history[-1].id if history else None
            # Adaptive personas for Council based on all detected domains
            detected = getattr(session, 'detected_categories', {category: 1.0} if category != "GENERIC" else {})
            payload["personas"] = specialized_personas or PipelineSelector.get_personas_for_domains(detected)
            
        elif selected_strategy == ThinkingStrategy.UNCONVENTIONAL_PIVOT:
            payload["current_paradigm"] = thought_content[:150]  # Snippet for pivot context
            payload["provocation_method"] = provocation_method
            
        elif selected_strategy == ThinkingStrategy.LONG_TERM_HORIZON:
            payload["target_thought_id"] = history[-1].id if history else None
            payload["projection_scale"] = projection_scale
        
        # Execute strategy
        result = orchestrator.execute_strategy(session_id, selected_strategy, payload)
        
        # Determine if session completed or more steps needed
        session = orchestrator.memory.get_session(session_id)
        is_complete = not next_thought_needed or thought_number >= (session.estimated_total_thoughts if session else estimated_total_thoughts)
        
        # Extract usage/financial telemetry (Attached by orchestrator transparency layer)
        usage = result.get("usage", {})
        
        return {
            "status": "success",
            "session_id": session_id,
            "thought_number": thought_number,
            "total_steps": session.estimated_total_thoughts if session else estimated_total_thoughts,
            "is_complete": is_complete,
            "strategy_used": selected_strategy.value,
            "thought_result": result,
            "financial_telemetry": usage.get("session_totals", {}),
            "token_economy": usage.get("token_economy", {}),
            "next_strategy": _get_strategy_pipeline(
                complexity, thought_number, last_clarity, last_coherence, category=category
            ).value if not is_complete else None
        }


    @mcp.tool()
    async def list_thinking(
        include_archived: bool = False,
        status_filter: str = "all"
    ) -> Dict[str, Any]:
        """
        [LIST_THINKING] List all cognitive thinking sessions with metadata.
        
        View all your thinking sessions, their status, complexity level, and progress.
        
        Args:
            include_archived: Include archived sessions
            status_filter: Filter by status - "all", "active", "completed", "awaiting_clearance"
            
        Returns:
            List of thinking sessions with metadata
            
        Example:
            {
                "sessions": [
                    {"id": "sess_abc", "status": "active", "steps": 3, "complexity": "moderate"}
                ],
                "total": 1,
                "active": 1
            }
        """
        sessions = orchestrator.memory.list_sessions()
        
        result_sessions = []
        total_active = 0
        total_awaiting = 0
        
        for sid in sessions:
            session = orchestrator.memory.get_session(sid)
            if not session:
                continue
                
            status = getattr(session, 'status', 'unknown')
            
            # Filter
            status_val = status.value if hasattr(status, 'value') else str(status)
            if status_filter != "all" and status_val != status_filter:
                continue
            
            if status == SessionStatus.ACTIVE:
                total_active += 1
            elif status == SessionStatus.AWAITING_HUMAN_CLEARANCE:
                total_awaiting += 1
            
            history = orchestrator.memory.get_session_history(sid)
            
            result_sessions.append({
                "id": sid,
                "status": status.value if hasattr(status, 'value') else str(status),
                "problem_summary": session.problem_statement[:50] + "..." if len(session.problem_statement) > 50 else session.problem_statement,
                "steps_completed": len(history),
                "total_cost_usd": getattr(session, 'total_cost_usd', 0),
                "total_cost_idr": getattr(session, 'total_cost_idr', 0),
                "profile": getattr(session, 'profile', 'balanced').value if hasattr(getattr(session, 'profile', None), 'value') else str(getattr(session, 'profile', 'balanced')),
                "complexity": getattr(session, 'complexity', 'unknown')
            })
        
        return {
            "sessions": result_sessions,
            "total": len(result_sessions),
            "active": total_active,
            "awaiting_clearance": total_awaiting
        }


    logger.info("Simplified Tools registered: thinking, rethinking, list_thinking")
