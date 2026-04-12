"""
Bias detection domain module.
Provides token-efficient cognitive bias identification with caching.
"""
from __future__ import annotations

import functools
import re
from typing import List, Set, Tuple


# Compile patterns once for performance
_BIAS_PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    ("absolutist_language", re.compile(r'\b(always|never)\b', re.IGNORECASE), "absolutist_language"),
    ("overconfidence_language", re.compile(r'\b(obviously|clearly)\b', re.IGNORECASE), "overconfidence_language"),
    ("generalization", re.compile(r'\b(everyone|no one)\b', re.IGNORECASE), "generalization"),
]

# Extended patterns for comprehensive detection
_EXTENDED_PATTERNS: List[Tuple[str, re.Pattern, str]] = _BIAS_PATTERNS + [
    ("certainty_bias", re.compile(r'\b(definitely|certainly|undoubtedly)\b', re.IGNORECASE), "certainty_bias"),
    ("extreme_language", re.compile(r'\b(extreme|impossible|perfect|worst|best)\b', re.IGNORECASE), "extreme_language"),
    ("emotional_appeal", re.compile(r'\b(terrible|amazing|shocking|outrageous)\b', re.IGNORECASE), "emotional_appeal"),
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

    # Single pass: check all patterns against text
    lowered = text.lower()
    for name, pattern, flag in patterns:
        if flag in found_flags:
            continue
        if pattern.search(lowered):
            found_flags.add(flag)

    return tuple(sorted(found_flags))


def comprehensive_bias_check(text: str) -> list[str]:
    """Extended bias detection with more patterns."""
    return list(detect_bias_flags_optimized(text, extended=True))


def has_critical_bias(text: str) -> bool:
    """
    Fast check for high-priority biases only.
    Useful for quick filtering before expensive operations.
    """
    lowered = text.lower()
    critical_patterns = [r'\balways\b', r'\bnever\b', r'\bobviously\b']
    return any(re.search(p, lowered) for p in critical_patterns)
