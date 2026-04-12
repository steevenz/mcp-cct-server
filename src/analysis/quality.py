"""
Quality assessment domain module.
Provides token-efficient text clarity scoring with caching.
"""
from __future__ import annotations

import functools
import re
from typing import Tuple


# Compile regex once for performance
_TOKEN_PATTERN = re.compile(r"\w+")
_SENTENCE_PATTERN = re.compile(r"[.!?]")


@functools.lru_cache(maxsize=512)
def _cached_word_stats(text: str) -> Tuple[int, int, float]:
    """
    Cached word statistics for clarity score.
    Returns: (word_count, sentence_count, avg_words_per_sentence)
    """
    words = _TOKEN_PATTERN.findall(text)
    word_count = len(words)
    sentence_count = max(1, len(_SENTENCE_PATTERN.findall(text)))
    avg_words = word_count / sentence_count
    return word_count, sentence_count, avg_words


def clarity_score(text: str) -> float:
    """
    Calculate text clarity score using cached word statistics.
    Token-optimized for repeated analyses.
    """
    cleaned = text.strip()
    if not cleaned:
        return 0.0

    word_count, _, avg_words = _cached_word_stats(cleaned)

    # Fast path decisions
    if word_count < 10:
        return 0.25

    if avg_words > 35:
        return 0.4

    if avg_words < 8:
        return 0.6

    return 0.8


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for OpenAI-style tokenization.
    Rule of thumb: ~1.3 tokens per word on average.
    """
    words = len(_TOKEN_PATTERN.findall(text))
    # Add overhead for punctuation and special chars
    return int(words * 1.3) + text.count("\n") * 2
