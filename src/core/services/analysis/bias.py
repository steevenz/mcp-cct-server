"""
Bias detection and enforcement domain module.
Provides token-efficient cognitive bias identification with caching and enforcement.

Implements the Bias Wall pattern from CCT v5.0 §6.B:
- Detects cognitive biases in generated thoughts
- Enforces automatic blocking/rewrite of biased content
- Provides bias mitigation strategies
"""
from __future__ import annotations

import functools
import re
from typing import List, Set, Tuple, Dict, Any, Optional
import logging

from src.core.models.analysis import BiasSeverity, BiasCheckResult, BiasEnforcementResult

logger = logging.getLogger(__name__)


# Compile patterns once for performance
_BIAS_PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    ("absolutist_language", re.compile(r'\b(always|never|must|cannot)\b', re.IGNORECASE), "absolutist_language"),
    ("overconfidence_language", re.compile(r'\b(obviously|clearly|certainly|undoubtedly)\b', re.IGNORECASE), "overconfidence_language"),
    ("generalization", re.compile(r'\b(everyone|no one|all|none)\b', re.IGNORECASE), "generalization"),
]

# Extended patterns for comprehensive detection
_EXTENDED_PATTERNS: List[Tuple[str, re.Pattern, str]] = _BIAS_PATTERNS + [
    ("certainty_bias", re.compile(r'\b(definitely|absolutely|guaranteed)\b', re.IGNORECASE), "certainty_bias"),
    ("extreme_language", re.compile(r'\b(extreme|impossible|perfect|worst|best|only)\b', re.IGNORECASE), "extreme_language"),
    ("emotional_appeal", re.compile(r'\b(terrible|amazing|shocking|outrageous|disaster)\b', re.IGNORECASE), "emotional_appeal"),
    ("confirmation_bias", re.compile(r'\b(proves?|confirms?|obviously shows)\b', re.IGNORECASE), "confirmation_bias"),
    ("availability_bias", re.compile(r'\b(recent|latest|news|heard that)\b', re.IGNORECASE), "availability_bias"),
]


def detect_bias_flags(text: str) -> list[str]:
    """
    Detect cognitive biases in text using single-pass compiled regex.
    Optimized for token efficiency with caching.
    """
    return list(detect_bias_flags_optimized(text, extended=False))


@functools.lru_cache(maxsize=512)
def detect_bias_flags_optimized(text: str, extended: bool = False) -> Tuple[str, ...]:
    """
    Cached single-pass bias detection.
    Returns tuple for hashability (cache key compatibility).

    Args:
        text: Input text to analyze
        extended: If True, use extended pattern set

    Returns:
        Tuple of detected bias flag strings
    """
    if not text:
        return ()

    patterns = _EXTENDED_PATTERNS if extended else _BIAS_PATTERNS
    found_flags: Set[str] = set()
    found_snippets: Set[str] = set()

    # Single pass: check all patterns against text
    lowered = text.lower()
    for name, pattern, flag in patterns:
        if flag in found_flags:
            continue
        match = pattern.search(lowered)
        if match:
            found_flags.add(flag)
            # Capture snippet (context around match)
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            found_snippets.add(text[start:end].strip())

    return tuple(sorted(found_flags))


def comprehensive_bias_check(text: str) -> BiasCheckResult:
    """
    Extended bias detection with severity assessment and suggestions.
    
    Returns BiasCheckResult with detailed analysis and mitigation suggestions.
    """
    flags = list(detect_bias_flags_optimized(text, extended=True))
    
    if not flags:
        return BiasCheckResult(
            has_bias=False,
            flags=[],
            severity=BiasSeverity.LOW,
            confidence=0.0,
            suggestions=[],
            original_snippets=[]
        )
    
    # Determine severity based on flags
    critical_flags = {"absolutist_language", "confirmation_bias"}
    high_flags = {"overconfidence_language", "extreme_language", "certainty_bias"}
    
    if any(f in critical_flags for f in flags):
        severity = BiasSeverity.CRITICAL
        confidence = 0.9
    elif any(f in high_flags for f in flags):
        severity = BiasSeverity.HIGH
        confidence = 0.75
    elif len(flags) >= 3:
        severity = BiasSeverity.MEDIUM
        confidence = 0.6
    else:
        severity = BiasSeverity.LOW
        confidence = 0.4
    
    # Generate suggestions based on detected flags
    suggestions = _generate_mitigation_suggestions(flags)
    
    # Extract snippets
    snippets = _extract_biased_snippets(text, flags)
    
    return BiasCheckResult(
        has_bias=True,
        flags=flags,
        severity=severity,
        confidence=confidence,
        suggestions=suggestions,
        original_snippets=snippets
    )


def _generate_mitigation_suggestions(flags: List[str]) -> List[str]:
    """Generate mitigation suggestions based on detected bias flags."""
    suggestions = []
    
    mitigation_map = {
        "absolutist_language": "Replace absolute terms ('always', 'never') with probabilistic language ('often', 'rarely', 'typically')",
        "overconfidence_language": "Add qualifiers and acknowledge uncertainty ('appears to', 'suggests', 'may indicate')",
        "generalization": "Specify scope or provide evidence for general claims",
        "certainty_bias": "Express confidence as degrees rather than absolutes",
        "extreme_language": "Use moderate language and provide balanced perspective",
        "emotional_appeal": "Focus on factual evidence rather than emotional language",
        "confirmation_bias": "Consider alternative explanations and counter-evidence",
        "availability_bias": "Reference comprehensive data rather than recent examples only"
    }
    
    for flag in flags:
        if flag in mitigation_map:
            suggestions.append(mitigation_map[flag])
    
    return suggestions


def _extract_biased_snippets(text: str, flags: List[str]) -> List[str]:
    """Extract text snippets that contain biased language."""
    snippets = []
    patterns = [p for p in _EXTENDED_PATTERNS if p[2] in flags]
    
    for name, pattern, flag in patterns:
        for match in pattern.finditer(text):
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            snippet = text[start:end].strip()
            if snippet not in snippets:
                snippets.append(snippet)
    
    return snippets[:5]  # Limit to 5 snippets


def has_critical_bias(text: str) -> bool:
    """
    Fast check for high-priority biases only.
    Useful for quick filtering before expensive operations.
    """
    lowered = text.lower()
    critical_patterns = [r'\balways\b', r'\bnever\b', r'\bobviously\b', r'\bdefinitely proves\b']
    return any(re.search(p, lowered) for p in critical_patterns)


class BiasWall:
    """
    Bias Wall: Enforcement mechanism for cognitive bias mitigation.
    
    Implements automatic blocking, flagging, and rewriting of biased thoughts.
    Integrates with the orchestrator for real-time bias enforcement.
    """
    
    def __init__(
        self,
        block_threshold: BiasSeverity = BiasSeverity.CRITICAL,
        rewrite_threshold: BiasSeverity = BiasSeverity.HIGH,
        enable_auto_rewrite: bool = True
    ):
        self.block_threshold = block_threshold
        self.rewrite_threshold = rewrite_threshold
        self.enable_auto_rewrite = enable_auto_rewrite
        self._stats = {
            "total_checked": 0,
            "blocked": 0,
            "rewritten": 0,
            "flagged": 0,
            "allowed": 0
        }
    
    def check_and_enforce(
        self,
        text: str,
        context: str = "thought",
        attempt_rewrite: bool = True
    ) -> BiasEnforcementResult:
        """
        Check text for biases and enforce appropriate action.
        
        Actions:
        - "blocked": Critical bias detected, content rejected
        - "rewritten": High bias detected, content auto-corrected
        - "flagged": Medium bias detected, content allowed with warning
        - "allowed": No significant bias, content approved
        """
        self._stats["total_checked"] += 1
        
        result = comprehensive_bias_check(text)
        
        if not result.has_bias:
            self._stats["allowed"] += 1
            return BiasEnforcementResult(
                action="allowed",
                original_text=text,
                final_text=text,
                bias_result=result,
                enforcement_message="No significant bias detected"
            )
        
        # Determine action based on severity
        if result.severity.value in [BiasSeverity.CRITICAL.value, BiasSeverity.HIGH.value]:
            if result.severity == BiasSeverity.CRITICAL or result.severity.value == BiasSeverity.CRITICAL.value:
                self._stats["blocked"] += 1
                return self._block_content(text, result, context)
            
            # HIGH severity - attempt rewrite if enabled
            if self.enable_auto_rewrite and attempt_rewrite:
                rewritten = self._rewrite_biased_content(text, result)
                self._stats["rewritten"] += 1
                return BiasEnforcementResult(
                    action="rewritten",
                    original_text=text,
                    final_text=rewritten,
                    bias_result=result,
                    enforcement_message=f"Bias detected ({', '.join(result.flags)}). Content automatically rewritten."
                )
            else:
                self._stats["flagged"] += 1
                return self._flag_content(text, result)
        
        # MEDIUM or LOW - flag but allow
        self._stats["flagged"] += 1
        return self._flag_content(text, result)
    
    def _block_content(
        self,
        text: str,
        bias_result: BiasCheckResult,
        context: str
    ) -> BiasEnforcementResult:
        """Block content due to critical bias."""
        message = (
            f"[BIAS WALL] {context} blocked due to critical bias: "
            f"{', '.join(bias_result.flags)}. "
            f"Suggestions: {'; '.join(bias_result.suggestions[:2])}"
        )
        logger.warning(message)
        
        return BiasEnforcementResult(
            action="blocked",
            original_text=text,
            final_text="[BLOCKED: Content violated Bias Wall policy]",
            bias_result=bias_result,
            enforcement_message=message
        )
    
    def _flag_content(self, text: str, bias_result: BiasCheckResult) -> BiasEnforcementResult:
        """Flag content but allow it through."""
        message = (
            f"[BIAS WALL] {context} flagged for bias: {', '.join(bias_result.flags)}. "
            f"Consider: {'; '.join(bias_result.suggestions[:2])}"
        )
        logger.info(message)
        
        # Add warning prefix to text
        flagged_text = f"[BIAS WARNING: {', '.join(bias_result.flags)}]\n\n{text}"
        
        return BiasEnforcementResult(
            action="flagged",
            original_text=text,
            final_text=flagged_text,
            bias_result=bias_result,
            enforcement_message=message
        )
    
    def _rewrite_biased_content(self, text: str, bias_result: BiasCheckResult) -> str:
        """
        Auto-rewrite content to reduce bias.
        Simple rule-based rewriting - in production, this would use LLM.
        """
        rewritten = text
        
        # Apply basic replacements
        replacements = {
            r'\balways\b': 'often',
            r'\bnever\b': 'rarely',
            r'\bobviously\b': 'appears to',
            r'\bclearly\b': 'suggests',
            r'\bdefinitely\b': 'likely',
            r'\babsolutely\b': 'generally',
            r'\bperfect\b': 'effective',
            r'\bimpossible\b': 'unlikely',
        }
        
        for pattern, replacement in replacements.items():
            rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
        
        # Add bias mitigation note
        rewritten = (
            f"[AUTO-CORRECTED for bias: {', '.join(bias_result.flags)}]\n\n"
            f"{rewritten}\n\n"
            f"[Note: Original contained potentially biased language. "
            f"Review suggestions: {'; '.join(bias_result.suggestions[:2])}]"
        )
        
        return rewritten
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bias enforcement statistics."""
        stats = self._stats.copy()
        if stats["total_checked"] > 0:
            stats["block_rate"] = round(stats["blocked"] / stats["total_checked"] * 100, 2)
            stats["rewrite_rate"] = round(stats["rewritten"] / stats["total_checked"] * 100, 2)
        return stats
    
    def reset_stats(self) -> None:
        """Reset bias enforcement statistics."""
        self._stats = {
            "total_checked": 0,
            "blocked": 0,
            "rewritten": 0,
            "flagged": 0,
            "allowed": 0
        }
