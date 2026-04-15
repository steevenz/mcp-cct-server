"""
ReAct Engine: Reason + Act Pattern Implementation

Implements the ReAct (Reason + Act) pattern for adaptive task execution.
This pattern uses a thought-action-observation loop for dynamic reasoning.

Reference: docs/context-tree/Planning/Patterns/ReAct.md
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReActStep:
    """A single ReAct step."""
    thought: str
    action: str
    observation: str
    step_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "step_number": self.step_number
        }


class ReActEngine:
    """
    ReAct (Reason + Act) Engine for adaptive task execution.
    
    Implements a dynamic loop of:
    1. Thought: Reason about current state
    2. Action: Decide on next action
    3. Observation: Observe result and update state
    """
    
    def __init__(self, max_steps: int = 10):
        self.max_steps = max_steps
        self._steps: List[ReActStep] = []
    
    def process(
        self,
        problem: str,
        context: Dict[str, Any],
        available_actions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a problem using ReAct pattern.
        
        Args:
            problem: The problem to solve
            context: Current context and state
            available_actions: List of available actions/tools
            
        Returns:
            Result with steps and final answer
        """
        logger.info(f"[REACT] Starting ReAct processing for: {problem[:50]}...")
        
        self._steps = []
        current_context = context.copy()
        
        for step_num in range(1, self.max_steps + 1):
            # Step 1: Thought - Reason about current state
            thought = self._generate_thought(problem, current_context, step_num)
            
            # Step 2: Action - Decide on next action
            action = self._decide_action(thought, available_actions, current_context)
            
            # Step 3: Observation - Would observe result (simulated)
            observation = self._simulate_observation(action, current_context)
            
            # Record step
            step = ReActStep(
                thought=thought,
                action=action,
                observation=observation,
                step_number=step_num
            )
            self._steps.append(step)
            
            # Update context with observation
            current_context["last_observation"] = observation
            current_context["step_number"] = step_num
            
            # Check if done
            if self._should_stop(observation, step_num):
                logger.info(f"[REACT] Converged at step {step_num}")
                break
        
        return {
            "status": "success",
            "steps": [step.to_dict() for step in self._steps],
            "total_steps": len(self._steps),
            "final_context": current_context,
            "pattern": "react"
        }
    
    def _generate_thought(
        self,
        problem: str,
        context: Dict[str, Any],
        step_number: int
    ) -> str:
        """Generate thought for current step."""
        if step_number == 1:
            return f"Initial analysis of problem: {problem}. Need to understand requirements and available context."
        else:
            last_obs = context.get("last_observation", "No observation yet")
            return f"Based on previous observation: {last_obs}. Determine next action."
    
    def _decide_action(
        self,
        thought: str,
        available_actions: Optional[List[str]],
        context: Dict[str, Any]
    ) -> str:
        """Decide on next action based on thought."""
        if available_actions:
            # Simple heuristic: pick first available action
            # In production, this would use LLM to decide
            return available_actions[0] if available_actions else "continue"
        return "analyze"
    
    def _simulate_observation(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> str:
        """Simulate observation for given action."""
        return f"Executed action: {action}. Result: Action completed successfully."
    
    def _should_stop(self, observation: str, step_number: int) -> bool:
        """Determine if should stop processing."""
        # Stop if observation indicates completion or max steps reached
        stop_keywords = ["completed", "finished", "done", "success"]
        return any(keyword in observation.lower() for keyword in stop_keywords)
    
    def get_steps(self) -> List[ReActStep]:
        """Get all steps."""
        return self._steps
    
    def get_token_efficiency_score(self) -> float:
        """
        Calculate token efficiency score for ReAct pattern.
        
        ReAct is moderately efficient - it balances reasoning with action,
        but can be verbose if many iterations are needed.
        """
        if not self._steps:
            return 1.0
        
        # Efficiency decreases with more steps
        base_efficiency = 0.8
        step_penalty = min(len(self._steps) * 0.02, 0.3)
        return max(base_efficiency - step_penalty, 0.5)
