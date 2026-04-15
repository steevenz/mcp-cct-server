"""
Engineering Tools: Eval-First and Task Decomposition MCP Tools

Implements the CCT v5.0 Engineering Domain workflows:
- Eval-First: Enforce "No Code Without Criteria"
- Task Decomposition: 15-minute rule for complex tasks

Reference: docs/context-tree/Engineering/Workflows/
"""
from typing import Dict, Any, Optional, List
from mcp.server.fastmcp import FastMCP
import logging

logger = logging.getLogger(__name__)


def register_engineering_tools(
    mcp: FastMCP,
    orchestrator: Any
):
    """
    Register engineering workflow tools to MCP server.
    
    Args:
        mcp: FastMCP instance
        orchestrator: CognitiveOrchestrator instance with eval_first and task_decomposition services
    """
    
    @mcp.tool()
    def define_eval_criteria(
        session_id: str,
        capability_evals: List[str],
        regression_evals: List[str],
        success_metrics: List[str],
        baseline_snapshot: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Define evaluation criteria before implementation (Eval-First Protocol).
        
        Enforces the "No Code Without Criteria" rule for engineering tasks.
        All three criteria types must be defined before implementation can proceed.
        
        Args:
            session_id: The cognitive session ID
            capability_evals: What specific functionality must work? (Testable requirements)
            regression_evals: What existing functionality must not break? (Dependency checks)
            success_metrics: How do we measure success? (Quantitative metrics)
            baseline_snapshot: Optional current state snapshot for regression comparison
            
        Returns:
            Result with eval status and criteria confirmation
        """
        if not orchestrator.eval_first_service:
            return {
                "status": "error",
                "message": "EvalFirstService not initialized"
            }
        
        result = orchestrator.eval_first_service.define_criteria(
            session_id=session_id,
            capability_evals=capability_evals,
            regression_evals=regression_evals,
            success_metrics=success_metrics,
            baseline_snapshot=baseline_snapshot
        )
        
        logger.info(
            f"[ENGINEERING-TOOLS] Defined eval criteria for session {session_id}: "
            f"{result.get('eval_status')}"
        )
        
        return result
    
    @mcp.tool()
    def check_eval_status(session_id: str) -> Dict[str, Any]:
        """
        Check evaluation criteria status for a session.
        
        Use this to verify whether criteria are complete before attempting implementation.
        
        Args:
            session_id: The cognitive session ID
            
        Returns:
            Current eval status (not_defined, partial, complete, validated)
        """
        if not orchestrator.eval_first_service:
            return {
                "status": "error",
                "message": "EvalFirstService not initialized"
            }
        
        status = orchestrator.eval_first_service.check_eval_status(session_id)
        criteria = orchestrator.eval_first_service.get_criteria(session_id)
        
        return {
            "status": "success",
            "session_id": session_id,
            "eval_status": status.value,
            "criteria": criteria.to_dict() if criteria else None
        }
    
    @mcp.tool()
    def validate_for_implementation(session_id: str) -> Dict[str, Any]:
        """
        Validate that evaluation criteria are met before allowing implementation.
        
        This is the gatekeeper function that enforces the Eval-First protocol.
        Returns allow_implementation flag that must be checked before code generation.
        
        Args:
            session_id: The cognitive session ID
            
        Returns:
            Validation result with allow_implementation flag
        """
        if not orchestrator.eval_first_service:
            return {
                "status": "error",
                "message": "EvalFirstService not initialized"
            }
        
        result = orchestrator.eval_first_service.validate_before_implementation(session_id)
        
        logger.info(
            f"[ENGINEERING-TOOLS] Validated implementation for session {session_id}: "
            f"allow={result.get('allow_implementation')}"
        )
        
        return result
    
    @mcp.tool()
    def decompose_task(
        session_id: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Decompose a complex task into 15-minute agent-sized units.
        
        Implements the Lego Principle: break complex engineering tasks into
        independently verifiable units that can be completed within 15 minutes.
        
        Args:
            session_id: The cognitive session ID
            task_description: The task to decompose
            context: Additional context (files, dependencies, etc.)
            
        Returns:
            Decomposition plan with task units, dependencies, and verification criteria
        """
        if not orchestrator.task_decomposition_service:
            return {
                "status": "error",
                "message": "TaskDecompositionService not initialized"
            }
        
        plan = orchestrator.task_decomposition_service.decompose_task(
            session_id=session_id,
            task_description=task_description,
            context=context
        )
        
        logger.info(
            f"[ENGINEERING-TOOLS] Decomposed task for session {session_id}: "
            f"{len(plan.units)} units, {plan.total_estimated_minutes} minutes"
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "decomposition": plan.to_dict()
        }
    
    @mcp.tool()
    def get_next_task(session_id: str) -> Dict[str, Any]:
        """
        Get the next task unit to execute respecting dependencies.
        
        Use this to iterate through decomposed tasks in the correct order.
        
        Args:
            session_id: The cognitive session ID
            
        Returns:
            Next task unit or None if all tasks are completed
        """
        if not orchestrator.task_decomposition_service:
            return {
                "status": "error",
                "message": "TaskDecompositionService not initialized"
            }
        
        unit = orchestrator.task_decomposition_service.get_next_task(session_id)
        
        if unit:
            return {
                "status": "success",
                "session_id": session_id,
                "next_task": {
                    "id": unit.id,
                    "description": unit.description,
                    "estimated_minutes": unit.estimated_minutes,
                    "dependencies": unit.dependencies,
                    "verification_criteria": unit.verification_criteria,
                    "dominant_risk": unit.dominant_risk
                }
            }
        else:
            return {
                "status": "success",
                "session_id": session_id,
                "message": "All tasks completed or no decomposition plan found",
                "next_task": None
            }
    
    @mcp.tool()
    def update_task_status(
        session_id: str,
        unit_id: str,
        task_status: str
    ) -> Dict[str, Any]:
        """
        Update the status of a task unit.
        
        Use this to mark tasks as in_progress, completed, or blocked.
        
        Args:
            session_id: The cognitive session ID
            unit_id: The task unit identifier
            task_status: New status (pending, in_progress, completed, blocked)
            
        Returns:
            Update result with updated plan
        """
        if not orchestrator.task_decomposition_service:
            return {
                "status": "error",
                "message": "TaskDecompositionService not initialized"
            }
        
        result = orchestrator.task_decomposition_service.update_task_status(
            session_id=session_id,
            unit_id=unit_id,
            status=task_status
        )
        
        logger.info(
            f"[ENGINEERING-TOOLS] Updated task {unit_id} to {task_status} "
            f"for session {session_id}"
        )
        
        return result
    
    @mcp.tool()
    def validate_decomposition(session_id: str) -> Dict[str, Any]:
        """
        Validate that decomposition follows the 15-minute rule.
        
        Use this to ensure all task units are within the 15-minute constraint.
        
        Args:
            session_id: The cognitive session ID
            
        Returns:
            Validation result with any violations
        """
        if not orchestrator.task_decomposition_service:
            return {
                "status": "error",
                "message": "TaskDecompositionService not initialized"
            }
        
        result = orchestrator.task_decomposition_service.validate_decomposition(session_id)
        
        return result
    
    @mcp.tool()
    def get_decomposition_plan(session_id: str) -> Dict[str, Any]:
        """
        Get the complete decomposition plan for a session.
        
        Args:
            session_id: The cognitive session ID
            
        Returns:
            Complete decomposition plan with all units
        """
        if not orchestrator.task_decomposition_service:
            return {
                "status": "error",
                "message": "TaskDecompositionService not initialized"
            }
        
        plan = orchestrator.task_decomposition_service.get_decomposition_plan(session_id)
        
        if plan:
            return {
                "status": "success",
                "session_id": session_id,
                "plan": plan.to_dict()
            }
        else:
            return {
                "status": "success",
                "session_id": session_id,
                "message": "No decomposition plan found for this session",
                "plan": None
            }
    
    @mcp.tool()
    def start_human_orchestration(
        session_id: str,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Start a human orchestration session (Delegate-Review-Own model).
        
        Initiates the structured human-AI collaboration workflow:
        1. Delegate: AI performs implementation work
        2. Review: Human verifies output
        3. Own: Human confirms ownership of outcome
        
        Args:
            session_id: The cognitive session ID
            task_description: The task to orchestrate
            
        Returns:
            Orchestration session
        """
        if not orchestrator.human_orchestration_service:
            return {
                "status": "error",
                "message": "HumanOrchestrationService not initialized"
            }
        
        result = orchestrator.human_orchestration_service.start_orchestration(
            session_id=session_id,
            task_description=task_description
        )
        
        logger.info(
            f"[ENGINEERING-TOOLS] Started human orchestration for session {session_id}"
        )
        
        return result
    
    @mcp.tool()
    def submit_delegate_output(
        session_id: str,
        delegate_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit AI delegate output for human review.
        
        Use this after AI completes the DELEGATE phase to transition to REVIEW phase.
        
        Args:
            session_id: The orchestration session ID
            delegate_output: Output from AI delegate (implementation, tests, docs)
            
        Returns:
            Result with session updated to REVIEW phase
        """
        if not orchestrator.human_orchestration_service:
            return {
                "status": "error",
                "message": "HumanOrchestrationService not initialized"
            }
        
        result = orchestrator.human_orchestration_service.submit_delegate_output(
            session_id=session_id,
            delegate_output=delegate_output
        )
        
        logger.info(
            f"[ENGINEERING-TOOLS] Delegate output submitted for session {session_id}"
        )
        
        return result
    
    @mcp.tool()
    def submit_human_review(
        session_id: str,
        review_feedback: str,
        review_status: str
    ) -> Dict[str, Any]:
        """
        Submit human review feedback.
        
        Args:
            session_id: The session identifier
            review_feedback: Human review feedback
            review_status: Review decision (approved, rejected, revision_requested)
            
        Returns:
            Result with session updated based on review
        """
        # Human orchestration service removed per plan update
        return {
            "status": "error",
            "message": "Human orchestration service has been removed per architectural reorganization"
        }


def register_planning_tools(
    mcp: FastMCP,
    orchestrator: Any
):
    """
    Register planning pattern tools to MCP server.
    
    Args:
        mcp: FastMCP instance
        orchestrator: CognitiveOrchestrator instance
    """
    
    @mcp.tool()
    def execute_react(
        problem: str,
        context: Dict[str, Any],
        available_actions: Optional[List[str]] = None,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Execute problem using ReAct (Reason + Act) pattern.
        
        ReAct uses a thought-action-observation loop for adaptive task execution.
        
        Args:
            problem: The problem to solve
            context: Current context and state
            available_actions: List of available actions/tools
            max_steps: Maximum number of ReAct steps
            
        Returns:
            Result with steps and final answer
        """
        from src.engines.planning.react import ReActEngine
        
        engine = ReActEngine(max_steps=max_steps)
        result = engine.process(problem, context, available_actions)
        
        logger.info(f"[PLANNING-TOOLS] Executed ReAct pattern: {len(result['steps'])} steps")
        
        return result
    
    @mcp.tool()
    def execute_rewoo(
        problem: str,
        context: Dict[str, Any],
        available_actions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute problem using ReWOO (Reasoning Without Observation) pattern.
        
        ReWOO minimizes token calls by planning all actions upfront before execution.
        
        Args:
            problem: The problem to solve
            context: Current context and state
            available_actions: List of available actions/tools
            
        Returns:
            Result with reasoning, plan, and execution status
        """
        from src.engines.planning.rewoo import ReWOOEngine
        
        engine = ReWOOEngine()
        result = engine.process(problem, context, available_actions)
        
        logger.info(f"[PLANNING-TOOLS] Executed ReWOO pattern: {result['total_actions']} actions")
        
        return result
    
    @mcp.tool()
    def execute_tot(
        problem: str,
        context: Dict[str, Any],
        max_depth: int = 3,
        branch_factor: int = 3
    ) -> Dict[str, Any]:
        """
        Execute problem using Tree of Thoughts (ToT) pattern.
        
        ToT explores multiple reasoning paths simultaneously through branching.
        
        Args:
            problem: The problem to solve
            context: Current context and state
            max_depth: Maximum depth of thought tree
            branch_factor: Number of branches per node
            
        Returns:
            Result with thought tree and best path
        """
        from src.engines.planning.threeofthoughts import ToTEngine
        
        engine = ToTEngine(max_depth=max_depth, branch_factor=branch_factor)
        result = engine.process(problem, context)
        
        logger.info(
            f"[PLANNING-TOOLS] Executed ToT pattern: "
            f"{result['total_nodes']} nodes, depth {result['max_depth']}"
        )
        
        return result
    
    @mcp.tool()
    def execute_cot(
        problem: str,
        context: Dict[str, Any],
        max_steps: int = 5
    ) -> Dict[str, Any]:
        """
        Execute problem using Chain of Thought (CoT) pattern.
        
        CoT provides step-by-step logical decomposition for transparency.
        
        Args:
            problem: The problem to solve
            context: Current context and state
            max_steps: Maximum number of reasoning steps
            
        Returns:
            Result with chain of thought steps
        """
        from src.engines.planning.chainofthought import CoTEngine
        
        engine = CoTEngine(max_steps=max_steps)
        result = engine.process(problem, context)
        
        logger.info(f"[PLANNING-TOOLS] Executed CoT pattern: {result['total_steps']} steps")
        
        return result
    
    @mcp.tool()
    def compare_pattern_efficiency(
        problem: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare token efficiency of different planning patterns.
        
        Use this to select the most efficient pattern for your task.
        
        Args:
            problem: The problem to analyze
            context: Current context and state
            
        Returns:
            Comparison of efficiency scores for each pattern
        """
        from src.engines.planning.react import ReActEngine
        from src.engines.planning.rewoo import ReWOOEngine
        from src.engines.planning.threeofthoughts import ToTEngine
        from src.engines.planning.chainofthought import CoTEngine
        
        # Execute each pattern briefly to get efficiency scores
        react_engine = ReActEngine(max_steps=5)
        rewoo_engine = ReWOOEngine()
        tot_engine = ToTEngine(max_depth=2, branch_factor=2)
        cot_engine = CoTEngine(max_steps=3)
        
        react_engine.process(problem, context)
        rewoo_engine.process(problem, context)
        tot_engine.process(problem, context)
        cot_engine.process(problem, context)
        
        comparison = {
            "react": {
                "pattern": "ReAct (Reason + Act)",
                "description": "Adaptive execution with thought-action-observation loop",
                "efficiency_score": react_engine.get_token_efficiency_score(),
                "best_for": "Adaptive tasks requiring real-time adjustments"
            },
            "rewoo": {
                "pattern": "ReWOO (Reasoning Without Observation)",
                "description": "Upfront planning to minimize token calls",
                "efficiency_score": rewoo_engine.get_token_efficiency_score(),
                "best_for": "Well-defined tasks with predictable steps"
            },
            "tot": {
                "pattern": "Tree of Thoughts",
                "description": "Branching exploration of multiple paths",
                "efficiency_score": tot_engine.get_token_efficiency_score(),
                "best_for": "Complex problems requiring exploration of alternatives"
            },
            "cot": {
                "pattern": "Chain of Thought",
                "description": "Linear step-by-step reasoning for transparency",
                "efficiency_score": cot_engine.get_token_efficiency_score(),
                "best_for": "Problems requiring clear logical decomposition"
            }
        }
        
        # Sort by efficiency
        sorted_comparison = dict(
            sorted(comparison.items(), key=lambda x: x[1]["efficiency_score"], reverse=True)
        )
        
        logger.info("[PLANNING-TOOLS] Compared pattern efficiency")
        
        return {
            "status": "success",
            "comparison": sorted_comparison,
            "recommended": max(comparison.items(), key=lambda x: x[1]["efficiency_score"])[0]
        }
    
    logger.info("Planning pattern tools registered (ReAct, ReWOO, ToT, CoT)")
