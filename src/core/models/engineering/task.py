"""
Task Decomposition Domain Models

Domain models for the 15-minute rule task decomposition workflow.
"""
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field


class TaskComplexityLevel(str, Enum):
    """Complexity level of a task."""
    SIMPLE = "simple"  # < 15 minutes
    MODERATE = "moderate"  # 15-30 minutes
    COMPLEX = "complex"  # 30-60 minutes
    SOVEREIGN = "sovereign"  # > 60 minutes


@dataclass
class TaskUnit:
    """A single agent-sized task unit."""
    id: str
    description: str
    estimated_minutes: int
    dependencies: List[str] = field(default_factory=list)
    verification_criteria: List[str] = field(default_factory=list)
    dominant_risk: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, blocked
    
    def is_agent_sized(self) -> bool:
        """Check if task is within 15-minute rule."""
        return self.estimated_minutes <= 15


@dataclass
class DecompositionPlan:
    """Complete task decomposition plan."""
    original_task: str
    units: List[TaskUnit] = field(default_factory=list)
    total_estimated_minutes: int = 0
    critical_path: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if all units are agent-sized."""
        return all(unit.is_agent_sized() for unit in self.units)
    
    def get_next_unit(self) -> Optional[TaskUnit]:
        """Get next pending unit respecting dependencies."""
        completed_ids = {unit.id for unit in self.units if unit.status == "completed"}
        
        for unit in self.units:
            if unit.status == "pending":
                # Check if dependencies are met
                if all(dep in completed_ids for dep in unit.dependencies):
                    return unit
        
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "original_task": self.original_task,
            "total_units": len(self.units),
            "total_estimated_minutes": self.total_estimated_minutes,
            "is_valid": self.is_valid(),
            "critical_path": self.critical_path,
            "units": [
                {
                    "id": unit.id,
                    "description": unit.description,
                    "estimated_minutes": unit.estimated_minutes,
                    "dependencies": unit.dependencies,
                    "verification_criteria": unit.verification_criteria,
                    "dominant_risk": unit.dominant_risk,
                    "status": unit.status,
                    "is_agent_sized": unit.is_agent_sized()
                }
                for unit in self.units
            ]
        }
