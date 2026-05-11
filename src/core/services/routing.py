from __future__ import annotations

from src.core.services.orchestration.routing import RoutingService


class IntelligenceRouter(RoutingService):
    def __init__(self, scoring: object | None = None, scoring_engine: object | None = None):
        super().__init__(scoring_engine=scoring_engine or scoring)

__all__ = ["IntelligenceRouter"]
