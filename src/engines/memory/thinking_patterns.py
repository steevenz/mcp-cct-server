import os
import uuid
import logging
import json
from datetime import datetime
from typing import Optional
from src.core.models.domain import EnhancedThought, GoldenThinkingPattern, CCTSessionState
from src.engines.memory.manager import MemoryManager

logger = logging.getLogger(__name__)

class PatternArchiver:
    """
    Implements the 'Golden Thinking Pattern Auto-Archiving' logic.
    Identifies elite cognitive strategies and persists them to the global TP repository.
    """
    def __init__(self, memory: MemoryManager, docs_root: str = "docs/context-tree/Thinking-Patterns"):
        self.memory = memory
        self.docs_root = docs_root
        os.makedirs(self.docs_root, exist_ok=True)

    def process_thought(self, session: CCTSessionState, thought: EnhancedThought) -> Optional[GoldenThinkingPattern]:
        """
        Evaluates if a thought is worthy of becoming a Golden Thinking Pattern.
        """
        # Threshold Logic: Consistency > 0.9 and Evidence > 0.8
        if thought.metrics.logical_coherence <= 0.9 or thought.metrics.evidence_strength <= 0.8:
            return None

        logger.info(f"✨ Golden Thinking Pattern Candidate Detected: {thought.id} (Logic: {thought.metrics.logical_coherence})")

        # 2. Create GoldenThinkingPattern Record
        tp_id = f"TP_{uuid.uuid4().hex[:8]}"
        pattern = GoldenThinkingPattern(
            id=tp_id,
            thought_id=thought.id,
            session_id=session.session_id,
            original_problem=session.problem_statement,
            summary=thought.summary or "Elite cognitive pattern",
            content=thought.content,
            metrics=thought.metrics,
            tags=thought.tags,
            usage_count=1,
            timestamp=datetime.now()
        )

        # 3. Persist to Global Memory (SQLite)
        self.memory.save_thinking_pattern(pattern)
        thought.is_thinking_pattern = True
        
        # 4. Export to Context Tree (Markdown)
        self._export_to_markdown(pattern, thought.strategy.value)

        return pattern

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
title: "{pattern.summary[:100]}..."
tags: {pattern.tags}
tp_id: "{pattern.id}"
thought_id: "{pattern.thought_id}"
logic_score: {pattern.metrics.logical_coherence}
evidence_score: {pattern.metrics.evidence_strength}
---

# Golden Thinking Pattern: {pattern.id}

## Problem Context
> {pattern.original_problem}

## Cognitive Strategy: {topic}
{pattern.content}

## Metadata
- **Archived At:** {pattern.timestamp}
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
