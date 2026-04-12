import logging
from typing import List, Dict, Optional
from src.core.models.domain import EnhancedThought, CCTSessionState

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
            return ContextPruner._summarize_distant_history(full_history, target_thought_id, depth_threshold=3)

        if strategy == "sliding":
            return full_history[-8:] # Keep last 8 thoughts

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
        depth_threshold: int = 3
    ) -> List[EnhancedThought]:
        """
        For thoughts deeper than the threshold from the target, replace content with summary.
        """
        if not current_id:
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
            
        # 2. Reconstruct history with summaries
        optimized_history = []
        for t in history:
            dist = distance_map.get(t.id, 999) # If not in active path, treat as far
            
            if dist > depth_threshold:
                # Optimized: swap content for summary if available
                new_thought = t.model_copy()
                if new_thought.summary:
                    new_thought.content = f"[SUMMARY] {new_thought.summary}"
                    # Mark as optimized to save tokens
                    new_thought.tags.append("context_optimized")
                optimized_history.append(new_thought)
            else:
                optimized_history.append(t)
                
        return optimized_history
