"""
PatternArchiver: Long-Term Potentiation (LTP) System.

Implements the cognitive evolution mechanism from CCT v5.0 §5.C.
Automatically archives elite thoughts (Golden Thinking Patterns) that achieve
the threshold score (logical_coherence >= 0.9, evidence_strength >= 0.8).

Features:
- Automatic pattern detection and archival
- Usage count tracking (patterns strengthen with use)
- Relevance-based retrieval
- Anti-pattern archival for cognitive immune system
- Markdown export to Context Tree
"""

import os
import uuid
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from src.core.models.domain import EnhancedThought, GoldenThinkingPattern, AntiPattern, CCTSessionState
from src.engines.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


@dataclass
class ArchiveResult:
    """Result of pattern archival operation."""
    archived: bool
    pattern_id: Optional[str] = None
    pattern_type: str = "unknown"  # 'golden', 'anti', 'none'
    reason: str = ""


class PatternArchiver:
    """
    Pattern Archiver for Long-Term Potentiation (LTP).
    
    Implements biological-inspired learning where frequently used
    neural pathways (thinking patterns) become stronger over time.
    Also supports Context Tree markdown export for human-readable archives.
    """
    
    def __init__(
        self,
        memory: MemoryManager,
        tp_threshold: float = 0.9,
        evidence_threshold: float = 0.8,
        docs_root: str = "docs/context-tree/Thinking-Patterns"
    ):
        self.memory = memory
        self.tp_threshold = tp_threshold
        self.evidence_threshold = evidence_threshold
        self.docs_root = docs_root
        os.makedirs(self.docs_root, exist_ok=True)
        self._stats = {
            "golden_archived": 0,
            "anti_archived": 0,
            "retrievals": 0
        }

    def process_thought(self, session: CCTSessionState, thought: EnhancedThought) -> Optional[GoldenThinkingPattern]:
        """
        Evaluates if a thought is worthy of becoming a Golden Thinking Pattern.
        Legacy compatibility method - delegates to archive_thought.
        """
        result = self.archive_thought(thought, session.session_id)
        if result.archived and result.pattern_type == "golden":
            # Retrieve the pattern we just archived
            return self.memory.get_thinking_pattern_by_thought_id(thought.id)
        return None

    def is_golden_pattern_candidate(self, thought: EnhancedThought) -> bool:
        """
        Check if thought qualifies as Golden Thinking Pattern.
        
        Criteria (from CCT v5.0):
        - logical_coherence >= 0.9
        - evidence_strength >= 0.8
        """
        if not thought.metrics:
            return False
        
        metrics = thought.metrics
        return (
            metrics.logical_coherence >= self.tp_threshold and
            metrics.evidence_strength >= self.evidence_threshold
        )

    def archive_thought(self, thought: EnhancedThought, session_id: str) -> ArchiveResult:
        """
        Archive a thought as Golden Thinking Pattern if it qualifies.
        Also exports to Context Tree markdown.
        
        Returns ArchiveResult indicating success/failure and reason.
        """
        # Check if already archived
        existing = self._check_existing_pattern(thought)
        if existing:
            # Increment usage count for existing pattern
            self._increment_usage_count(existing.id)
            return ArchiveResult(
                archived=False,
                pattern_id=existing.id,
                pattern_type="golden_existing",
                reason="Pattern already archived, usage count incremented"
            )
        
        # Check if qualifies as golden pattern
        if not self.is_golden_pattern_candidate(thought):
            return ArchiveResult(
                archived=False,
                pattern_type="none",
                reason=f"Does not meet thresholds (coherence: {thought.metrics.logical_coherence:.2f}, evidence: {thought.metrics.evidence_strength:.2f})"
            )
        
        # Create Golden Thinking Pattern
        pattern = GoldenThinkingPattern(
            id=f"gtp_{uuid.uuid4().hex[:8]}",
            thought_id=thought.id,
            session_id=session_id,
            strategy=thought.strategy,
            content_summary=thought.summary or thought.content[:200],
            full_content=thought.content,
            metrics=thought.metrics,
            tags=thought.tags,
            created_at=datetime.now(timezone.utc).isoformat(),
            usage_count=1
        )
        
        # Persist to memory
        try:
            self.memory.save_thinking_pattern(pattern)
            self._stats["golden_archived"] += 1
            thought.is_thinking_pattern = True
            
            # Export to Context Tree (Markdown)
            self._export_to_markdown(pattern, thought.strategy.value)
            
            logger.info(
                f"[ARCHIVER] Golden pattern archived: {pattern.id} "
                f"(coherence: {thought.metrics.logical_coherence:.2f}, "
                f"evidence: {thought.metrics.evidence_strength:.2f})"
            )
            
            return ArchiveResult(
                archived=True,
                pattern_id=pattern.id,
                pattern_type="golden",
                reason="Elite thought archived as Golden Thinking Pattern"
            )
        except Exception as e:
            logger.error(f"[ARCHIVER] Failed to archive pattern: {e}")
            return ArchiveResult(
                archived=False,
                pattern_type="error",
                reason=f"Archival failed: {str(e)}"
            )

    def archive_anti_pattern(
        self,
        thought: EnhancedThought,
        session_id: str,
        failure_reason: str,
        corrective_action: str,
        category: str = "unknown"
    ) -> ArchiveResult:
        """
        Archive a failure as Anti-Pattern for cognitive immune system.
        
        Anti-patterns prevent the AI from "falling into the same pit twice"
        by remembering failures and their corrections.
        """
        anti_pattern = AntiPattern(
            id=f"anti_{uuid.uuid4().hex[:8]}",
            thought_id=thought.id,
            session_id=session_id,
            failed_strategy=thought.strategy,
            problem_context=thought.content[:200],
            category=category,
            failure_reason=failure_reason,
            corrective_action=corrective_action,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        try:
            self.memory.save_anti_pattern(anti_pattern)
            self._stats["anti_archived"] += 1
            
            logger.info(
                f"[ARCHIVER] Anti-pattern archived: {anti_pattern.id} "
                f"(category: {category}, strategy: {thought.strategy.value}) | "
                f"session={session_id} | "
                f"total_anti={self._stats['anti_archived']}"
            )
            
            return ArchiveResult(
                archived=True,
                pattern_id=anti_pattern.id,
                pattern_type="anti",
                reason="Failure archived as Anti-Pattern for immune system"
            )
        except Exception as e:
            logger.error(f"[ARCHIVER] Failed to archive anti-pattern: {e}")
            return ArchiveResult(
                archived=False,
                pattern_type="error",
                reason=f"Anti-pattern archival failed: {str(e)}"
            )

    def get_top_patterns(self, n: int = 5) -> List[GoldenThinkingPattern]:
        """
        Retrieve top N most used golden patterns.
        
        These are the strongest neural pathways - patterns that have
        been validated and reused multiple times.
        """
        try:
            patterns = self.memory.get_thinking_patterns_by_usage(limit=n)
            self._stats["retrievals"] += 1
            logger.info(
                f"[ARCHIVER] Retrieved top {len(patterns)} patterns | "
                f"retrieval_count={self._stats['retrievals']} | "
                f"usage_range={patterns[-1].usage_count if patterns else 0}-{patterns[0].usage_count if patterns else 0}"
            )
            return patterns
        except Exception as e:
            logger.error(f"[ARCHIVER] Failed to retrieve patterns: {e}")
            return []

    def find_similar_patterns(self, content: str, threshold: float = 0.7) -> List[GoldenThinkingPattern]:
        """
        Find golden patterns similar to given content.
        
        Uses simple keyword matching for now. In production, this should
        use vector embeddings for semantic similarity.
        """
        try:
            all_patterns = self.memory.get_all_thinking_patterns()
            content_lower = content.lower()
            
            similar = []
            for pattern in all_patterns:
                # Simple keyword overlap scoring
                pattern_words = set(pattern.content_summary.lower().split())
                content_words = set(content_lower.split())
                
                if not pattern_words or not content_words:
                    continue
                
                overlap = len(pattern_words & content_words)
                score = overlap / max(len(pattern_words), len(content_words))
                
                if score >= threshold:
                    similar.append(pattern)
            
            # Sort by usage count (strength)
            similar.sort(key=lambda p: p.usage_count, reverse=True)
            logger.info(
                f"[ARCHIVER] Similar pattern search completed | "
                f"total_patterns={len(all_patterns)} | "
                f"similar_found={len(similar)} | "
                f"threshold={threshold:.2f}"
            )
            return similar[:10]
            
        except Exception as e:
            logger.error(f"[ARCHIVER] Failed to find similar patterns: {e}")
            return []

    def _check_existing_pattern(self, thought: EnhancedThought) -> Optional[GoldenThinkingPattern]:
        """Check if a similar pattern already exists."""
        try:
            # Check by thought_id first
            existing = self.memory.get_thinking_pattern_by_thought_id(thought.id)
            if existing:
                return existing
            
            # Check by content similarity
            similar = self.find_similar_patterns(thought.content, threshold=0.9)
            if similar:
                return similar[0]
            
            return None
        except Exception:
            return None

    def _increment_usage_count(self, pattern_id: str) -> None:
        """Increment the usage count of a pattern (LTP effect)."""
        try:
            pattern = self.memory.get_thinking_pattern_by_id(pattern_id)
            old_count = pattern.usage_count if pattern else 0
            self.memory.increment_pattern_usage(pattern_id)
            new_count = old_count + 1
            logger.info(
                f"[ARCHIVER] Pattern usage incremented (LTP effect) | "
                f"pattern_id={pattern_id} | "
                f"usage_count={old_count}->{new_count}"
            )
        except Exception as e:
            logger.warning(f"[ARCHIVER] Failed to increment usage for {pattern_id}: {e}")

    def _export_to_markdown(self, pattern: GoldenThinkingPattern, strategy_name: str):
        """Converts the pattern into a standardized Context Tree Markdown file."""
        topic = strategy_name.replace("_", "-").title()
        topic_dir = os.path.join(self.docs_root, topic)
        os.makedirs(topic_dir, exist_ok=True)

        # Ensure context.md exists for the topic
        self._ensure_context_md(self.docs_root, "Thinking Patterns", "Repository of elite cognitive patterns.")
        self._ensure_context_md(topic_dir, f"{topic} Patterns", f"Curated {topic} thinking patterns from active missions.")

        file_path = os.path.join(topic_dir, f"{pattern.id}.md")
        
        md_content = f"""---
title: "{pattern.content_summary[:100]}..."
tags: {pattern.tags}
tp_id: "{pattern.id}"
thought_id: "{pattern.thought_id}"
logic_score: {pattern.metrics.logical_coherence}
evidence_score: {pattern.metrics.evidence_strength}
---

# Golden Thinking Pattern: {pattern.id}

## Problem Context
> {pattern.full_content[:200]}...

## Cognitive Strategy: {topic}
{pattern.full_content}

## Metadata
- **Archived At:** {pattern.created_at}
- **Usage Count:** {pattern.usage_count}
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        logger.info(f"📄 Pattern Exported to Context Tree: {file_path}")

    def _ensure_context_md(self, directory: str, name: str, purpose: str):
        context_path = os.path.join(directory, "context.md")
        if not os.path.exists(context_path):
            content = f"# Domain: {name}\n\n## Purpose\n{purpose}\n\n## Scope\n- Elite cognitive strategies\n- Scalable problem-solving steps\n"
            with open(context_path, "w", encoding="utf-8") as f:
                f.write(content)

    def get_stats(self) -> Dict[str, Any]:
        """Get archiver statistics."""
        return {
            **self._stats,
            "tp_threshold": self.tp_threshold,
            "evidence_threshold": self.evidence_threshold
        }

    def reset_stats(self) -> None:
        """Reset archiver statistics."""
        self._stats = {
            "golden_archived": 0,
            "anti_archived": 0,
            "retrievals": 0
        }
