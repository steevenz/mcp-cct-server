import logging
from typing import List, Dict, Optional
from src.core.models.domain import EnhancedThought, CCTSessionState
from src.core.constants import (
    DEFAULT_SLIDING_WINDOW_SIZE,
    DEFAULT_SUMMARY_DEPTH_THRESHOLD,
)
from src.analysis.summarization import ContextCompressor, CompressionResult

logger = logging.getLogger(__name__)

class ContextPruner:
    """
    Utility to optimize the history sent to the LLM based on token budgets and branching structure.
    """

    @staticmethod
    def prune_history(
        session_state: CCTSessionState, 
        full_history: List[EnhancedThought],
        target_thought_id: Optional[str] = None
    ) -> List[EnhancedThought]:
        """
        Main entry point for history pruning. 
        Supports multiple strategies: full, sliding, summarized, branch_only.
        """
        strategy = session_state.context_strategy
        logger.info(f"Pruning history using strategy: {strategy}")

        if strategy == "full":
            return full_history

        if strategy == "branch_only":
            return ContextPruner._filter_active_path(full_history, target_thought_id)

        if strategy == "summarized":
            return ContextPruner._summarize_distant_history(full_history, target_thought_id)

        if strategy == "sliding":
            return full_history[-DEFAULT_SLIDING_WINDOW_SIZE:] # Keep last N thoughts

        return full_history

    @staticmethod
    def _filter_active_path(history: List[EnhancedThought], current_id: Optional[str]) -> List[EnhancedThought]:
        """
        Filters the history to only include thoughts that are part of the direct ancestral path.
        """
        if not current_id:
            return history
            
        thought_map = {t.id: t for t in history}
        active_path_ids = []
        
        ptr = current_id
        while ptr:
            active_path_ids.append(ptr)
            node = thought_map.get(ptr)
            ptr = node.parent_id if node else None
            
        return [t for t in history if t.id in active_path_ids]

    @staticmethod
    def _summarize_distant_history(
        history: List[EnhancedThought], 
        current_id: Optional[str],
        depth_threshold: int = DEFAULT_SUMMARY_DEPTH_THRESHOLD,
        token_budget: int = 4000
    ) -> List[EnhancedThought]:
        """
        For thoughts deeper than the threshold from the target, replace content with summary.
        
        Enhanced with Recursive Summarization from ContextCompressor for better
        token economy while maintaining semantic coherence.
        """
        if not current_id or len(history) <= depth_threshold:
            return history
            
        # 1. Map distance from current_id
        distance_map = {}
        thought_map = {t.id: t for t in history}
        
        ptr = current_id
        dist = 0
        while ptr:
            distance_map[ptr] = dist
            node = thought_map.get(ptr)
            ptr = node.parent_id if node else None
            dist += 1
        
        # 2. Split into recent (preserve) and distant (compress)
        recent_thoughts = []
        distant_thoughts = []
        
        for t in history:
            dist = distance_map.get(t.id, 999)
            if dist <= depth_threshold:
                recent_thoughts.append(t)
            else:
                distant_thoughts.append(t)
        
        # 3. Use ContextCompressor for recursive summarization of distant thoughts
        if distant_thoughts:
            compressor = ContextCompressor(
                max_tokens_budget=token_budget,
                preserve_recent_n=0,  # We handle preservation manually
                compression_threshold=1000
            )
            
            compression_result = compressor.compress_context(distant_thoughts)
            
            logger.info(
                f"[ContextPruner] Compressed {compression_result.thoughts_summarized} "
                f"thoughts: {compression_result.original_tokens} → "
                f"{compression_result.compressed_tokens} tokens "
                f"({compression_result.compression_ratio:.1%} ratio)"
            )
            
            # Create a synthetic summary thought
            if compression_result.summary:
                from datetime import datetime, timezone
                import uuid
                
                summary_thought = EnhancedThought(
                    id=f"summary_{uuid.uuid4().hex[:8]}",
                    content=compression_result.summary,
                    summary="Recursive compression of distant context",
                    parent_id=distant_thoughts[0].parent_id if distant_thoughts else None,
                    strategy="compression",
                    thought_type="summary",
                    created_at=datetime.now(timezone.utc).isoformat(),
                    tags=["context_optimized", "recursive_summary"],
                    depth=-1,  # Meta-thought
                    branch_id=None,
                    metrics=distant_thoughts[-1].metrics if distant_thoughts else None
                )
                
                # Combine: recent thoughts + summary meta-thought
                optimized_history = distant_thoughts[:1] + [summary_thought] + recent_thoughts
                return optimized_history
        
        # Fallback: return original if no compression needed
        return history
    
    @staticmethod
    def prune_with_compression(
        session_state: CCTSessionState,
        full_history: List[EnhancedThought],
        token_budget: int = 4000
    ) -> CompressionResult:
        """
        Advanced pruning using recursive summarization.
        
        Returns compression metrics along with optimized history.
        """
        compressor = ContextCompressor(max_tokens_budget=token_budget)
        result = compressor.compress_context(full_history)
        
        logger.info(
            f"[ContextPruner] Session {session_state.session_id}: "
            f"Compressed {result.thoughts_summarized} thoughts, "
            f"ratio: {result.compression_ratio:.1%}"
        )
        
        return result
