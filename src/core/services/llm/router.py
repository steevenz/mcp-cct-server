"""
ModelSelectionStrategy: Intelligent Model Selection for Cost-Performance Optimization.

Implements the CCT v5.0 §7.C requirement for intelligent model tier selection.
Selects appropriate models based on:
- Task complexity
- Required reasoning depth
- Cost constraints
- Latency requirements

Anthropic Tiers:
- Haiku: Fast, cheap for simple tasks ($0.25/1M tokens)
- Sonnet: Balanced for most reasoning tasks ($3/1M tokens)
- Opus: Deep reasoning for complex tasks ($15/1M tokens)

OpenAI Tiers:
- GPT-4o-mini: Fast, cheap ($0.15/1M tokens)
- GPT-4o: Balanced ($2.50/1M tokens)
- GPT-4-turbo: Deep reasoning ($10/1M tokens)

Gemini Tiers:
- gemini-flash-latest: Fast, free tier available
- gemini-pro: Balanced
- gemini-ultra: Deep reasoning
"""

import logging
from typing import Dict, Any, Optional, List
from src.core.config import Settings
from src.core.models import ReasoningDepth, ModelSelection, CognitiveTaskContext

logger = logging.getLogger(__name__)


class RouterService:
    """
    Intelligent Model Selection Strategy for cost-performance optimization.
    
    Implements intelligent selection to minimize costs while maintaining quality.
    """
    
    # Cost per 1K tokens (input + output avg)
    DEPTH_COSTS = {
        "anthropic": {
            ReasoningDepth.FAST: 0.25,      # Haiku
            ReasoningDepth.BALANCED: 3.0,   # Sonnet
            ReasoningDepth.DEEP: 15.0,      # Opus
        },
        "openai": {
            ReasoningDepth.FAST: 0.15,      # GPT-4o-mini
            ReasoningDepth.BALANCED: 2.50,  # GPT-4o
            ReasoningDepth.DEEP: 10.0,      # GPT-4-turbo
        },
        "gemini": {
            ReasoningDepth.FAST: 0.0,       # Flash (free tier)
            ReasoningDepth.BALANCED: 0.0,   # Pro (free tier available)
            ReasoningDepth.DEEP: 0.0,       # Ultra
        },
        "ollama": {
            ReasoningDepth.FAST: 0.0,
            ReasoningDepth.BALANCED: 0.0,
            ReasoningDepth.DEEP: 0.0,
        }
    }
    
    # Estimated latency (ms per 1K tokens)
    DEPTH_LATENCY = {
        "anthropic": {
            ReasoningDepth.FAST: 500,
            ReasoningDepth.BALANCED: 1500,
            ReasoningDepth.DEEP: 4000,
        },
        "openai": {
            ReasoningDepth.FAST: 300,
            ReasoningDepth.BALANCED: 1200,
            ReasoningDepth.DEEP: 3000,
        },
        "gemini": {
            ReasoningDepth.FAST: 400,
            ReasoningDepth.BALANCED: 1000,
            ReasoningDepth.DEEP: 2500,
        },
        "ollama": {
            ReasoningDepth.FAST: 200,
            ReasoningDepth.BALANCED: 800,
            ReasoningDepth.DEEP: 2000,
        }
    }
    
    # Model mappings by provider and depth
    MODELS = {
        "anthropic": {
            ReasoningDepth.FAST: "claude-3-haiku-20240307",
            ReasoningDepth.BALANCED: "claude-3-5-sonnet-20240620",
            ReasoningDepth.DEEP: "claude-3-opus-20240229",
        },
        "openai": {
            ReasoningDepth.FAST: "gpt-4o-mini",
            ReasoningDepth.BALANCED: "gpt-4o",
            ReasoningDepth.DEEP: "gpt-4-turbo",
        },
        "gemini": {
            ReasoningDepth.FAST: "gemini-flash-latest",
            ReasoningDepth.BALANCED: "gemini-pro",
            ReasoningDepth.DEEP: "gemini-ultra",
        },
        "ollama": {
            ReasoningDepth.FAST: "llama3",
            ReasoningDepth.BALANCED: "llama3",
            ReasoningDepth.DEEP: "llama3",
        }
    }
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._selection_stats = {
            "total_requests": 0,
            "depth_distribution": {depth.value: 0 for depth in ReasoningDepth},
            "cost_savings": 0.0,  # vs always using DEEP depth
        }
    
    def select_model(self, task_context: CognitiveTaskContext) -> ModelSelection:
        """
        Select appropriate model for a cognitive task.
        
        Implements the asymmetric selection algorithm:
        1. Determine required depth based on task complexity
        2. Apply cost constraints if specified
        3. Select provider based on availability and cost
        4. Return selection decision with cost/latency estimates
        """
        self._selection_stats["total_requests"] += 1
        
        # Step 1: Determine base depth from complexity
        base_depth = self._complexity_to_depth(task_context)
        
        # Step 2: Adjust for latency preference
        adjusted_depth = self._apply_latency_preference(base_depth, task_context.latency_preference)
        
        # Step 3: Apply cost constraints
        final_depth = self._apply_cost_constraints(adjusted_depth, task_context)
        
        # Step 4: Select provider
        provider = self._select_provider(final_depth)
        
        # Step 5: Build selection
        model = self.MODELS[provider][final_depth]
        cost_per_1k = self.DEPTH_COSTS[provider][final_depth]
        latency_per_1k = self.DEPTH_LATENCY[provider][final_depth]
        
        estimated_cost = (cost_per_1k * task_context.token_estimate) / 1000
        estimated_latency = (latency_per_1k * task_context.token_estimate) / 1000
        
        # Update stats
        self._selection_stats["depth_distribution"][final_depth.value] += 1
        
        # Calculate cost savings vs using DEEP depth
        deep_cost = (self.TIER_COSTS[provider][ReasoningDepth.DEEP] * task_context.token_estimate) / 1000
        self._selection_stats["cost_savings"] += (deep_cost - estimated_cost)
        
        rationale = self._generate_rationale(task_context, final_depth, provider)
        
        logger.info(
            f"[STRATEGY] Task selected for {provider}/{model} ({final_depth.value}) "
            f"- est. cost: ${estimated_cost:.4f}, latency: {estimated_latency:.0f}ms"
        )
        
        return ModelSelection(
            provider=provider,
            model=model,
            depth=final_depth,
            estimated_cost_per_1k=cost_per_1k,
            estimated_latency_ms=int(estimated_latency),
            selection_rationale=rationale
        )
    
    def _complexity_to_depth(self, task: CognitiveTaskContext) -> ReasoningDepth:
        """Map task complexity to reasoning depth."""
        complexity_map = {
            "simple": ReasoningDepth.FAST,
            "moderate": ReasoningDepth.BALANCED,
            "complex": ReasoningDepth.BALANCED,
            "sovereign": ReasoningDepth.DEEP,
        }
        
        base_depth = complexity_map.get(task.complexity, ReasoningDepth.BALANCED)
        
        # Override for code tasks (need better reasoning)
        if task.requires_code and base_depth == ReasoningDepth.FAST:
            base_depth = ReasoningDepth.BALANCED
        
        # Override for deep reasoning tasks
        if task.requires_reasoning and task.complexity in ["complex", "sovereign"]:
            base_depth = ReasoningDepth.DEEP
        
        return base_depth
    
    def _apply_latency_preference(self, depth: ReasoningDepth, preference: str) -> ReasoningDepth:
        """Adjust depth based on latency preference."""
        if preference == "fast":
            # Downgrade one depth if possible
            if depth == ReasoningDepth.DEEP:
                return ReasoningDepth.BALANCED
            elif depth == ReasoningDepth.BALANCED:
                return ReasoningDepth.FAST
        elif preference == "quality":
            # Upgrade one depth if possible
            if depth == ReasoningDepth.FAST:
                return ReasoningDepth.BALANCED
            elif depth == ReasoningDepth.BALANCED:
                return ReasoningDepth.DEEP
        return depth
    
    def _apply_cost_constraints(self, depth: ReasoningDepth, task: CognitiveTaskContext) -> ReasoningDepth:
        """Downgrade depth if cost exceeds budget."""
        if task.cost_budget is None:
            return depth
        
        # Check cheapest provider for this depth
        for check_depth in [depth, ReasoningDepth.BALANCED, ReasoningDepth.FAST]:
            provider = self._select_provider(check_depth)
            cost_per_1k = self.DEPTH_COSTS[provider][check_depth]
            estimated_cost = (cost_per_1k * task.token_estimate) / 1000
            
            if estimated_cost <= task.cost_budget:
                if check_depth != depth:
                    logger.info(f"[STRATEGY] Downgraded from {depth.value} to {check_depth.value} due to cost budget")
                return check_depth
        
        # If all depths exceed budget, return cheapest
        return ReasoningDepth.FAST
    
    def _select_provider(self, depth: ReasoningDepth) -> str:
        """Select best available provider for the depth."""
        # Priority: Gemini (free) > Ollama (local) > Anthropic > OpenAI
        if self.settings.gemini_api_key:
            return "gemini"
        elif self.settings.ollama_base_url:
            return "ollama"
        elif self.settings.anthropic_api_key:
            return "anthropic"
        elif self.settings.openai_api_key:
            return "openai"
        else:
            # Default fallback
            return "gemini"
    
    def _generate_rationale(self, task: CognitiveTaskContext, depth: ReasoningDepth, provider: str) -> str:
        """Generate human-readable selection rationale."""
        reasons = []
        
        reasons.append(f"Complexity '{task.complexity}' maps to {depth.value} depth")
        
        if task.requires_code:
            reasons.append("Code generation requires balanced reasoning")
        
        if task.requires_reasoning:
            reasons.append("Deep reasoning requested")
        
        reasons.append(f"Provider '{provider}' selected based on availability")
        
        return "; ".join(reasons)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get selection statistics."""
        if self._selection_stats["total_requests"] == 0:
            return self._selection_stats
        
        distribution = self._selection_stats["depth_distribution"].copy()
        total = self._selection_stats["total_requests"]
        
        return {
            **self._selection_stats,
            "depth_percentages": {
                depth: round(count / total * 100, 1) 
                for depth, count in distribution.items()
            },
            "avg_cost_savings_per_request": round(
                self._selection_stats["cost_savings"] / total, 4
            ) if total > 0 else 0
        }
    
    def reset_stats(self) -> None:
        """Reset selection statistics."""
        self._selection_stats = {
            "total_requests": 0,
            "depth_distribution": {depth.value: 0 for depth in ReasoningDepth},
            "cost_savings": 0.0,
        }
    
    def get_model_for_strategy(self, strategy: str, complexity: str = "moderate") -> str:
        """
        Get appropriate model for a thinking strategy.
        
        Legacy method for backward compatibility with skills_loader.py
        """
        # Map strategies to task profiles
        strategy_complexity = {
            "LINEAR": "simple",
            "ANALYTICAL": "moderate",
            "CRITICAL": "moderate",
            "FIRST_PRINCIPLES": "complex",
            "SYSTEMIC": "complex",
            "DIALECTICAL": "complex",
            "MULTI_AGENT_FUSION": "complex",
            "COUNCIL_OF_CRITICS": "sovereign",
            "ACTOR_CRITIC_LOOP": "complex",
        }
        
        task_complexity = strategy_complexity.get(strategy, complexity)
        
        task = CognitiveTaskContext(
            complexity=task_complexity,
            requires_reasoning=task_complexity in ["complex", "sovereign"],
            requires_code="CODE" in strategy or "ENGINEERING" in strategy,
            token_estimate=2000,
            latency_preference="balanced"
        )
        
        selection = self.select_model(task)
        return selection.model
