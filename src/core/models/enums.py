from enum import Enum

class ThinkingStrategy(str, Enum):
    """List of available thinking strategies."""
    
    # --- Primitive Modes (The Workers) ---
    LINEAR = "linear"
    TREE = "tree"
    DIALECTICAL = "dialectical"
    SYSTEMATIC = "systematic"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    METACOGNITIVE = "metacognitive"
    CRITICAL = "critical"
    SYSTEMIC = "systemic"
    LATERAL = "lateral"
    STRATEGIC = "strategic"
    EMPATHETIC = "empathetic"
    ABSTRACT = "abstract"
    PRACTICAL = "practical"
    INTEGRATIVE = "integrative"
    EVOLUTIONARY = "evolutionary"
    CONVERGENT = "convergent"
    DIVERGENT = "divergent"
    REFLECTIVE = "reflective"
    TEMPORAL = "temporal"
    ACTOR_CRITIC = "actor_critic"
    
    # Advanced Primitives (Added)
    FIRST_PRINCIPLES = "first_principles"
    ABDUCTIVE = "abductive"
    COUNTERFACTUAL = "counterfactual"
    EMPIRICAL_RESEARCH = "empirical_research"
    ANALOGICAL_TRANSFER = "analogical_transfer"
    ADVERSARIAL_SIMULATION = "adversarial_simulation"
    DEDUCTIVE_VALIDATION = "deductive_validation"
    SYNTHESIS = "synthesis" # Adding synthesis as a strategy if it's used as a step
    
    # Strategic & Business Primitives
    SWOT_ANALYSIS = "swot_analysis"
    FIRST_PRINCIPLES_ECON = "first_principles_econ"
    SECOND_ORDER_THINKING = "second_order_thinking"

    # --- CCT Hybrid Modes (The Orchestrators) ---
    ACTOR_CRITIC_LOOP = "actor_critic_loop"
    UNCONVENTIONAL_PIVOT = "unconventional_pivot"
    LONG_TERM_HORIZON = "long_term_horizon"
    MULTI_AGENT_FUSION = "multi_agent_fusion"

class ThoughtType(str, Enum):
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"
    CONCLUSION = "conclusion"
    QUESTION = "question"
    METACOGNITION = "metacognition"
    PLAN = "plan"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"

class ConfidenceLevel(int, Enum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5

class CCTProfile(str, Enum):
    BALANCED = "balanced"
    CREATIVE_FIRST = "creative_first"
    CRITICAL_FIRST = "critical_first"
    DEEP_RECURSIVE = "deep_recursive"
