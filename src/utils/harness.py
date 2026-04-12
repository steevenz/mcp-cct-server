import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class TokenHarness:
    """
    CCT Performance Harness for real-time cost calculation and efficiency tracking.
    Supports multi-model pricing via external JSON registry.
    """
    
    DEFAULT_PRICING_PATH = Path("datasets/pricing.json")
    DEFAULT_MODEL = "claude-3-5-sonnet-20240620"

    def __init__(self, pricing_path: Optional[str] = None):
        self.pricing_path = Path(pricing_path) if pricing_path else self.DEFAULT_PRICING_PATH
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Loads the pricing registry from JSON file."""
        try:
            if not self.pricing_path.exists():
                # Fallback to absolute path from project root if relative fails
                root_path = Path(__file__).parent.parent.parent / self.pricing_path
                if root_path.exists():
                    with open(root_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                return {}
            
            with open(self.pricing_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def calculate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculates the cost in USD based on model pricing.
        Cost = (PromptTokens * InputPrice / 1M) + (CompletionTokens * OutputPrice / 1M)
        """
        model_data = self.registry.get(model_id, self.registry.get(self.DEFAULT_MODEL))
        
        if not model_data:
            # Absolute baseline fallback if registry is empty
            return (prompt_tokens * 3.0 / 1_000_000) + (completion_tokens * 15.0 / 1_000_000)

        in_price = model_data.get("input_price_per_1m", 3.0)
        out_price = model_data.get("output_price_per_1m", 15.0)

        cost = (prompt_tokens * in_price / 1_000_000) + (completion_tokens * out_price / 1_000_000)
        return round(cost, 6)

    def get_efficiency_metrics(self, session_state: Any) -> Dict[str, Any]:
        """
        Calculates cognitive efficiency metrics.
        ROI = ConsistencyScore / TotalCost (simplified)
        Complexity = ThoughtsCount / TotalTokens
        """
        total_thoughts = session_state.current_thought_number
        total_tokens = session_state.total_prompt_tokens + session_state.total_completion_tokens
        total_cost = session_state.total_cost_usd
        consistency = session_state.consistency_score

        # Avoid division by zero
        token_efficiency = (total_thoughts / total_tokens * 1000) if total_tokens > 0 else 0
        cost_efficiency = (consistency / total_cost) if total_cost > 0 else 0

        return {
            "token_efficiency_idx": round(token_efficiency, 2), # Thoughts per 1K tokens
            "cost_efficiency_idx": round(cost_efficiency, 2),   # Consistency per $1
            "avg_cost_per_thought": round(total_cost / total_thoughts, 4) if total_thoughts > 0 else 0
        }
