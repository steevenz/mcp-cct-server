"""
Council of Critics Hybrid Engine.

Advanced Multi-Agent Recursive Debate that orchestrates a panel of specialized
critics to evaluate a proposal, followed by a consolidated synthesis phase.
"""

from .orchestrator import CouncilOfCriticsEngine
from .schemas import CouncilOfCriticsInput

__all__ = ["CouncilOfCriticsEngine", "CouncilOfCriticsInput"]
