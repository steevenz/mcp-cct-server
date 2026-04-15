"""
Recursive Summarization Module for Token Economy

Implements context compression through recursive summarization of
older thoughts, maintaining cognitive context without token bloat.

Reference: Whitepaper.md Section 5.2 - Active Branch Pruning & Context Compression
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.core.models.domain import EnhancedThought
from src.core.models.analysis import CompressionResult
from src.core.services.analysis.quality import estimate_token_count

logger = logging.getLogger(__name__)


class ContextCompressor:
    """
    Recursively compresses older thoughts to maintain token budget.
    
    Implements the "Recursive Summarization" technique from the Token Economy:
    - Preserves recent thoughts in full detail
    - Compresses older thoughts into summaries
    - Maintains semantic coherence across compressed context
    """
    
    def __init__(
        self,
        max_tokens_budget: int = 4000,
        preserve_recent_n: int = 5,
        compression_threshold: int = 1000
    ):
        self.max_tokens_budget = max_tokens_budget
        self.preserve_recent_n = preserve_recent_n
        self.compression_threshold = compression_threshold
        
    def compress_context(
        self,
        thoughts: List[EnhancedThought],
        current_thought_id: Optional[str] = None
    ) -> CompressionResult:
        """
        Compress thought history to fit token budget.
        
        Strategy:
        1. Always preserve most recent N thoughts in full
        2. Compress older thoughts into tiered summaries
        3. Ensure total tokens stay under budget
        
        Args:
            thoughts: Chronological list of thoughts
            current_thought_id: ID of current thought (to exclude from compression)
            
        Returns:
            CompressionResult with compression metrics
        """
        if not thoughts:
            return CompressionResult(0, 0, 1.0, "", 0, [])
        
        # Calculate current token count
        total_tokens = sum(
            estimate_token_count(t.content) for t in thoughts
        )
        
        # If under budget, no compression needed
        if total_tokens <= self.max_tokens_budget:
            return CompressionResult(
                original_tokens=total_tokens,
                compressed_tokens=total_tokens,
                compression_ratio=1.0,
                summary="No compression needed - under budget",
                thoughts_summarized=0,
                preserved_thoughts=[t.id for t in thoughts]
            )
        
        logger.info(
            f"Context compression triggered: {total_tokens} tokens "
            f"(budget: {self.max_tokens_budget})"
        )
        
        # Split thoughts: preserve recent, compress older
        preserve_count = min(self.preserve_recent_n, len(thoughts))
        preserved_thoughts = thoughts[-preserve_count:]
        older_thoughts = thoughts[:-preserve_count]
        
        preserved_tokens = sum(
            estimate_token_count(t.content) for t in preserved_thoughts
        )
        
        # Calculate compression budget for older thoughts
        compression_budget = self.max_tokens_budget - preserved_tokens
        
        if compression_budget < 0:
            # Even recent thoughts exceed budget - must compress everything
            logger.warning("Critical: Even recent thoughts exceed token budget")
            return self._emergency_compression(thoughts)
        
        # Compress older thoughts
        if older_thoughts:
            compressed_summary = self._recursive_summarize(older_thoughts, compression_budget)
            compressed_tokens = estimate_token_count(compressed_summary)
        else:
            compressed_summary = ""
            compressed_tokens = 0
        
        final_tokens = preserved_tokens + compressed_tokens
        
        return CompressionResult(
            original_tokens=total_tokens,
            compressed_tokens=final_tokens,
            compression_ratio=final_tokens / total_tokens if total_tokens > 0 else 1.0,
            summary=compressed_summary,
            thoughts_summarized=len(older_thoughts),
            preserved_thoughts=[t.id for t in preserved_thoughts]
        )
    
    def _recursive_summarize(
        self,
        thoughts: List[EnhancedThought],
        token_budget: int
    ) -> str:
        """
        Recursively summarize thoughts into hierarchical summary.
        
        Implements tiered compression:
        - Level 1: Individual thought summaries
        - Level 2: Group summaries (every N thoughts)
        - Level 3: Meta-summary of all groups
        """
        if not thoughts:
            return ""
        
        # Level 1: Summarize individual thoughts
        individual_summaries = []
        for thought in thoughts:
            summary = self._summarize_thought(thought)
            individual_summaries.append(summary)
        
        # Check if we need further compression
        combined = " | ".join(individual_summaries)
        tokens = estimate_token_count(combined)
        
        if tokens <= token_budget:
            return f"[Historical Context: {len(thoughts)} thoughts summarized] {combined}"
        
        # Level 2: Group summarization for deeper compression
        group_size = max(2, len(thoughts) // 3)
        group_summaries = []
        
        for i in range(0, len(thoughts), group_size):
            group = thoughts[i:i + group_size]
            group_summary = self._summarize_group(group)
            group_summaries.append(group_summary)
        
        meta_summary = " | ".join(group_summaries)
        
        return (
            f"[Compressed History: {len(thoughts)} thoughts → "
            f"{len(group_summaries)} groups] {meta_summary}"
        )
    
    def _summarize_thought(self, thought: EnhancedThought) -> str:
        """Create a concise summary of a single thought."""
        content = thought.content
        
        # Extract key information
        strategy = thought.strategy if hasattr(thought, 'strategy') else 'unknown'
        thought_type = thought.thought_type if hasattr(thought, 'thought_type') else 'unknown'
        
        # Truncate content if too long
        max_chars = 200
        if len(content) > max_chars:
            content = content[:max_chars].rsplit(' ', 1)[0] + "..."
        
        return f"[{strategy}/{thought_type}] {content}"
    
    def _summarize_group(self, thoughts: List[EnhancedThought]) -> str:
        """Summarize a group of related thoughts."""
        strategies = set()
        types = set()
        key_points = []
        
        for t in thoughts:
            if hasattr(t, 'strategy'):
                strategies.add(t.strategy)
            if hasattr(t, 'thought_type'):
                types.add(t.thought_type)
            
            # Extract first sentence as key point
            first_sentence = t.content.split('.')[0][:100]
            if first_sentence:
                key_points.append(first_sentence)
        
        strategy_str = "/".join(str(s) for s in strategies) if strategies else "mixed"
        type_str = "/".join(str(t) for t in types) if types else "mixed"
        
        # Combine key points
        combined_points = "; ".join(key_points[:3])
        if len(key_points) > 3:
            combined_points += f" (+{len(key_points) - 3} more)"
        
        return f"[Group: {strategy_str}/{type_str}] {combined_points}"
    
    def _emergency_compression(self, thoughts: List[EnhancedThought]) -> CompressionResult:
        """
        Emergency compression when even recent thoughts exceed budget.
        
        Keeps only the most essential context.
        """
        # Keep only last 3 thoughts with aggressive truncation
        essential = thoughts[-3:] if len(thoughts) >= 3 else thoughts
        
        summaries = []
        for t in essential:
            content = t.content[:100] + "..." if len(t.content) > 100 else t.content
            summaries.append(f"[{t.strategy if hasattr(t, 'strategy') else '?'}/{t.thought_type if hasattr(t, 'thought_type') else '?'}] {content}")
        
        compressed = " | ".join(summaries)
        compressed_tokens = estimate_token_count(compressed)
        original_tokens = sum(estimate_token_count(t.content) for t in thoughts)
        
        return CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
            summary=f"[EMERGENCY COMPRESSION: {len(thoughts)} → {len(essential)} thoughts] {compressed}",
            thoughts_summarized=len(thoughts) - len(essential),
            preserved_thoughts=[t.id for t in essential]
        )


class ThoughtChainCompressor:
    """
    Specialized compressor for thought chains with parent-child relationships.
    
    Preserves tree structure while compressing content.
    """
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        
    def compress_chain(
        self,
        root_thought: EnhancedThought,
        all_thoughts: Dict[str, EnhancedThought]
    ) -> str:
        """
        Compress a thought chain preserving branch structure.
        
        Args:
            root_thought: The root/parent thought
            all_thoughts: Dictionary mapping thought_id to thought
            
        Returns:
            Hierarchical summary preserving branch structure
        """
        return self._compress_recursive(root_thought, all_thoughts, depth=0)
    
    def _compress_recursive(
        self,
        thought: EnhancedThought,
        all_thoughts: Dict[str, EnhancedThought],
        depth: int
    ) -> str:
        """Recursively compress thought and its children."""
        if depth >= self.max_depth:
            return "[...truncated...]"
        
        # Summarize current thought
        content = thought.content[:150] + "..." if len(thought.content) > 150 else thought.content
        
        # Find and compress children
        children_ids = getattr(thought, 'child_thought_ids', [])
        children = [all_thoughts.get(cid) for cid in children_ids if cid in all_thoughts]
        children = [c for c in children if c]  # Filter None
        
        if not children:
            return f"└─ [{thought.strategy if hasattr(thought, 'strategy') else '?'}] {content}"
        
        # Compress children
        child_summaries = []
        for child in children:
            child_summary = self._compress_recursive(child, all_thoughts, depth + 1)
            child_summaries.append(child_summary)
        
        children_str = "\n".join("  " + cs for cs in child_summaries)
        
        return f"├─ [{thought.strategy if hasattr(thought, 'strategy') else '?'}] {content}\n{children_str}"


def compress_session_context(
    thoughts: List[EnhancedThought],
    token_budget: int = 4000
) -> CompressionResult:
    """
    Convenience function for compressing session context.
    
    Args:
        thoughts: List of thoughts in session
        token_budget: Maximum tokens allowed
        
    Returns:
        CompressionResult with summary and metrics
    """
    compressor = ContextCompressor(max_tokens_budget=token_budget)
    return compressor.compress_context(thoughts)
