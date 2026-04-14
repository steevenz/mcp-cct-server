"""
Simplified CCT Tools - Hybrid Orchestration System

Ultra-simple 3-tool API with auto session management:
- thinking: Start new session + execute first thinking step automatically
- rethinking: Continue thinking from existing session (step 2, 3, etc.)
- list_thinking: List all thinking sessions with metadata

Now powered by a Hybrid Engine: 
Autonomous reasoning when LLM is set, Guided fallback otherwise.
"""
from __future__ import annotations
from typing import Any, Dict, Optional, List, Tuple
import logging
import time
from mcp.server.fastmcp import FastMCP

from src.core.models.enums import ThinkingStrategy, ThoughtType, CCTProfile, SessionStatus
from src.core.validators import validate_session_id, validate_thought_content, validate_problem_statement
from src.core.rate_limiter import rate_limited
from src.engines.orchestrator import CognitiveOrchestrator
from src.utils.pipelines import PipelineSelector

# New Services
from src.core.services.complexity import ComplexityService, TaskComplexity

logger = logging.getLogger(__name__)

def _get_strategy_pipeline(complexity: TaskComplexity, current_step: int, 
                           category: str = "GENERIC") -> ThinkingStrategy:
    """
    Determine next strategy based on category (templates) or fallback complexity.
    """
    # 1. SOVEREIGN/COMPLEX: Always use the Sovereign 8-Step Pipeline
    if complexity in {TaskComplexity.COMPLEX, TaskComplexity.SOVEREIGN}:
        pipeline = PipelineSelector.SOVEREIGN_PIPELINE
        if 0 <= current_step < len(pipeline):
            return pipeline[current_step]
        return ThinkingStrategy.MULTI_AGENT_FUSION
    
    # 2. Category-Based Template Logic (Moderate/Simple)
    if category != "GENERIC":
        template = PipelineSelector.PIPELINE_TEMPLATES.get(category, [])
        if template and 0 <= current_step < len(template):
            return template[current_step]
    
    # 3. Fallback Complexity-Based Logic
    if complexity == TaskComplexity.SIMPLE:
        if current_step == 0: return ThinkingStrategy.LINEAR
        if current_step == 1: return ThinkingStrategy.ANALYTICAL
        return ThinkingStrategy.INTEGRATIVE
    
    else:  # MODERATE Generic
        if current_step == 0: return ThinkingStrategy.EMPIRICAL_RESEARCH
        if current_step == 1: return ThinkingStrategy.FIRST_PRINCIPLES
        if current_step == 2: return ThinkingStrategy.SYSTEMIC
        return ThinkingStrategy.INTEGRATIVE


def register_simplified_tools(
    mcp: FastMCP, 
    orchestrator: CognitiveOrchestrator, 
    settings: Any,
    complexity_service: ComplexityService
):
    """
    Register simplified tools to MCP server.
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
        """
        start_time = time.time()
        
        if error := validate_problem_statement(problem_statement):
            return {"status": "error", "error": error}
        
        # Step 1: Detect complexity & category
        complexity = complexity_service.detect_complexity(problem_statement)
        primary_category = PipelineSelector.detect_category(problem_statement)
        categories = PipelineSelector.detect_categories(problem_statement)
        
        logger.info(f"[THINKING] New session - Complexity: {complexity.value}, Primary: {primary_category}")
        
        # Step 2: Create session
        try:
            profile_lower = profile.lower()
            profile_map = {
                "creative": CCTProfile.CREATIVE_FIRST,
                "critical": CCTProfile.CRITICAL_FIRST,
                "human_in_the_loop": CCTProfile.HUMAN_IN_THE_LOOP,
                "deep_recursive": CCTProfile.DEEP_RECURSIVE,
                "balanced": CCTProfile.BALANCED
            }
            profile_enum = profile_map.get(profile_lower, CCTProfile.BALANCED)
            
            # Select initial pipeline
            pipeline = PipelineSelector.select_pipeline(problem_statement, complexity.value)
            
            # Adjust estimated thoughts
            if estimated_thoughts <= 0:
                if complexity == TaskComplexity.SOVEREIGN: final_est = 10
                elif complexity == TaskComplexity.COMPLEX: final_est = 8
                elif complexity == TaskComplexity.MODERATE: final_est = 5
                else: final_est = 3
            else:
                final_est = estimated_thoughts
            
            session = orchestrator.memory.create_session(
                problem_statement=problem_statement,
                profile=profile_enum,
                estimated_thoughts=final_est,
                model_id=model_id if model_id else settings.default_model,
                complexity=complexity.value
            )
            session_id = session.session_id
            
            # Persist context
            session.detected_categories = categories
            session.primary_category = primary_category
            session.suggested_pipeline = pipeline
            orchestrator.memory.update_session(session)
            
        except Exception as e:
            logger.error(f"[THINKING] Failed to create session: {e}", exc_info=True)
            return {"status": "error", "error": f"Session creation failed: {str(e)}"}
        
        # Step 3: Execute first thinking step
        if not thought_content:
            thought_content = f"Initial analysis of: {problem_statement[:100]}..."
        
        try:
            strategy = _get_strategy_pipeline(complexity, 0, category=primary_category)
            logger.info(f"[THINKING] Step 1 using strategy: {strategy.value}")
            
            payload = {
                "thought_content": thought_content,
                "thought_type": ThoughtType.ANALYSIS,
                "strategy": strategy,
                "thought_number": 1,
                "estimated_total_thoughts": session.estimated_total_thoughts,
                "next_thought_needed": session.estimated_total_thoughts > 1
            }
            
            thought_result = await orchestrator.execute_strategy(session_id, strategy, payload)
            
            total_time = time.time() - start_time
            return {
                "status": "success",
                "session_id": session_id,
                "detected_complexity": complexity.value,
                "detected_category": primary_category,
                "steps": f"1/{session.estimated_total_thoughts}",
                "strategy_used": strategy.value,
                "thought_result": thought_result,
                "next_action": "Call rethinking with step=2",
                "processing_time": f"{total_time:.3f}s"
            }
            
        except Exception as e:
            logger.error(f"[THINKING] Step 1 failed: {e}", exc_info=True)
            return {
                "status": "partial_success",
                "session_id": session_id,
                "session_created": True,
                "step_1_error": str(e)
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
        critic_persona: str = "auto"
    ) -> Dict[str, Any]:
        """
        [RETHINKING] Continue thinking from existing session (step 2, 3, etc.)
        """
        if error := validate_session_id(session_id):
            return {"status": "error", "error": error}
        
        if error := validate_thought_content(thought_content):
            return {"status": "error", "error": error}
        
        session = orchestrator.memory.get_session(session_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        history = orchestrator.memory.get_session_history(session_id)
        complexity = TaskComplexity(getattr(session, 'complexity', 'simple'))
        category = getattr(session, 'primary_category', 'GENERIC')
        
        # Determine strategy
        if strategy.lower() == "auto":
            selected_strategy = _get_strategy_pipeline(
                complexity, 
                thought_number - 1,
                category=category
            )
        else:
            try:
                selected_strategy = ThinkingStrategy(strategy.lower())
            except ValueError:
                return {"error": f"Invalid strategy: {strategy}"}
        
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
        
        if selected_strategy == ThinkingStrategy.ACTOR_CRITIC_LOOP:
            payload["target_thought_id"] = history[-1].id if history else None
            payload["critic_persona"] = PipelineSelector.DOMAIN_PERSONAS.get(category, "Critical Reviewer") if critic_persona == "auto" else critic_persona
            
        elif selected_strategy == ThinkingStrategy.MULTI_AGENT_FUSION:
            payload["target_thought_id"] = history[-1].id if history else None
            # Default personas from domain
            detected = getattr(session, 'detected_categories', {category: 1.0})
            payload["personas"] = PipelineSelector.get_personas_for_domains(detected)
        
        result = await orchestrator.execute_strategy(session_id, selected_strategy, payload)
        
        is_complete = not next_thought_needed or thought_number >= session.estimated_total_thoughts
        
        return {
            "status": "success",
            "session_id": session_id,
            "thought_number": thought_number,
            "is_complete": is_complete,
            "strategy": selected_strategy.value,
            "thought_result": result
        }


    @mcp.tool()
    async def list_thinking(
        include_archived: bool = False,
        status_filter: str = "all"
    ) -> Dict[str, Any]:
        """
        [LIST_THINKING] List all cognitive thinking sessions with metadata.
        """
        sessions = orchestrator.memory.list_sessions()
        result_sessions = []
        
        for sid in sessions:
            session = orchestrator.memory.get_session(sid)
            if not session: continue
                
            status = getattr(session, 'status', SessionStatus.ACTIVE)
            history = orchestrator.memory.get_session_history(sid)
            
            result_sessions.append({
                "id": sid,
                "status": status.value if hasattr(status, 'value') else str(status),
                "summary": session.problem_statement[:60] + "...",
                "steps": f"{len(history)}/{session.estimated_total_thoughts}",
                "complexity": getattr(session, 'complexity', 'unknown')
            })
        
        return {"sessions": result_sessions, "total": len(result_sessions)}

    logger.info("Simplified Tools registered: thinking, rethinking, list_thinking")
