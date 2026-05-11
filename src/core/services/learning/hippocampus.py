"""
Digital Hippocampus: Architectural Style Learning Service

Implements the Strategic Human Assistance concept from whitepaper section 1:
- Learns the user's architectural style from interactions
- Auto-builds and refines mindset/soul prompts dynamically
- Provides fallback mechanism when configs/identity uses defaults
- Enables the AI to become a true cognitive partner that understands the human master

This is the missing "Strategic Human Assistance" feature that transforms CCT from
a helper to a cognitive partner that learns and adapts to the user's style.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict
import json
import os
import re

from src.core.models.domain import EnhancedThought, CCTSessionState
from src.core.services.user.identity import UserIdentityService
from src.engines.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


@dataclass
class StylePattern:
    """Learned architectural style pattern from user interactions."""
    pattern_id: str
    pattern_type: str  # 'preference', 'rejection', 'pattern'
    description: str
    examples: List[str] = field(default_factory=list)
    confidence: float = 0.0
    last_observed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    observation_count: int = 1


@dataclass
class LearnedIdentity:
    """Dynamically learned identity components."""
    learned_preferences: List[StylePattern] = field(default_factory=list)
    learned_rejections: List[StylePattern] = field(default_factory=list)
    learned_patterns: List[StylePattern] = field(default_factory=list)
    interaction_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class HippocampusService:
    """
    Digital Hippocampus Service for learning user's architectural style.

    Implements Strategic Human Assistance by:
    1. Analyzing user interactions to extract architectural preferences
    2. Building dynamic mindset/soul prompts based on learned patterns
    3. Providing fallback when static identity files are used
    4. Continuously refining the learned identity over time
    """

    def __init__(
        self,
        memory: MemoryManager,
        identity_service: UserIdentityService,
        learning_data_path: str = "database/learned_identity"
    ):
        self.memory = memory
        self.identity = identity_service
        self.learning_data_path = learning_data_path
        os.makedirs(learning_data_path, exist_ok=True)

        self.learned_identity = LearnedIdentity()
        self._load_learned_identity()

        logger.info("[HIPPOCAMPUS] Digital Hippocampus initialized for architectural style learning")

    def _load_learned_identity(self) -> None:
        """Load previously learned identity from disk."""
        try:
            learned_file = os.path.join(self.learning_data_path, "learned_identity.json")
            if os.path.exists(learned_file):
                with open(learned_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learned_identity = LearnedIdentity(
                        learned_preferences=[
                            StylePattern(**p) for p in data.get('learned_preferences', [])
                        ],
                        learned_rejections=[
                            StylePattern(**p) for p in data.get('learned_rejections', [])
                        ],
                        learned_patterns=[
                            StylePattern(**p) for p in data.get('learned_patterns', [])
                        ],
                        interaction_count=data.get('interaction_count', 0),
                        last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now(timezone.utc).isoformat()))
                    )
                logger.info(f"[HIPPOCAMPUS] Loaded {len(self.learned_identity.learned_preferences)} preferences, "
                           f"{len(self.learned_identity.learned_rejections)} rejections, "
                           f"{len(self.learned_identity.learned_patterns)} patterns")
        except Exception as e:
            logger.warning(f"[HIPPOCAMPUS] Failed to load learned identity: {e}. Starting fresh.")

    def _save_learned_identity(self) -> None:
        """Save learned identity to disk."""
        try:
            learned_file = os.path.join(self.learning_data_path, "learned_identity.json")
            data = {
                'learned_preferences': [
                    {
                        'pattern_id': p.pattern_id,
                        'pattern_type': p.pattern_type,
                        'description': p.description,
                        'examples': p.examples,
                        'confidence': p.confidence,
                        'last_observed': p.last_observed.isoformat(),
                        'observation_count': p.observation_count
                    }
                    for p in self.learned_identity.learned_preferences
                ],
                'learned_rejections': [
                    {
                        'pattern_id': p.pattern_id,
                        'pattern_type': p.pattern_type,
                        'description': p.description,
                        'examples': p.examples,
                        'confidence': p.confidence,
                        'last_observed': p.last_observed.isoformat(),
                        'observation_count': p.observation_count
                    }
                    for p in self.learned_identity.learned_rejections
                ],
                'learned_patterns': [
                    {
                        'pattern_id': p.pattern_id,
                        'pattern_type': p.pattern_type,
                        'description': p.description,
                        'examples': p.examples,
                        'confidence': p.confidence,
                        'last_observed': p.last_observed.isoformat(),
                        'observation_count': p.observation_count
                    }
                    for p in self.learned_identity.learned_patterns
                ],
                'interaction_count': self.learned_identity.interaction_count,
                'last_updated': self.learned_identity.last_updated.isoformat()
            }
            with open(learned_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug("[HIPPOCAMPUS] Learned identity saved to disk")
        except Exception as e:
            logger.error(f"[HIPPOCAMPUS] Failed to save learned identity: {e}")

    def analyze_session(self, session_id: str) -> LearnedIdentity:
        """
        Analyze a session to extract architectural style patterns.

        Uses offline Gemma 2B for pattern extraction when available,
        falls back to regex-based heuristics.

        This is called automatically when a session completes.
        """
        session = self.memory.get_session(session_id)
        if not session:
            logger.warning(f"[HIPPOCAMPUS] Session {session_id} not found")
            return self.learned_identity

        history = self.memory.get_session_history(session_id)
        if not history:
            logger.warning(f"[HIPPOCAMPUS] No history found for session {session_id}")
            return self.learned_identity

        logger.info(f"[HIPPOCAMPUS] Analyzing session {session_id} with {len(history)} thoughts")

        # Try offline LLM analysis first (smart tier routing)
        offline_result = None
        try:
            from src.core.llm_offline.engine import smart_analyze_session
            session_text = f"Problem: {session.problem_statement}\n\n"
            session_text += "\n\n".join([
                f"Thought {i+1} ({h.strategy.value}): {h.content[:300]}"
                for i, h in enumerate(history[:10])
            ])
            import asyncio
            offline_result = asyncio.run(smart_analyze_session(session_text))
            logger.info(f"[HIPPOCAMPUS] Smart analysis: tier={offline_result.get('tier_used')}, "
                       f"confidence={offline_result.get('confidence', 0):.2f}")
        except Exception as e:
            logger.warning(f"[HIPPOCAMPUS] Smart analysis unavailable: {e}")

        # Analyze thoughts for patterns (existing heuristic)
        for thought in history:
            self._analyze_thought(thought)

        # Incorporate offline LLM insights if available
        if offline_result and offline_result.get("status") == "success":
            self._incorporate_offline_insights(offline_result)

        self.learned_identity.interaction_count += len(history)
        self.learned_identity.last_updated = datetime.now(timezone.utc)
        self._save_learned_identity()

        logger.info(f"[HIPPOCAMPUS] Session analysis complete. "
                   f"Total preferences: {len(self.learned_identity.learned_preferences)}, "
                   f"Total rejections: {len(self.learned_identity.learned_rejections)}, "
                   f"Total patterns: {len(self.learned_identity.learned_patterns)}")

        return self.learned_identity

    def _incorporate_offline_insights(self, offline_result: Dict[str, Any]) -> None:
        """Merge offline LLM insights into learned identity (supports smart tier format)."""
        # Try smart tier format first (nested under 'content'), then flat
        content = offline_result.get("content", offline_result)
        if isinstance(content, str):
            try:
                import json
                content = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                content = offline_result

        preferences = content.get("preferences", content.get("architectural_patterns", []))
        for pref in preferences:
            if isinstance(pref, str):
                self._add_pattern("preference", pref, "offline_llm_extracted", impact_factor=0.8)

        rejections = content.get("rejections", [])
        for rej in rejections:
            if isinstance(rej, str):
                self._add_pattern("rejection", rej, "offline_llm_extracted", impact_factor=0.7)

        persona_hints = content.get("user_persona_hints", content.get("persona_hints", []))
        for hint in persona_hints:
            if isinstance(hint, str):
                self._add_pattern("pattern", f"persona_hint: {hint}", "offline_llm_extracted", impact_factor=0.6)

        tier = offline_result.get("tier_used", 1)
        logger.info(f"[HIPPOCAMPUS] Incorporated insights from Tier {tier}: "
                   f"{len(preferences)} prefs, {len(rejections)} rejs, {len(persona_hints)} hints")

    def _analyze_thought(self, thought: EnhancedThought) -> None:
        """
        Analyze a single thought for architectural style patterns.

        Uses regex for better boundary matching and adjusts pattern confidence
        based on the thought's logical coherence and clarity metrics.
        """
        content_lower = thought.content.lower()

        # Calculate impact factor based on metrics (0.5 to 1.5)
        impact_factor = 1.0
        if thought.metrics:
            impact_factor = (thought.metrics.logical_coherence + thought.metrics.clarity_score) / 2.0
            impact_factor = max(0.5, min(1.5, impact_factor * 1.5))

        # Detect architectural preferences
        preference_patterns = {
            r'\bddd\b': 'Domain-Driven Design',
            r'\bclean architecture\b': 'Clean Architecture',
            r'\bsolid\b': 'SOLID principles',
            r'\bmicroservices?\b': 'Microservices',
            r'\bevent-driven\b': 'Event-driven architecture',
            r'\bcqrs\b': 'CQRS pattern',
            r'\bhexagonal\b': 'Hexagonal architecture',
            r'\bmodular\b': 'Modular design',
            r'\btestable\b': 'Testable code',
            r'\btype-safe\b': 'Type safety',
            r'\bentereprise-grade\b': 'Enterprise-grade quality'
        }

        for p_regex, description in preference_patterns.items():
            if re.search(p_regex, content_lower):
                self._add_pattern('preference', description, thought.content, impact_factor)

        # Detect architectural rejections (anti-patterns)
        rejection_patterns = {
            r'\bspaghetti\b': 'Spaghetti code',
            r'\bgod object\b': 'God Object anti-pattern',
            r'\btight coupling\b': 'Tight coupling',
            r'\bhardcoded\b': 'Hardcoded values',
            r'\bmagic numbers?\b': 'Magic numbers',
            r'\bglobal state\b': 'Global state',
            r'\bmonolithic\b': 'Monolithic architecture (when rejected)',
            r'\bstub\b': 'Stub code rejection'
        }

        for r_regex, rejection in rejection_patterns.items():
            if re.search(r_regex, content_lower):
                self._add_pattern('rejection', rejection, thought.content, impact_factor)

        # Detect thought type patterns
        if thought.thought_type.value == 'evaluation':
            self._add_pattern('pattern', 'Critical evaluation mindset', thought.content, impact_factor)
        elif thought.thought_type.value == 'synthesis':
            self._add_pattern('pattern', 'Synthesis and integration', thought.content, impact_factor)
        elif thought.thought_type.value == 'research':
            self._add_pattern('pattern', 'Deep research oriented', thought.content, impact_factor)

    def _add_pattern(self, pattern_type: str, description: str, example: str, impact_factor: float = 1.0) -> None:
        """Add or update a pattern in the learned identity."""
        pattern_id = f"{pattern_type}_{hash(description)}"

        # Find existing pattern
        if pattern_type == 'preference':
            patterns = self.learned_identity.learned_preferences
        elif pattern_type == 'rejection':
            patterns = self.learned_identity.learned_rejections
        else:
            patterns = self.learned_identity.learned_patterns

        for pattern in patterns:
            if pattern.pattern_id == pattern_id:
                # Update existing pattern
                pattern.observation_count += 1
                pattern.confidence = min(1.0, pattern.confidence + (0.1 * impact_factor))
                pattern.last_observed = datetime.now(timezone.utc)
                if example not in pattern.examples:
                    pattern.examples.append(example[:200])  # Truncate example
                return

        # Add new pattern
        new_pattern = StylePattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            description=description,
            examples=[example[:200]],
            confidence=min(1.0, 0.5 * impact_factor),
            last_observed=datetime.now(timezone.utc),
            observation_count=1
        )
        patterns.append(new_pattern)

    def generate_dynamic_mindset(self) -> str:
        """
        Generate a dynamic USER_MINDSET based on learned patterns.

        This provides the auto-build prompt capability when the static
        configs/identity files use defaults.
        """
        if not self.learned_identity.learned_preferences:
            logger.info("[HIPPOCAMPUS] No learned preferences, returning default mindset")
            return None  # Use static default

        mindset_lines = ["# 🧠 LEARNED USER_MINDSET: Dynamic Architectural DNA\n"]
        mindset_lines.append("## Learned Architectural Preferences\n")

        # Group preferences by confidence
        high_confidence = [p for p in self.learned_identity.learned_preferences if p.confidence >= 0.7]
        medium_confidence = [p for p in self.learned_identity.learned_preferences if 0.5 <= p.confidence < 0.7]

        if high_confidence:
            mindset_lines.append("### Strong Preferences (High Confidence)")
            for pattern in high_confidence:
                mindset_lines.append(f"- **{pattern.description}** (confidence: {pattern.confidence:.2f})")
                if pattern.examples:
                    mindset_lines.append(f"  - Example: {pattern.examples[0]}")

        if medium_confidence:
            mindset_lines.append("\n### Emerging Preferences (Medium Confidence)")
            for pattern in medium_confidence:
                mindset_lines.append(f"- **{pattern.description}** (confidence: {pattern.confidence:.2f})")

        # Add learned rejections
        if self.learned_identity.learned_rejections:
            mindset_lines.append("\n## Architectural Rejections (Anti-Patterns)")
            for pattern in self.learned_identity.learned_rejections:
                mindset_lines.append(f"- 🚫 **{pattern.description}** (confidence: {pattern.confidence:.2f})")

        # Add learned patterns
        if self.learned_identity.learned_patterns:
            mindset_lines.append("\n## Cognitive Patterns")
            for pattern in self.learned_identity.learned_patterns:
                mindset_lines.append(f"- **{pattern.description}** (confidence: {pattern.confidence:.2f})")

        mindset_lines.append(f"\n*Generated from {self.learned_identity.interaction_count} interactions*")

        dynamic_mindset = "\n".join(mindset_lines)
        logger.info(f"[HIPPOCAMPUS] Generated dynamic mindset ({len(dynamic_mindset)} characters)")

        return dynamic_mindset

    def generate_dynamic_soul(self) -> str:
        """
        Generate a dynamic CCT_SOUL based on learned patterns.

        This provides the auto-build prompt capability for the digital twin persona.
        """
        if not self.learned_identity.learned_patterns:
            logger.info("[HIPPOCAMPUS] No learned patterns, returning default soul")
            return None  # Use static default

        soul_lines = ["# 🧬 LEARNED CCT_SOUL: Dynamic Digital Twin Persona\n"]
        soul_lines.append("## Learned Interaction Style\n")

        # Analyze patterns to determine interaction style
        critical_count = len([p for p in self.learned_identity.learned_patterns if 'critical' in p.description.lower()])
        synthesis_count = len([p for p in self.learned_identity.learned_patterns if 'synthesis' in p.description.lower()])

        if critical_count > synthesis_count:
            soul_lines.append("### Critical Thinking Style")
            soul_lines.append("You adopt a highly critical, analytical approach to architectural decisions.")
            soul_lines.append("You prioritize identifying flaws, vulnerabilities, and edge cases.")
        elif synthesis_count > critical_count:
            soul_lines.append("### Integrative Thinking Style")
            soul_lines.append("You excel at synthesizing multiple perspectives into cohesive solutions.")
            soul_lines.append("You prioritize finding common patterns and resolving contradictions.")
        else:
            soul_lines.append("### Balanced Thinking Style")
            soul_lines.append("You balance critical analysis with integrative synthesis.")
            soul_lines.append("You adapt your approach based on the task requirements.")

        # Add learned rejections as "allergies"
        if self.learned_identity.learned_rejections:
            soul_lines.append("\n## Architectural Allergies")
            soul_lines.append("You have zero tolerance for the following anti-patterns:")
            for pattern in self.learned_identity.learned_rejections:
                if pattern.confidence >= 0.7:
                    soul_lines.append(f"- 🚫 **{pattern.description}** - Reject immediately")
                else:
                    soul_lines.append(f"- ⚠️ **{pattern.description}** - Be skeptical")

        soul_lines.append(f"\n*Persona refined from {self.learned_identity.interaction_count} interactions*")

        dynamic_soul = "\n".join(soul_lines)
        logger.info(f"[HIPPOCAMPUS] Generated dynamic soul ({len(dynamic_soul)} characters)")

        return dynamic_soul

    def get_enhanced_identity(self) -> Dict[str, str]:
        """
        Get enhanced identity with learned patterns.

        Returns:
            Dict with 'user_mindset' and 'cct_soul', either:
            - Dynamic (if enough learning data)
            - Static (fallback to defaults)
            - Hybrid (static + dynamic enhancements)
        """
        static_identity = self.identity.load_identity()

        dynamic_mindset = self.generate_dynamic_mindset()
        dynamic_soul = self.generate_dynamic_soul()

        # Determine which to use
        if dynamic_mindset and dynamic_soul:
            # Use dynamic if we have enough data
            if self.learned_identity.interaction_count >= 10:
                logger.info("[HIPPOCAMPUS] Using fully dynamic identity")
                return {
                    'user_mindset': dynamic_mindset,
                    'cct_soul': dynamic_soul,
                    'source': 'dynamic'
                }
            else:
                # Use hybrid (static + dynamic)
                logger.info("[HIPPOCAMPUS] Using hybrid identity (static + dynamic)")
                hybrid_mindset = f"{static_identity.get('user_mindset', '')}\n\n{dynamic_mindset}"
                hybrid_soul = f"{static_identity.get('cct_soul', '')}\n\n{dynamic_soul}"
                return {
                    'user_mindset': hybrid_mindset,
                    'cct_soul': hybrid_soul,
                    'source': 'hybrid'
                }
        else:
            # Use static
            logger.info("[HIPPOCAMPUS] Using static identity (no learning data)")
            return {
                'user_mindset': static_identity.get('user_mindset'),
                'cct_soul': static_identity.get('cct_soul'),
                'source': 'static'
            }

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about the learning process."""
        return {
            'interaction_count': self.learned_identity.interaction_count,
            'preference_count': len(self.learned_identity.learned_preferences),
            'rejection_count': len(self.learned_identity.learned_rejections),
            'pattern_count': len(self.learned_identity.learned_patterns),
            'last_updated': self.learned_identity.last_updated.isoformat(),
            'high_confidence_preferences': len([p for p in self.learned_identity.learned_preferences if p.confidence >= 0.7]),
            'high_confidence_rejections': len([p for p in self.learned_identity.learned_rejections if p.confidence >= 0.7])
        }

    def infer_current_context(self, problem_statement: str = "") -> Dict[str, Any]:
        learned = self.learned_identity

        critical_count = len([p for p in learned.learned_patterns if 'critical' in p.description.lower()])
        synthesis_count = len([p for p in learned.learned_patterns if 'synthesis' in p.description.lower()])

        has_architecture_bias = any(
            p.confidence >= 0.7
            and p.description in {"Domain-Driven Design", "Clean Architecture", "Hexagonal architecture", "Modular design"}
            for p in learned.learned_preferences
        )
        persona = "principal-architect" if has_architecture_bias else None

        raw_text = " ".join(
            [
                *(e for p in learned.learned_preferences for e in (p.examples or [])),
                *(e for p in learned.learned_patterns for e in (p.examples or [])),
            ]
        ).lower()
        has_test_signal = bool(re.search(r"\bpytest\b|\bjunit\b|\bvitest\b|\bgo test\b|\btests?\b", raw_text))
        has_security_signal = bool(re.search(r"\bsecurity\b|\bthreat\b|\bzero[- ]trust\b|\bpii\b|\bsecrets?\b", raw_text))

        habit = None
        habit_confidence = 0.0
        eval_pattern = next(
            (p for p in learned.learned_patterns if p.description.lower() == "critical evaluation mindset"),
            None,
        )
        if eval_pattern and eval_pattern.confidence >= 0.55:
            habit = "eval-first"
            habit_confidence = float(eval_pattern.confidence)
        if has_test_signal:
            habit = "tdd-first"
            habit_confidence = max(habit_confidence, 0.65)

        behaviour = "security-first" if has_security_signal else None

        signals: List[Dict[str, Any]] = []
        if persona:
            signals.append({"type": "persona", "value": persona, "confidence": 0.65})
        if habit:
            signals.append({"type": "habit", "value": habit, "confidence": habit_confidence})
        if behaviour:
            signals.append({"type": "behaviour", "value": behaviour, "confidence": 0.6})

        if critical_count + synthesis_count > 0:
            if critical_count > synthesis_count:
                signals.append({"type": "reasoning_bias", "value": "critical", "confidence": 0.55})
            elif synthesis_count > critical_count:
                signals.append({"type": "reasoning_bias", "value": "integrative", "confidence": 0.55})
            else:
                signals.append({"type": "reasoning_bias", "value": "balanced", "confidence": 0.45})

        confidence = 0.0
        if signals:
            confidence = sum(float(s.get("confidence", 0.0) or 0.0) for s in signals) / len(signals)

        very_low = 0.15
        low = 0.35
        decision = "fallback_balanced"
        needs_confirmation = False
        confirmation_question = None

        if confidence < very_low:
            decision = "ask_confirmation"
            needs_confirmation = True
            confirmation_question = (
                "I can't confidently infer your active persona/habit right now. "
                "Do you want me to run in mimic_user mode (and if yes, which persona/habit)?"
            )
        elif confidence >= low:
            decision = "mimic"

        reasoning_priors = (
            "Reasoning structure (mimic candidate): "
            "index evidence → analyze tradeoffs → systematic debugging → minimal patch → targeted tests. "
            "Use evidence links (file:line) for claims and avoid leaking secrets."
        )
        if critical_count > synthesis_count:
            reasoning_priors = (
                f"{reasoning_priors} "
                "Bias toward adversarial review and edge-case enumeration before concluding."
            )
        elif synthesis_count > critical_count:
            reasoning_priors = (
                f"{reasoning_priors} "
                "Bias toward consolidating multiple perspectives into a single coherent plan."
            )

        if problem_statement:
            reasoning_priors = f"{reasoning_priors} Problem focus: {problem_statement[:160]}"

        return {
            "persona": persona,
            "habit": habit,
            "behaviour": behaviour,
            "confidence": round(confidence, 4),
            "decision": decision,
            "signals": signals,
            "needs_confirmation": needs_confirmation,
            "confirmation_question": confirmation_question,
            "reasoning_priors": reasoning_priors,
        }

    def record_context_confirmation(
        self,
        persona: Optional[str],
        habit: Optional[str],
        behaviour: Optional[str],
        example: str = "",
        impact_factor: float = 1.2,
    ) -> None:
        parts: List[str] = []
        if persona:
            parts.append(f"persona:{persona}")
        if habit:
            parts.append(f"habit:{habit}")
        if behaviour:
            parts.append(f"behaviour:{behaviour}")

        if not parts:
            return

        description = "Confirmed active context: " + " ".join(parts)
        self._add_pattern("pattern", description, example or description, impact_factor=impact_factor)
        self.learned_identity.interaction_count += 1
        self.learned_identity.last_updated = datetime.now(timezone.utc)
        self._save_learned_identity()
