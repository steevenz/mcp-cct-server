"""
Complexity domain models.
"""
from enum import Enum


class TaskComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    SOVEREIGN = "sovereign"
