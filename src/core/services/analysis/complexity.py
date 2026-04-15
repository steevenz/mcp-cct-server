import re
from typing import Set

from src.core.models.analysis import TaskComplexity

class ComplexityService:
    """
    Domain service for determining task complexity based on problem statement heuristics.
    """
    
    COMPLEX_KEYWORDS: Set[str] = {
        "architecture", "design", "refactor", "optimize", "security", 
        "audit", "complex", "system", "infrastructure", "deployment",
        "scale", "migration", "integration", "enterprise", "performance",
        "bottleneck", "vulnerability", "threat", "hardening", "forensic"
    }
    
    SOVEREIGN_KEYWORDS: Set[str] = {
        "production", "critical", "military-grade", "government", 
        "financial", "bank", "high-stakes", "mission-critical"
    }

    def detect_complexity(self, problem_statement: str) -> TaskComplexity:
        """
        Heuristic-based complexity detection.
        """
        text = problem_statement.lower()
        
        # Word count as a basic indicator
        words = re.findall(r'\w+', text)
        word_count = len(words)
        
        # Keyword matches
        complex_hits = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in text)
        sovereign_hits = sum(1 for kw in self.SOVEREIGN_KEYWORDS if kw in text)
        
        if sovereign_hits >= 1 or (word_count > 150 and complex_hits >= 5):
            return TaskComplexity.SOVEREIGN
            
        if complex_hits >= 3 or word_count > 80:
            return TaskComplexity.COMPLEX
            
        if complex_hits >= 1 or word_count > 30:
            return TaskComplexity.MODERATE
            
        return TaskComplexity.SIMPLE
