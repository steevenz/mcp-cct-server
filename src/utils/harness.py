import json
from typing import Dict, Any, Optional
from pathlib import Path

from src.core.constants import (
    DEFAULT_PRICING_PATH,
    DEFAULT_MODEL,
    FALLBACK_INPUT_PRICE_PER_1M,
    FALLBACK_OUTPUT_PRICE_PER_1M,
)

class TokenHarness:
    """
    CCT Performance Harness for real-time cost calculation and efficiency tracking.
    Supports multi-model pricing via external JSON registry.
    """
    
    DEFAULT_PRICING_PATH = Path(DEFAULT_PRICING_PATH)
    DEFAULT_MODEL = DEFAULT_MODEL

    def __init__(self, pricing_path: Optional[str] = None):
        self.pricing_path = Path(pricing_path) if pricing_path else self.DEFAULT_PRICING_PATH
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Loads the pricing registry from directory containing per-model JSON files."""
        registry = {}
        try:
            pricing_dir = self.pricing_path
            
            # Fallback to absolute path from project root if relative fails
            if not pricing_dir.exists():
                pricing_dir = Path(__file__).parent.parent.parent / self.pricing_path
            
            if not pricing_dir.exists():
                return {}
            
            # Load all JSON files from the pricing directory
            for json_file in pricing_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        model_data = json.load(f)
                        model_id = model_data.get("model_id")
                        if model_id:
                            registry[model_id] = model_data
                except Exception as e:
                    # Skip invalid files
                    continue
                    
            return registry
        except Exception:
            return {}

    def get_model_pricing(self, model_id: str) -> Dict[str, Any]:
        """
        Retrieves pricing data for a specific model.
        Falls back to default model if not found.
        """
        # Try exact match first
        if model_id in self.registry:
            return self.registry[model_id]
        
        # Try partial match (e.g., "claude-3-5-sonnet" matches "claude-3-5-sonnet-20240620")
        for registered_id, data in self.registry.items():
            if model_id in registered_id or registered_id in model_id:
                return data
        
        # Fall back to default model
        return self.registry.get(self.DEFAULT_MODEL, {})

    def calculate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculates the cost in USD based on model-specific pricing.
        Cost = (PromptTokens * InputPrice / 1M) + (CompletionTokens * OutputPrice / 1M)
        
        Args:
            model_id: The AI model identifier (e.g., "claude-3-5-sonnet-20240620")
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Calculated cost in USD
        """
        model_data = self.get_model_pricing(model_id)
        
        if not model_data:
            # Absolute baseline fallback if registry is empty
            return (prompt_tokens * FALLBACK_INPUT_PRICE_PER_1M / 1_000_000) + (completion_tokens * FALLBACK_OUTPUT_PRICE_PER_1M / 1_000_000)

        in_price = model_data.get("input_price_per_1m", FALLBACK_INPUT_PRICE_PER_1M)
        out_price = model_data.get("output_price_per_1m", FALLBACK_OUTPUT_PRICE_PER_1M)

        cost = (prompt_tokens * in_price / 1_000_000) + (completion_tokens * out_price / 1_000_000)
        return round(cost, 6)

    def is_model_supported(self, model_id: str) -> bool:
        """Check if a model has pricing data available."""
        return bool(self.get_model_pricing(model_id))

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
