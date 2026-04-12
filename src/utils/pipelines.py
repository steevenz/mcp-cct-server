import logging
from typing import List
from src.core.models.enums import ThinkingStrategy

logger = logging.getLogger(__name__)

class PipelineSelector:
    """
    Analyzes problem statements to recommend optimal cognitive strategy sequences.
    Implemented as a heuristic mapper (POC) with future expansion for LLM-based routing.
    """

    # Mapping Categories to Strategy Sequences
    PIPELINE_TEMPLATES = {
        "DEBUG": [
            ThinkingStrategy.EMPIRICAL_RESEARCH,
            ThinkingStrategy.ABDUCTIVE,
            ThinkingStrategy.FIRST_PRINCIPLES,
            ThinkingStrategy.ACTOR_CRITIC_LOOP
        ],
        "ARCH": [
            ThinkingStrategy.FIRST_PRINCIPLES,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.LONG_TERM_HORIZON,
            ThinkingStrategy.MULTI_AGENT_FUSION
        ],
        "FEAT": [
            ThinkingStrategy.LATERAL,
            ThinkingStrategy.CONVERGENT,
            ThinkingStrategy.PRACTICAL
        ],
        "SEC": [
            ThinkingStrategy.CRITICAL,
            ThinkingStrategy.ACTOR_CRITIC_LOOP,
            ThinkingStrategy.SYSTEMIC
        ],
        "BIZ": [
            ThinkingStrategy.SWOT_ANALYSIS,
            ThinkingStrategy.SECOND_ORDER_THINKING,
            ThinkingStrategy.LONG_TERM_HORIZON
        ]
    }

    @classmethod
    def detect_category(cls, problem_statement: str) -> str:
        text = problem_statement.lower()

        if any(w in text for w in ["bug", "fix", "error", "issue", "crash", "failed"]):
            return "DEBUG"
        if any(w in text for w in ["arch", "structure", "design", "refactor", "engine"]):
            return "ARCH"
        if any(w in text for w in ["feature", "implement", "add", "new", "create"]):
            return "FEAT"
        if any(w in text for w in ["security", "hack", "vulnerability", "auth", "harden"]):
            return "SEC"
        if any(w in text for w in ["market", "business", "strategy", "cost", "token"]):
            return "BIZ"

        return "GENERIC"

    @classmethod
    def select_pipeline(cls, problem_statement: str) -> List[ThinkingStrategy]:
        """
        Categorizes the problem and returns the matching pipeline.
        Defaults to a balanced sequence if no category matches.
        """
        category = cls.detect_category(problem_statement)
        if category == "GENERIC":
            logger.info("No specific category detected. Using Balanced Generic Pipeline.")
            return [
                ThinkingStrategy.FIRST_PRINCIPLES,
                ThinkingStrategy.ACTOR_CRITIC_LOOP,
                ThinkingStrategy.SYSTEMIC,
                ThinkingStrategy.INTEGRATIVE,
            ]

        logger.info(f"Problem categorized as {category}. Selecting specialized pipeline.")
        return cls.PIPELINE_TEMPLATES.get(category, [])
