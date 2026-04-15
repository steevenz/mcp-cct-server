import logging
from typing import List, Dict, Any, Set
from src.core.models.enums import ThinkingStrategy

logger = logging.getLogger(__name__)

class ActionSkill:
    """Represents a tactical capability (tool/skill) that can be injected."""
    def __init__(self, name: str, description: str, tool_mapping: List[str] = None):
        self.name = name
        self.description = description
        self.tool_mapping = tool_mapping or []

class SkillsLoader:
    """
    Handles dynamic loading and injection of Action Skills based on strategy.
    
    Reference: Whitepaper.md Section 7 - Hybrid Knowledge Ecosystem
    """

    # Static mapping for the POC
    STRATEGY_SKILL_MAP: Dict[ThinkingStrategy, List[ActionSkill]] = {
        ThinkingStrategy.EMPIRICAL_RESEARCH: [
            ActionSkill("WebAudit", "Ability to perform deep web search and documentation retrieval.", ["search_web", "read_url_content"]),
            ActionSkill("CVEResearch", "Focused search for security vulnerabilities and CVE database lookups.", ["search_web"])
        ],
        ThinkingStrategy.ADVERSARIAL_SIMULATION: [
            ActionSkill("ThreatModeler", "Structural analysis of attack vectors and boundary weaknesses.", []),
            ActionSkill("SecurityScanner", "Mock implementation of static/dynamic security analysis tools.", [])
        ],
        ThinkingStrategy.SYSTEMIC: [
            ActionSkill("GraphViz", "Visualizing complex system dependencies and component hierarchies.", []),
            ActionSkill("DataFlowAnalysis", "Tracing data transformation across system boundaries.", [])
        ],
        ThinkingStrategy.FIRST_PRINCIPLES: [
            ActionSkill("ConstraintSolver", "Identifying and isolating irreducible system constraints.", []),
            ActionSkill("AssumptionAudit", "Deconstructing complex problems into validated facts.", [])
        ],
        ThinkingStrategy.REACT: [
            ActionSkill("DynamicReasoning", "Thought-Action-Observation loop for adaptive tasks.", ["search_web", "read_url_content"]),
            ActionSkill("AdaptiveExecution", "Adjusting plans in real-time based on environmental feedback.", [])
        ],
        ThinkingStrategy.REWOO: [
            ActionSkill("PredictivePlanning", "Upfront logical dependency mapping for efficiency.", []),
            ActionSkill("ParallelExecution", "Identifying tasks that can be run concurrently.", [])
        ],
        ThinkingStrategy.TREE_OF_THOUGHTS: [
            ActionSkill("BranchingLogic", "Exploring multiple reasoning paths simultaneously.", []),
            ActionSkill("PathEvaluation", "Scoring and pruning reasoning branches based on coherence.", [])
        ],
        ThinkingStrategy.PLAN_AND_EXECUTE: [
            ActionSkill("StructuredDecomposition", "Breaking complex tasks into manageable sub-goals.", []),
            ActionSkill("SequentialExecution", "Maintaining state across multi-step technical workflows.", [])
        ],
        ThinkingStrategy.CHAIN_OF_THOUGHT: [
            ActionSkill("TransparentReasoning", "Step-by-step logical decomposition for human auditability.", []),
            ActionSkill("LogicalValidation", "Ensuring each reasoning step follows from the previous.", [])
        ],
        ThinkingStrategy.ENGINEERING_DECONSTRUCTION: [
            ActionSkill("EvalArchitect", "Defining capability and regression evals before implementation.", []),
            ActionSkill("TaskDecomposer", "Applying the 15-minute unit rule to break down complex tasks.", []),
            ActionSkill("ModelRouter", "Optimizing performance by routing tasks to Haiku, Sonnet, or Opus tiers.", ["get_health"])
        ],
        ThinkingStrategy.SELF_DEBUGGING: [
            ActionSkill("FailureCapture", "Recording error logs, tool sequences, and context pressure snapshot.", []),
            ActionSkill("RootCauseDiagnostician", "Identifying the logical or state failure patterns behind errors.", []),
            ActionSkill("ContainedRecoverer", "Executing minimal, safe recovery actions to break loops or drift.", []),
            ActionSkill("IntrospectionReporter", "Producing human-readable debug logs for audit and future learning.", [])
        ],
        ThinkingStrategy.BRAINSTORMING: [
            ActionSkill("SocraticGate", "Mandating 3 clarifying questions for vague or complex tasks.", []),
            ActionSkill("DynamicQuestioner", "Generating high-leverage architectural questions vs static templates.", []),
            ActionSkill("StatusReporter", "Using visual scan icons (✅🔄⏳❌) for mission transparency.", [])
        ],
        ThinkingStrategy.POST_MISSION_LEARNING: [
            ActionSkill("InstinctExtractor", "Extracting atomic learned behaviors from session tool data.", []),
            ActionSkill("PatternEvolver", "Promoting project-scoped instincts to global thinking patterns.", [])
        ],
        ThinkingStrategy.COUNCIL_OF_CRITICS: [
            ActionSkill("ArchitectLens", "Advising on structural integrity and long-term maintenance.", []),
            ActionSkill("SkepticLens", "Challenging premises and identifying hidden assumptions.", []),
            ActionSkill("PragmatistLens", "Optimizing for shipping speed and operational reality.", []),
            ActionSkill("CriticLens", "Surfacing downside risks and catastrophic failure modes.", [])
        ]
    }

    def __init__(self):
        self.active_skills: Set[str] = set()

    def get_skills_for_strategy(self, strategy: ThinkingStrategy) -> List[Dict[str, Any]]:
        """
        Returns a list of tactical skills and suggested tools for the given strategy.
        """
        skills = self.STRATEGY_SKILL_MAP.get(strategy, [])
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "suggested_tools": skill.tool_mapping
            }
            for skill in skills
        ]

    def inject_skills_context(self, strategy: ThinkingStrategy, payload: Dict[str, Any]) -> None:
        """
        Injects tactical skill documentation into the execution payload.
        """
        skills = self.get_skills_for_strategy(strategy)
        if skills:
            logger.info(f"Injecting {len(skills)} Action Skills for strategy {strategy.value}")
            payload["action_skills"] = skills
            # This context can be picked up by the model to know which tools to prioritize
            payload["skill_context_info"] = (
                "TACTICAL ADVISORY: For the current strategy, prioritize the following skills "
                "and their associated tools to ensure architectural alignment."
            )
