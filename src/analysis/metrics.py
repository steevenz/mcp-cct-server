"""
Metrics calculation domain module.
Provides token-efficient similarity and analysis with caching.
"""
from __future__ import annotations

import functools
import math
import random
import re
from collections import Counter
from typing import List, Tuple


# Compile regex once for performance
_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


@functools.lru_cache(maxsize=1024)
def _cached_tokenize(text: str) -> Tuple[str, ...]:
    """
    Cached tokenization to avoid re-processing same text.
    Returns tuple for hashability (required for cache key).
    """
    return tuple(_TOKEN_PATTERN.findall(text.lower()))


def _tokenize(text: str) -> list[str]:
    """Public interface - returns list for backward compatibility."""
    return list(_cached_tokenize(text))


@functools.lru_cache(maxsize=512)
def _cached_token_counts(text: str) -> Counter:
    """Cached token counter for cosine similarity."""
    return Counter(_cached_tokenize(text))


def cosine_similarity(a: str, b: str) -> float:
    """
    Calculate cosine similarity between two texts.
    Uses cached tokenization for O(1) lookup on repeated texts.
    """
    a_counts = _cached_token_counts(a)
    b_counts = _cached_token_counts(b)

    if not a_counts or not b_counts:
        return 0.0

    # Fast path: if identical token sets
    if a_counts == b_counts:
        return 1.0

    # Calculate dot product only for common tokens (optimization)
    common_tokens = set(a_counts.keys()) & set(b_counts.keys())
    if not common_tokens:
        return 0.0

    dot = sum(float(a_counts[t]) * float(b_counts[t]) for t in common_tokens)

    norm_a = math.sqrt(sum(float(v * v) for v in a_counts.values()))
    norm_b = math.sqrt(sum(float(v * v) for v in b_counts.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def sample_based_novelty(text: str, history: List[str], sample_size: int = 10) -> float:
    """
    Approximate novelty using sampling for large histories.
    Instead of O(n) comparison with all history, sample recent thoughts.

    Args:
        text: New thought content
        history: List of previous thought contents
        sample_size: Number of recent thoughts to compare

    Returns:
        Novelty score [0.0, 1.0], higher = more novel
    """
    if not history:
        return 1.0

    # Sample recent thoughts + some from older history
    if len(history) <= sample_size:
        sample = history
    else:
        # Always include most recent 5, sample 5 from rest
        recent = history[-5:]
        older = history[:-5]
        sampled_older = random.sample(older, min(5, len(older)))
        sample = recent + sampled_older

    # Find max similarity with sampled set
    max_sim = 0.0
    text_tokens = set(_cached_tokenize(text))

    for prev in sample:
        # Quick pre-filter: if token sets are very different, skip calculation
        prev_tokens = set(_cached_tokenize(prev))
        if len(text_tokens & prev_tokens) < 2:  # Very different
            continue

        sim = cosine_similarity(text, prev)
        max_sim = max(max_sim, sim)

    return 1.0 - max_sim
