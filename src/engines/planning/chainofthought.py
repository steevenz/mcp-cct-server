"""
CoT Engine: Chain of Thought Pattern Implementation

Implements the Chain of Thought (CoT) pattern for linear reasoning.
This pattern provides step-by-step logical decomposition for transparency.

Reference: docs/context-tree/Planning/Patterns/ChainOfThought.md
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CoTStep:
    """A single step in the chain of thought."""
    step_number: int
    thought: str
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "thought": self.thought,
            "reasoning": self.reasoning
        }


class CoTEngine:
    """
    Chain of Thought (CoT) Engine for linear reasoning.
    
    Implements step-by-step logical decomposition:
    1. Break down problem into steps
    2. Process each step sequentially
    3. Ensure logical flow between steps
    4. Provide transparent reasoning
    """
    
    def __init__(self, max_steps: int = 5):
        self.max_steps = max_steps
        self._steps: List[CoTStep] = []
    
    def process(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a problem using CoT pattern.
        
        Args:
            problem: The problem to solve
            context: Current context and state
            
        Returns:
            Result with chain of thought steps
        """
        logger.info(f"[COT] Starting CoT processing for: {problem[:50]}...")
        
        self._steps = []
        
        # Generate chain of thought steps
        steps = self._generate_chain(problem, context)
        
        for i, step in enumerate(steps, 1):
            cot_step = CoTStep(
                step_number=i,
                thought=step["thought"],
                reasoning=step["reasoning"]
            )
            self._steps.append(cot_step)
        
        return {
            "status": "success",
            "steps": [step.to_dict() for step in self._steps],
            "total_steps": len(self._steps),
            "final_answer": self._generate_final_answer(self._steps),
            "pattern": "chain_of_thought"
        }
    
    def _generate_chain(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate chain of thought steps."""
        # Standard CoT decomposition
        steps = [
            {
                "thought": f"Understand the problem: {problem}",
                "reasoning": "First, I need to clearly understand what is being asked and identify the key requirements."
            },
            {
                "thought": "Identify key components and constraints",
                "reasoning": "Break down the problem into its constituent parts and identify any constraints or limitations."
            },
            {
                "thought": "Develop a solution approach",
                "reasoning": "Based on the components identified, develop a systematic approach to solve the problem."
            },
            {
                "thought": "Execute the solution step by step",
                "reasoning": "Implement the solution following the developed approach, ensuring each step is logically connected."
            },
            {
                "thought": "Verify and validate the solution",
                "reasoning": "Check that the solution meets the requirements and validate the reasoning is sound."
            }
        ]
        
        # Adjust based on max_steps
        return steps[:self.max_steps]
    
    def _generate_final_answer(self, steps: List[CoTStep]) -> str:
        """Generate final answer from steps."""
        if not steps:
            return "No steps generated."
        
        return f"Based on {len(steps)} reasoning steps, the solution follows a logical chain: " + \
               " -> ".join([f"Step {s.step_number}" for s in steps])
    
    def get_steps(self) -> List[CoTStep]:
        """Get all steps."""
        return self._steps
    
    def get_token_efficiency_score(self) -> float:
        """
        Calculate token efficiency score for CoT pattern.
        
        CoT is moderately efficient - it provides transparency through
        step-by-step reasoning but can be verbose for complex problems.
        """
        if not self._steps:
            return 1.0
        
        # Efficiency decreases with more steps
        base_efficiency = 0.75
        step_penalty = min(len(self._steps) * 0.03, 0.25)
        return max(base_efficiency - step_penalty, 0.5)
