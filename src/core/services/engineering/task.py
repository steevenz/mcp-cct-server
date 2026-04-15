"""
Task Decomposition Service: 15-Minute Rule for Engineering Tasks

Implements the CCT v5.0 Engineering Domain requirement for breaking complex tasks
into agent-sized units that can be executed and verified within 15 minutes.

Reference: docs/context-tree/Engineering/Workflows/TaskDecomposition.md
"""
import logging
from typing import Dict, Any, Optional, List

from src.core.models.engineering.task import (
    TaskComplexityLevel,
    TaskUnit,
    DecompositionPlan
)

logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for decomposing complex tasks into 15-minute agent-sized units.
    
    Implements the Lego Principle: all engineering work must be deconstructed
    into independently verifiable, single-risk units.
    """
    
    def __init__(self):
        self._decomposition_store: Dict[str, DecompositionPlan] = {}
    
    def analyze_task_complexity(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskComplexityLevel:
        """
        Analyze task complexity based on description.
        
        Args:
            task_description: The task to analyze
            context: Additional context (files, dependencies, etc.)
            
        Returns:
            Complexity level estimate
        """
        # Heuristic analysis based on keywords and structure
        text = task_description.lower()
        
        # Count complexity indicators
        complexity_indicators = {
            "multi-file": ["file", "module", "component", "service"],
            "multi-system": ["api", "database", "integration", "system"],
            "architectural": ["design", "architecture", "structure", "schema"],
            "complex_logic": ["algorithm", "optimization", "performance"],
            "security": ["security", "auth", "encryption", "vulnerability"]
        }
        
        score = 0
        for category, keywords in complexity_indicators.items():
            matches = sum(1 for kw in keywords if kw in text)
            if category == "multi-file":
                score += matches * 2
            elif category == "multi-system":
                score += matches * 3
            elif category == "architectural":
                score += matches * 4
            else:
                score += matches
        
        # Map score to complexity level
        if score >= 15:
            return TaskComplexityLevel.SOVEREIGN
        elif score >= 10:
            return TaskComplexityLevel.COMPLEX
        elif score >= 5:
            return TaskComplexityLevel.MODERATE
        else:
            return TaskComplexityLevel.SIMPLE
    
    def decompose_task(
        self,
        session_id: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DecompositionPlan:
        """
        Decompose a task into agent-sized units.
        
        Args:
            session_id: Session identifier
            task_description: The task to decompose
            context: Additional context
            
        Returns:
            Decomposition plan with task units
        """
        complexity = self.analyze_task_complexity(task_description, context)
        
        if complexity == TaskComplexityLevel.SIMPLE:
            # Simple task doesn't need decomposition
            plan = DecompositionPlan(
                original_task=task_description,
                units=[
                    TaskUnit(
                        id="unit_1",
                        description=task_description,
                        estimated_minutes=10,
                        verification_criteria=["Task completed successfully"],
                        dominant_risk="None"
                    )
                ],
                total_estimated_minutes=10
            )
        else:
            # Complex task needs decomposition
            plan = self._generate_decomposition_plan(task_description, complexity)
        
        self._decomposition_store[session_id] = plan
        
        logger.info(
            f"[TASK-DECOMP] Decomposed task for session {session_id}: "
            f"{len(plan.units)} units, {plan.total_estimated_minutes} minutes total"
        )
        
        return plan
    
    def _generate_decomposition_plan(
        self,
        task_description: str,
        complexity: TaskComplexityLevel
    ) -> DecompositionPlan:
        """
        Generate a decomposition plan based on complexity.
        
        This is a heuristic-based generator. In production, this would use
        LLM-powered decomposition for more accurate results.
        """
        # Estimate number of units based on complexity
        unit_counts = {
            TaskComplexityLevel.MODERATE: 3,
            TaskComplexityLevel.COMPLEX: 6,
            TaskComplexityLevel.SOVEREIGN: 10
        }
        
        num_units = unit_counts.get(complexity, 1)
        
        # Generate heuristic units (in production, use LLM)
        units = []
        for i in range(num_units):
            unit_id = f"unit_{i + 1}"
            dependencies = [f"unit_{j}" for j in range(i)]
            
            unit = TaskUnit(
                id=unit_id,
                description=f"Sub-task {i + 1} of: {task_description[:50]}...",
                estimated_minutes=15,  # All units target 15-minute rule
                dependencies=dependencies,
                verification_criteria=[f"Unit {i + 1} verification criteria"],
                dominant_risk=f"Risk factor for unit {i + 1}"
            )
            units.append(unit)
        
        # Calculate critical path (simple heuristic: all units)
        critical_path = [unit.id for unit in units]
        
        return DecompositionPlan(
            original_task=task_description,
            units=units,
            total_estimated_minutes=sum(unit.estimated_minutes for unit in units),
            critical_path=critical_path
        )
    
    def get_decomposition_plan(self, session_id: str) -> Optional[DecompositionPlan]:
        """Get decomposition plan for a session."""
        return self._decomposition_store.get(session_id)
    
    def get_next_task(self, session_id: str) -> Optional[TaskUnit]:
        """Get next task to execute respecting dependencies."""
        plan = self._decomposition_store.get(session_id)
        if not plan:
            return None
        return plan.get_next_unit()
    
    def update_task_status(
        self,
        session_id: str,
        unit_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Update status of a task unit.
        
        Args:
            session_id: Session identifier
            unit_id: Task unit identifier
            status: New status (pending, in_progress, completed, blocked)
            
        Returns:
            Update result
        """
        plan = self._decomposition_store.get(session_id)
        if not plan:
            return {
                "status": "error",
                "message": f"No decomposition plan found for session {session_id}"
            }
        
        unit = next((u for u in plan.units if u.id == unit_id), None)
        if not unit:
            return {
                "status": "error",
                "message": f"Task unit {unit_id} not found"
            }
        
        unit.status = status
        
        logger.info(
            f"[TASK-DECOMP] Updated unit {unit_id} to {status} "
            f"for session {session_id}"
        )
        
        return {
            "status": "success",
            "unit_id": unit_id,
            "new_status": status,
            "plan": plan.to_dict()
        }
    
    def validate_decomposition(self, session_id: str) -> Dict[str, Any]:
        """
        Validate that decomposition follows 15-minute rule.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Validation result
        """
        plan = self._decomposition_store.get(session_id)
        if not plan:
            return {
                "status": "error",
                "message": "No decomposition plan found"
            }
        
        violations = [
            unit for unit in plan.units
            if not unit.is_agent_sized()
        ]
        
        if violations:
            return {
                "status": "invalid",
                "message": f"Found {len(violations)} units exceeding 15-minute rule",
                "violations": [
                    {
                        "id": unit.id,
                        "estimated_minutes": unit.estimated_minutes
                    }
                    for unit in violations
                ]
            }
        
        return {
            "status": "valid",
            "message": "All units comply with 15-minute rule",
            "plan": plan.to_dict()
        }
    
    def generate_decomposition_prompt(self, task_description: str) -> str:
        """
        Generate a prompt for LLM-powered task decomposition.
        
        Args:
            task_description: The task to decompose
            
        Returns:
            Prompt text for decomposition
        """
        return f"""
Decompose the following task into agent-sized units following the 15-Minute Rule:

Task: {task_description}

Requirements:
1. Each unit should be completable within 15 minutes
2. Each unit must have clear verification criteria
3. Identify dependencies between units
4. Specify the dominant risk for each unit
5. Order units to respect dependencies

Format your response as a structured list of units with:
- id: unit_1, unit_2, etc.
- description: Clear task description
- estimated_minutes: Target 15 minutes
- dependencies: List of unit IDs this depends on
- verification_criteria: How to verify completion
- dominant_risk: Primary risk factor
"""
