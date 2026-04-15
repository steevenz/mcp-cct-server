import logging
from typing import List, Set, Dict, Optional
from src.core.models.enums import ThinkingStrategy
from src.core.services.analysis.complexity import ComplexityService

logger = logging.getLogger(__name__)

class PolicyService:
    """
    PipelinePolicyManager: Domain Policy for Selecting Cognitive Strategies.
    
    Analyzes problem statements to recommend optimal cognitive strategy sequences.
    Advanced version: Supports multi-scenario weighted detection and Sovereign Deep Pipelines.
    
    [DDD] This is a Domain Policy that governs the intelligence routing flow.
    """

    def __init__(self, complexity_service: ComplexityService = None):
        self.complexity_service = complexity_service or ComplexityService()

    # Configurable keyword sets for category detection
    KEYWORDS: Dict[str, Set[str]] = {
        "DEBUG": {"bug", "fix", "error", "issue", "crash", "failed", "debug", "exception", "traceback"},
        "ARCH": {"arch", "structure", "design", "refactor", "engine", "system", "framework", "schema", "scaling"},
        "FEAT": {"feature", "implement", "add", "new", "create", "build", "develop", "functionality"},
        "SEC": {"security", "hack", "vulnerability", "auth", "harden", "encrypt", "protect", "injection", "cve"},
        "BIZ": {"market", "business", "strategy", "cost", "token", "price", "revenue", "profit", "roi", "product"},
        "PLAN": {"plan", "reason", "step-by-step", "recursive", "branching", "sequence", "workflow", "automated", "autonomous"},
        "ENGINEERING": {"refactor", "optimize", "architecture", "test", "eval", "benchmark", "agentic", "implementation"}
    }

    # Standardized deep reasoning sequence for COMPLEX/SOVEREIGN tasks
    # [SOVEREIGN INTEL WHITEV5] Optimized 9-Phase Pipeline
    SOVEREIGN_PIPELINE = [
        ThinkingStrategy.EMPIRICAL_RESEARCH,    # Phase 1: Fact Gathering
        ThinkingStrategy.FIRST_PRINCIPLES,     # Phase 2: Fundamental Assumptions
        ThinkingStrategy.ACTOR_CRITIC_LOOP,    # Phase 3: Internal Debate (Dual-Phase)
        ThinkingStrategy.COUNCIL_OF_CRITICS,   # Phase 4: Multi-Domain Review (Tri-Persona)
        ThinkingStrategy.SYSTEMIC,             # Phase 5: Holistic Connectivity
        ThinkingStrategy.UNCONVENTIONAL_PIVOT, # Phase 6: Paradigm Breaking
        ThinkingStrategy.LONG_TERM_HORIZON,    # Phase 7: Strategic Impact (Checkpoint)
        ThinkingStrategy.MULTI_AGENT_FUSION,   # Phase 8: Final Synthesis
        ThinkingStrategy.POST_MISSION_LEARNING # Phase 9: Evolutionary Archive
    ]

    # Persona mapping for Council of Critics based on detected domains
    DOMAIN_PERSONAS = {
        "ARCH": "System Architect",
        "SEC": "Security Auditor",
        "BIZ": "Product Strategist",
        "DEBUG": "Lead Debugger",
        "FEAT": "UX Specialist",
        "GENERIC": "Critical Reviewer"
    }

    # Mapping Categories to Strategy Sequences (Moderate/Default)
    PIPELINE_TEMPLATES = {
        "DEBUG": [
            ThinkingStrategy.SELF_DEBUGGING,
            ThinkingStrategy.EMPIRICAL_RESEARCH,
            ThinkingStrategy.ABDUCTIVE,
            ThinkingStrategy.FIRST_PRINCIPLES,
            ThinkingStrategy.ACTOR_CRITIC_LOOP
        ],
        "ARCH": [
            ThinkingStrategy.BRAINSTORMING,
            ThinkingStrategy.ENGINEERING_DECONSTRUCTION,
            ThinkingStrategy.FIRST_PRINCIPLES,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.COUNCIL_OF_CRITICS,
            # NOTE: ARCH pipeline includes POST_MISSION_LEARNING to capture architectural patterns
            # and design decisions for future reuse. Architecture decisions have high ROI value
            # when archived as Golden Thinking Patterns for similar structural challenges.
            ThinkingStrategy.POST_MISSION_LEARNING
        ],
        "FEAT": [
            ThinkingStrategy.BRAINSTORMING,
            ThinkingStrategy.ENGINEERING_DECONSTRUCTION,
            ThinkingStrategy.SYSTEMATIC,
            ThinkingStrategy.ACTOR_CRITIC_LOOP,
            ThinkingStrategy.POST_MISSION_LEARNING
        ],
        "SEC": [
            ThinkingStrategy.CRITICAL,
            ThinkingStrategy.ACTOR_CRITIC_LOOP,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.POST_MISSION_LEARNING
        ],
        "BIZ": [
            ThinkingStrategy.SWOT_ANALYSIS,
            ThinkingStrategy.SECOND_ORDER_THINKING,
            ThinkingStrategy.LONG_TERM_HORIZON,
            ThinkingStrategy.POST_MISSION_LEARNING
        ],
        "PLAN": [
            ThinkingStrategy.PLAN_AND_EXECUTE,
            ThinkingStrategy.REACT,
            ThinkingStrategy.TREE_OF_THOUGHTS,
            ThinkingStrategy.POST_MISSION_LEARNING
        ],
        "ENGINEERING": [
            ThinkingStrategy.BRAINSTORMING,
            ThinkingStrategy.ENGINEERING_DECONSTRUCTION,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.DEDUCTIVE_VALIDATION,
            ThinkingStrategy.POST_MISSION_LEARNING
        ]
    }

    @classmethod
    def detect_categories(cls, problem_statement: str) -> Dict[str, float]:
        """Calculates weighted scores for all domains."""
        text = problem_statement.lower()
        scores = {}
        
        for cat, keywords in cls.KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                scores[cat] = min(0.3 + (matches * 0.15), 1.0)
        
        return scores

    @classmethod
    def detect_category(cls, problem_statement: str) -> str:
        """Returns the primary category name."""
        scores = cls.detect_categories(problem_statement)
        if not scores:
            return "GENERIC"
        return max(scores, key=scores.get)

    @classmethod
    def get_personas_for_domains(cls, detected_categories: Dict[str, float]) -> List[str]:
        """Selects up to 3 personas based on weighted domains."""
        sorted_cats = sorted(detected_categories.items(), key=lambda x: x[1], reverse=True)
        top_cats = [cat for cat, score in sorted_cats[:3]]
        
        personas = [cls.DOMAIN_PERSONAS.get(cat, "Critical Reviewer") for cat in top_cats]
        if not personas:
            personas = ["Critical Reviewer"]
        return personas

    def select_pipeline(self, problem_statement: str, complexity: str) -> List[ThinkingStrategy]:
        """
        Select the optimal pipeline based on problem statement and complexity level.
        
        Args:
            problem_statement: The problem to analyze
            complexity: Complexity level (simple, moderate, complex, sovereign)
            
        Returns:
            List of ThinkingStrategy for the pipeline
        """
        complexity = complexity.lower()
        
        # SOVEREIGN/COMPLEX: Always use Sovereign Pipeline
        if complexity in ("complex", "sovereign"):
            return self.SOVEREIGN_PIPELINE
        
        # MODERATE/SIMPLE: Use category-based templates
        primary_category = self.detect_category(problem_statement)
        template = self.PIPELINE_TEMPLATES.get(primary_category, [])
        
        if template:
            return template
        
        # Fallback: Generic moderate pipeline
        return [
            ThinkingStrategy.EMPIRICAL_RESEARCH,
            ThinkingStrategy.FIRST_PRINCIPLES,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.INTEGRATIVE
        ]

# Alias for backward compatibility during migration
PipelineSelector = PolicyService
