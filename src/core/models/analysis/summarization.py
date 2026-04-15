"""
Summarization domain models.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class CompressionResult:
    """Result of thought compression operation."""
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    summary: str
    thoughts_summarized: int
    preserved_thoughts: List[str]  # IDs of thoughts kept in full
