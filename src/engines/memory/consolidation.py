"""
ConsolidationEngine: Episodic-to-Semantic Memory Consolidation.

Implements the neural "sleep" cycle — analyzing completed sessions to:
  - Promote high-value patterns to long-term semantic memory
  - Demote stale/low-usage patterns (synaptic pruning)
  - Detect pattern co-occurrence and meta-patterns
  - Prune redundant anti-patterns

Reference: Neural memory consolidation (hippocampus→neocortex transfer)
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from src.engines.memory.manager import MemoryManager
from src.core.models.domain import GoldenThinkingPattern, AntiPattern

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationReport:
    session_count: int = 0
    patterns_promoted: int = 0
    patterns_demoted: int = 0
    patterns_pruned: int = 0
    anti_patterns_pruned: int = 0
    meta_patterns_detected: int = 0
    consolidated_at: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class ConsolidationEngine:
    """
    Neural consolidation engine that runs episodic→semantic transfer.

    Mimics hippocampal replay during sleep:
      1. Scans recently completed sessions
      2. Identifies high-frequency pattern usage
      3. Promotes frequently co-occurring patterns to meta-patterns
      4. Demotes stale/low-usage patterns
      5. Prunes redundant anti-patterns
    """

    def __init__(
        self,
        memory: MemoryManager,
        promotion_threshold: int = 3,
        demotion_threshold_days: int = 30,
        prune_after_demotions: int = 3,
        co_occurrence_min: int = 2,
    ):
        self.memory = memory
        self.promotion_threshold = promotion_threshold
        self.demotion_threshold_days = demotion_threshold_days
        self.prune_after_demotions = prune_after_demotions
        self.co_occurrence_min = co_occurrence_min

    def consolidate(self, llm_instance_id: Optional[str] = None) -> ConsolidationReport:
        """
        Run a full consolidation cycle (episodic → semantic transfer).

        Call this after N sessions complete, or on a timer.
        """
        report = ConsolidationReport(
            consolidated_at=datetime.now(timezone.utc).isoformat()
        )

        try:
            patterns = self.memory.get_all_thinking_patterns()
            anti_patterns = self.memory.get_all_anti_patterns()
            sessions = self.memory.list_sessions(llm_instance_id=llm_instance_id, limit=500)

            report.session_count = len(sessions) if sessions else 0

            # 1. Promote: patterns used across multiple sessions
            promoted = self._promote_patterns(patterns)
            report.patterns_promoted = promoted

            # 2. Demote: stale patterns
            demoted = self._demote_stale_patterns(patterns)
            report.patterns_demoted = demoted

            # 3. Prune: patterns demoted too many times
            pruned = self._prune_dead_patterns(patterns)
            report.patterns_pruned = pruned

            # 4. Detect meta-patterns (co-occurrence)
            meta = self._detect_meta_patterns(patterns)
            report.meta_patterns_detected = meta

            # 5. Prune redundant anti-patterns
            anti_pruned = self._prune_redundant_anti_patterns(anti_patterns)
            report.anti_patterns_pruned = anti_pruned

            report.details = {
                "total_patterns": len(patterns),
                "total_anti_patterns": len(anti_patterns),
                "promotion_threshold": self.promotion_threshold,
                "demotion_threshold_days": self.demotion_threshold_days,
            }

            logger.info(
                f"[CONSOLIDATION] Complete: {promoted} promoted, {demoted} demoted, "
                f"{pruned} pruned, {meta} meta-patterns, {anti_pruned} anti-pruned"
            )

        except Exception as e:
            logger.error(f"[CONSOLIDATION] Failed: {e}", exc_info=True)
            report.details["error"] = str(e)

        return report

    def _promote_patterns(self, patterns: List[Dict[str, Any]]) -> int:
        """Promote frequently used patterns to 'consolidated' semantic memory."""
        promoted = 0
        for p in patterns:
            usage = p.get("usage_count", 0)
            tags = p.get("tags", [])
            is_consolidated = "consolidated" in tags
            if usage >= self.promotion_threshold and not is_consolidated:
                tags.append("consolidated")
                tags.append("semantic")
                p["tags"] = tags
                p["consolidated_at"] = datetime.now(timezone.utc).isoformat()
                try:
                    pattern_id = p.get("id") or p.get("tp_id")
                    if pattern_id:
                        self.memory._save_raw_pattern(pattern_id, p)
                        promoted += 1
                        logger.debug(f"[CONSOLIDATION] Promoted pattern {pattern_id} (usage={usage})")
                except Exception as e:
                    logger.warning(f"[CONSOLIDATION] Failed to promote pattern: {e}")
        return promoted

    def _demote_stale_patterns(self, patterns: List[Dict[str, Any]]) -> int:
        """Demote patterns not used recently (synaptic pruning candidate)."""
        demoted = 0
        now = datetime.now(timezone.utc)
        for p in patterns:
            created_raw = p.get("created_at") or p.get("timestamp") or ""
            try:
                created = datetime.fromisoformat(created_raw)
            except (ValueError, TypeError):
                continue
            age_days = (now - created).days
            usage = p.get("usage_count", 0)
            tags = p.get("tags", [])

            if age_days > self.demotion_threshold_days and usage < 2:
                if "demoted" not in tags:
                    tags.append("demoted")
                    p["tags"] = tags
                    p["demoted_at"] = now.isoformat()
                    p["demotion_count"] = p.get("demotion_count", 0) + 1
                    try:
                        pattern_id = p.get("id") or p.get("tp_id")
                        if pattern_id:
                            self.memory._save_raw_pattern(pattern_id, p)
                            demoted += 1
                            logger.debug(f"[CONSOLIDATION] Demoted pattern {pattern_id} (age={age_days}d)")
                    except Exception as e:
                        logger.warning(f"[CONSOLIDATION] Failed to demote pattern: {e}")
        return demoted

    def _prune_dead_patterns(self, patterns: List[Dict[str, Any]]) -> int:
        """Remove patterns demoted too many times."""
        pruned = 0
        for p in patterns:
            demotion_count = p.get("demotion_count", 0)
            if demotion_count >= self.prune_after_demotions:
                pattern_id = p.get("id") or p.get("tp_id")
                if pattern_id:
                    try:
                        self.memory._delete_pattern(pattern_id)
                        pruned += 1
                        logger.info(f"[CONSOLIDATION] Pruned dead pattern {pattern_id}")
                    except Exception as e:
                        logger.warning(f"[CONSOLIDATION] Failed to prune {pattern_id}: {e}")
        return pruned

    def _detect_meta_patterns(self, patterns: List[Dict[str, Any]]) -> int:
        """
        Detect patterns that frequently co-occur → promote to meta-pattern.

        A meta-pattern is a strategy template that combines multiple
        sub-strategies proven to work well together.
        """
        if len(patterns) < self.co_occurrence_min:
            return 0

        strategy_pairs: Dict[str, int] = {}
        strategies = [p.get("strategy", "unknown") for p in patterns if p.get("strategy")]

        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                pair = tuple(sorted([strategies[i], strategies[j]]))
                key = f"{pair[0]}+{pair[1]}"
                strategy_pairs[key] = strategy_pairs.get(key, 0) + 1

        meta_count = 0
        for pair_key, count in strategy_pairs.items():
            if count >= self.co_occurrence_min:
                s1, s2 = pair_key.split("+")
                meta_id = f"meta_{uuid.uuid4().hex[:6]}"
                meta_pattern = {
                    "id": meta_id,
                    "tp_id": meta_id,
                    "type": "meta_pattern",
                    "tag": f"meta:{s1}+{s2}",
                    "strategies": [s1, s2],
                    "co_occurrence_count": count,
                    "usage_count": 1,
                    "tags": ["meta_pattern", "consolidated"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    self.memory._save_raw_pattern(meta_id, meta_pattern)
                    meta_count += 1
                    logger.info(f"[CONSOLIDATION] Meta-pattern detected: {s1}+{s2} (x{count})")
                except Exception as e:
                    logger.warning(f"[CONSOLIDATION] Failed to save meta-pattern: {e}")

        return meta_count

    def _prune_redundant_anti_patterns(self, anti_patterns: List[Dict[str, Any]]) -> int:
        """
        Remove anti-patterns that have been superseded or are too old.

        Anti-patterns older than 2x demotion threshold with zero usage get pruned.
        """
        pruned = 0
        now = datetime.now(timezone.utc)
        for ap in anti_patterns:
            created_raw = ap.get("created_at") or ap.get("timestamp") or ""
            try:
                created = datetime.fromisoformat(created_raw)
            except (ValueError, TypeError):
                continue
            age_days = (now - created).days
            if age_days > self.demotion_threshold_days * 2:
                ap_id = ap.get("id") or ap.get("failure_id")
                if ap_id:
                    try:
                        self.memory._delete_anti_pattern(ap_id)
                        pruned += 1
                        logger.debug(f"[CONSOLIDATION] Pruned old anti-pattern {ap_id}")
                    except Exception as e:
                        logger.warning(f"[CONSOLIDATION] Failed to prune anti-pattern: {e}")
        return pruned
