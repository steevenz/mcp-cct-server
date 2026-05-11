"""
Adaptive Strategy Router — learns from past outcome to inform strategy selection.

Enhances the IntelligenceRouter with:
  1. Per-domain strategy success tracking (which strategies work best for which problems)
  2. Empty/edge-case safety (no IndexError on empty pipelines)
  3. Strategy diversity enforcement (avoid repeating the same failed strategy)
  4. Domain classification for adaptive routing

Neural analogue: Basal ganglia — learns action→outcome associations over time.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from src.core.models.enums import ThinkingStrategy
from src.core.models.domain import EnhancedThought, CCTSessionState
from src.core.services.orchestration.routing import RoutingService

logger = logging.getLogger(__name__)

_DOMAIN_KEYWORDS: Dict[str, Set[str]] = {
    "architecture": {"architecture", "design", "system", "structure", "pattern", "modular", "monolith", "microservice"},
    "security": {"security", "auth", "encryption", "vulnerability", "attack", "threat", "compliance", "audit"},
    "performance": {"performance", "latency", "throughput", "optimize", "cache", "bottleneck", "scalability"},
    "data": {"data", "database", "sql", "nosql", "schema", "migration", "etl", "pipeline"},
    "api": {"api", "rest", "graphql", "endpoint", "rpc", "websocket", "grpc"},
    "testing": {"test", "ci", "cd", "deployment", "quality", "coverage", "regression"},
    "general": set(),
}


def _classify_domain(problem: str) -> str:
    """Classify a problem statement into a domain for adaptive routing."""
    if not problem:
        return "general"
    text = problem.lower()
    scores = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if not keywords:
            continue
        scores[domain] = sum(1 for kw in keywords if kw in text)
    if not scores or max(scores.values()) == 0:
        return "general"
    return max(scores, key=scores.get)


class StrategyMemory:
    """
    Persistent store of strategy→outcome associations per domain.

    File-backed JSON so learnings survive server restarts.
    Thread-safe for concurrent writes.
    """

    def __init__(self, path: str = "database/metadata/strategy_memory.json"):
        self.path = path
        self._lock = threading.Lock()
        self._data: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def record_outcome(self, domain: str, strategy: str, success: bool) -> None:
        with self._lock:
            key = f"{domain}:{strategy}"
            entry = self._data.setdefault(key, {"domain": domain, "strategy": strategy, "attempts": 0, "successes": 0})
            entry["attempts"] += 1
            if success:
                entry["successes"] += 1
            entry["last_used"] = datetime.now(timezone.utc).isoformat()
            self._save()

    def success_rate(self, domain: str, strategy: str) -> float:
        key = f"{domain}:{strategy}"
        entry = self._data.get(key)
        if not entry or entry["attempts"] == 0:
            return 0.0
        return entry["successes"] / entry["attempts"]

    def best_strategies(self, domain: str, top_n: int = 3) -> List[str]:
        candidates = []
        for key, entry in self._data.items():
            if entry.get("domain") == domain and entry["attempts"] > 0:
                rate = entry["successes"] / entry["attempts"]
                candidates.append((rate, entry["strategy"], entry["attempts"]))
        candidates.sort(key=lambda x: (-x[0], -x[2]))
        return [s for _, s, _ in candidates[:top_n]]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_entries": len(self._data),
                "domains": list(set(e["domain"] for e in self._data.values())),
                "strategies": list(set(e["strategy"] for e in self._data.values())),
            }


class AdaptiveRouter:
    """
    Wraps the IntelligenceRouter with adaptive strategy selection.

    Falls through:
      1. If strategy_memory has high-confidence recommendation → use it
      2. Otherwise → delegate to existing IntelligenceRouter
      3. Record outcome for future learning
    """

    def __init__(self, scoring_engine: Any = None):
        self._inner = RoutingService(scoring_engine=scoring_engine)
        self._memory = StrategyMemory()
        self._diversity_window: List[str] = []  # last N strategies used (prevent loops)

    @property
    def scoring(self):
        return self._inner.scoring

    @scoring.setter
    def scoring(self, value):
        self._inner.scoring = value

    def determine_initial_pipeline(self, problem_statement: str) -> List[ThinkingStrategy]:
        return self._inner.determine_initial_pipeline(problem_statement)

    def next_strategy(
        self, session: CCTSessionState, recent_thoughts: List[EnhancedThought]
    ) -> ThinkingStrategy:
        if not recent_thoughts:
            if session.suggested_pipeline:
                return session.suggested_pipeline[0]
            return ThinkingStrategy.LINEAR

        # Classify the problem domain for adaptive selection
        domain = _classify_domain(session.problem_statement)
        last_strategy = recent_thoughts[-1].strategy.value if recent_thoughts else ""

        # Check if current strategy is failing (low metrics → try known-good alternative)
        last_metrics = recent_thoughts[-1].metrics if recent_thoughts[-1].metrics else None
        is_stuck = last_metrics and (
            last_metrics.clarity_score < 0.3 or last_metrics.logical_coherence < 0.3
        )

        if is_stuck and last_strategy:
            best = self._memory.best_strategies(domain, top_n=3)
            # Pick the best strategy that isn't the current failing one
            for candidate in best:
                if candidate != last_strategy and candidate not in self._diversity_window[-3:]:
                    try:
                        logger.info(f"[ADAPTIVE] Strategy {last_strategy} stuck in domain {domain}. Pivoting to {candidate}")
                        return ThinkingStrategy(candidate)
                    except ValueError:
                        continue

        # Delegate to inner router for standard selection
        strategy = self._inner.next_strategy(session, recent_thoughts)

        # Track diversity
        self._diversity_window.append(strategy.value)
        if len(self._diversity_window) > 10:
            self._diversity_window.pop(0)

        return strategy

    def should_finish(self, session, recent_thoughts) -> bool:
        return self._inner.should_finish(session, recent_thoughts)

    def record_outcome(self, domain: str, strategy: str, success: bool) -> None:
        self._memory.record_outcome(domain, strategy, success)

    def get_adaptive_metrics(self) -> Dict[str, Any]:
        return {
            "strategy_memory": self._memory.get_stats(),
            "diversity_window": self._diversity_window[-5:],
        }
