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
