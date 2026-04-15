from typing import Dict, Any, List
from src.core.models.enums import ThinkingStrategy

class GuidanceService:
    """
    Provides structured cognitive protocols and templates for 'Guided' execution.
    Used when the server acts as an advisor rather than an autonomous actor.
    """

    PROTOCOLS: Dict[ThinkingStrategy, Dict[str, Any]] = {
        ThinkingStrategy.ACTOR_CRITIC_LOOP: {
            "name": "Actor-Critic Loop",
            "phases": [
                {
                    "name": "Criticism Phase",
                    "persona": "Skeptic / Auditor",
                    "instruction": (
                        "Critically evaluate the previous proposal. Identify architectural flaws, "
                        "security vulnerabilities, or scalability bottlenecks. Do not solve them yet."
                    )
                },
                {
                    "name": "Synthesis Phase",
                    "persona": "Architect / Lead Artisan",
                    "instruction": (
                        "Synthesize the original proposal with the criticisms. "
                        "Resolve the conflicts to formulate a robust, production-ready implementation."
                    )
                }
            ],
            "template": (
                "ACTOR-CRITIC PROTOCOL:\n"
                "1. Critically attack the weaknesses of [TARGET].\n"
                "2. Evolve the solution based on those weaknesses."
            )
        },
        ThinkingStrategy.MULTI_AGENT_FUSION: {
            "name": "Multi-Agent Fusion",
            "instruction": (
                "Simulate a collaborative war room with specialized experts. "
                "Each expert provides a divergent perspective, which is then synthesized into a master conclusion."
            ),
            "suggested_personas": ["Systems Architect", "Security Engineer", "Product Manager", "UX Specialist"],
            "template": (
                "WAR ROOM PROTOCOL:\n"
                "1. Generate 3-4 divergent insights from [PERSONAS].\n"
                "2. Synthesize all insights into a single Unified Conclusion."
            )
        },
        ThinkingStrategy.INTEGRATIVE: {
            "name": "Integrative Synthesis",
            "instruction": "Merge all recent findings into a unified, high-density conclusion.",
            "template": "SYNTHESIS GOAL: Eliminate redundancy and resolve contradictions across [NODES]."
        }
    }

    def get_guidance(self, strategy: ThinkingStrategy) -> Dict[str, Any]:
        """Returns the protocol guidance for a given strategy."""
        return self.PROTOCOLS.get(strategy, {
            "name": strategy.value.replace("_", " ").title(),
            "instruction": f"Proceed with the {strategy.value} cognitive strategy.",
            "template": "Focus on clarity and logical coherence."
        })

    def format_guidance_message(self, strategy: ThinkingStrategy) -> str:
        """Formats a human-readable guidance message for the tool output."""
        guidance = self.get_guidance(strategy)
        msg = f"GUIDED MODE ACTIVATED: {guidance['name']}\n"
        msg += f"PROTOCOL: {guidance['instruction']}\n"
        if "template" in guidance:
            msg += f"TEMPLATE: {guidance['template']}"
        return msg
