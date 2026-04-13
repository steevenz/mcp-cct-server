"""
Automatic Thinking Pattern Injector for Phase 0

Implements automatic injection of Golden Thinking Patterns and Anti-Patterns
into new sessions during initialization (Phase 0).

Reference: CODEBASE_ANALYSIS_REPORT.md Section 5 - Evolutionary Memory System
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.core.models.domain import GoldenThinkingPattern, AntiPattern
from src.engines.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


@dataclass
class InjectionResult:
    """Result of pattern injection operation."""
    patterns_injected: int
    anti_patterns_injected: int
    relevance_scores: Dict[str, float]
    injection_context: Dict[str, Any]


class PatternInjector:
    """
    Automatically injects relevant patterns into new cognitive sessions.
    
    Implements the "Pre-Computation Injection" feature from the Evolutionary
    Memory system, ensuring sessions start with relevant cognitive priors.
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        max_patterns: int = 5,
        min_relevance_score: float = 0.6,
        anti_pattern_threshold: float = 0.4,  # Lower threshold for "Immune System" sensitivity
        enable_anti_patterns: bool = True
    ):
        self.memory = memory_manager
        self.max_patterns = max_patterns
        self.min_relevance_score = min_relevance_score
        self.anti_pattern_threshold = anti_pattern_threshold
        self.enable_anti_patterns = enable_anti_patterns
        
    def inject_for_session(
        self,
        session_id: str,
        problem_statement: str,
        domain_keywords: Optional[List[str]] = None
    ) -> InjectionResult:
        """
        Automatically inject relevant patterns into a new session.
        
        Called during Phase 0 (Meta-Cognitive Routing) to provide
        cognitive starting points based on historical successes.
        
        Args:
            session_id: Target session ID
            problem_statement: The problem being solved
            domain_keywords: Optional domain-specific keywords
            
        Returns:
            InjectionResult with injection metrics
        """
        logger.info(
            f"[Pattern Injection] Phase 0 for session {session_id}: "
            f"Analyzing problem statement..."
        )
        
        # Extract keywords from problem statement
        keywords = domain_keywords or self._extract_keywords(problem_statement)
        
        # Retrieve relevant patterns
        patterns = self._select_relevant_patterns(problem_statement, keywords)
        
        # Retrieve relevant anti-patterns
        anti_patterns = []
        if self.enable_anti_patterns:
            anti_patterns = self._select_relevant_anti_patterns(problem_statement, keywords)
        
        # Calculate relevance scores
        relevance_scores = {}
        for p in patterns:
            score = self._calculate_relevance(p, problem_statement, keywords)
            relevance_scores[p.id] = score
        
        # Store injection metadata in session
        injection_context = {
            "trigger": "phase_0_auto_injection",
            "problem_keywords": keywords,
            "injection_timestamp": self._current_timestamp(),
            "patterns_selected": [p.id for p in patterns],
            "anti_patterns_selected": [ap.id for ap in anti_patterns],
            "relevance_scores": relevance_scores
        }
        
        # Log injection
        logger.info(
            f"[Pattern Injection] Injected {len(patterns)} patterns and "
            f"{len(anti_patterns)} anti-patterns into session {session_id}"
        )
        
        return InjectionResult(
            patterns_injected=len(patterns),
            anti_patterns_injected=len(anti_patterns),
            relevance_scores=relevance_scores,
            injection_context=injection_context
        )
    
    def _extract_keywords(self, problem_statement: str) -> List[str]:
        """Extract relevant keywords from problem statement."""
        # Simple keyword extraction - can be enhanced with NLP
        import re
        
        # Convert to lowercase and extract meaningful words
        text = problem_statement.lower()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because',
            'until', 'while', 'this', 'that', 'these', 'those'
        }
        
        # Extract words (alphanumeric, min 3 chars)
        words = re.findall(r'\b[a-z][a-z0-9_]{2,}\b', text)
        
        # Filter stop words and return unique keywords
        keywords = [w for w in words if w not in stop_words]
        return list(set(keywords))[:20]  # Limit to top 20 unique keywords
    
    def _select_relevant_patterns(
        self,
        problem_statement: str,
        keywords: List[str]
    ) -> List[GoldenThinkingPattern]:
        """Select most relevant thinking patterns for the problem."""
        # Get all available patterns from memory
        all_patterns = self._get_all_patterns()
        
        if not all_patterns:
            logger.warning("No thinking patterns available for injection")
            return []
        
        # Score each pattern for relevance
        scored_patterns = []
        for pattern in all_patterns:
            score = self._calculate_relevance(pattern, problem_statement, keywords)
            if score >= self.min_relevance_score:
                scored_patterns.append((pattern, score))
        
        # Sort by score (descending) and take top N
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        selected = [p for p, _ in scored_patterns[:self.max_patterns]]
        
        return selected
    
    def _select_relevant_anti_patterns(
        self,
        problem_statement: str,
        keywords: List[str]
    ) -> List[AntiPattern]:
        """Select relevant anti-patterns to prevent known failures."""
        # Get all anti-patterns
        all_anti_patterns = self._get_all_anti_patterns()
        
        if not all_anti_patterns:
            return []
        
        # Score and select
        scored_anti = []
        for ap in all_anti_patterns:
            score = self._calculate_anti_pattern_relevance(ap, problem_statement, keywords)
            if score >= self.anti_pattern_threshold:
                scored_anti.append((ap, score))
        
        scored_anti.sort(key=lambda x: x[1], reverse=True)
        return [ap for ap, _ in scored_anti[:3]]  # Limit to 3 anti-patterns
    
    def _calculate_relevance(
        self,
        pattern: GoldenThinkingPattern,
        problem_statement: str,
        keywords: List[str]
    ) -> float:
        """Calculate relevance score for a thinking pattern."""
        score = 0.0
        
        # Get pattern metadata
        pattern_content = getattr(pattern, 'content', '')
        pattern_tags = getattr(pattern, 'tags', [])
        pattern_strategy = getattr(pattern, 'strategy', '')
        
        # Keyword matching
        pattern_text = f"{pattern_content} {' '.join(pattern_tags)} {pattern_strategy}"
        pattern_text = pattern_text.lower()
        
        for keyword in keywords:
            if keyword in pattern_text:
                score += 0.2  # Each keyword match adds 0.2
        
        # Boost for high-quality patterns (golden patterns)
        is_golden = getattr(pattern, 'is_golden', False)
        if is_golden:
            score += 0.3
        
        # Boost for frequently used patterns
        usage_count = getattr(pattern, 'usage_count', 0)
        if usage_count > 5:
            score += 0.2
        elif usage_count > 2:
            score += 0.1
        
        # Normalize score (max 1.0)
        return min(score, 1.0)
    
    def _calculate_anti_pattern_relevance(
        self,
        anti_pattern: AntiPattern,
        problem_statement: str,
        keywords: List[str]
    ) -> float:
        """Calculate relevance for anti-pattern (higher = more likely to prevent failure)."""
        score = 0.0
        
        # Get anti-pattern metadata
        category = getattr(anti_pattern, 'category', '')
        context = getattr(anti_pattern, 'failure_context', '')
        
        # Match problem keywords with failure context
        context_text = f"{category} {context}".lower()
        
        for keyword in keywords:
            if keyword in context_text:
                score += 0.25
        
        # Boost for severe failures
        severity = getattr(anti_pattern, 'severity', 'medium')
        if severity == 'critical':
            score += 0.4
        elif severity == 'high':
            score += 0.2
        
        return min(score, 1.0)
    
    def _get_all_patterns(self) -> List[GoldenThinkingPattern]:
        """Retrieve all thinking patterns from memory."""
        try:
            # Query memory manager for patterns
            patterns_data = self.memory.get_all_thinking_patterns()
            
            # Convert to ThinkingPattern objects
            patterns = []
            for data in patterns_data:
                try:
                    pattern = GoldenThinkingPattern(**data)
                    patterns.append(pattern)
                except Exception as e:
                    logger.warning(f"Failed to parse pattern: {e}")
            
            return patterns
        except Exception as e:
            logger.error(f"Error retrieving patterns: {e}")
            return []
    
    def _get_all_anti_patterns(self) -> List[AntiPattern]:
        """Retrieve all anti-patterns from memory."""
        try:
            anti_patterns_data = self.memory.get_all_anti_patterns()
            
            anti_patterns = []
            for data in anti_patterns_data:
                try:
                    ap = AntiPattern(**data)
                    anti_patterns.append(ap)
                except Exception as e:
                    logger.warning(f"Failed to parse anti-pattern: {e}")
            
            return anti_patterns
        except Exception as e:
            logger.error(f"Error retrieving anti-patterns: {e}")
            return []
    
    def _current_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


def auto_inject_patterns(
    memory_manager: MemoryManager,
    session_id: str,
    problem_statement: str
) -> InjectionResult:
    """
    Convenience function for automatic pattern injection.
    
    Args:
        memory_manager: Memory manager instance
        session_id: Target session
        problem_statement: Problem being solved
        
    Returns:
        InjectionResult with injection metrics
    """
    injector = PatternInjector(memory_manager)
    return injector.inject_for_session(session_id, problem_statement)
