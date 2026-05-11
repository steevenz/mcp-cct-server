"""
Domain classifier for adaptive strategy routing.
Maps problem statements to problem domains for per-domain strategy learning.
"""
from typing import Set, Dict

_DOMAIN_KEYWORDS: Dict[str, Set[str]] = {
    "architecture": {"architecture", "design", "system", "structure", "pattern", "modular",
                     "monolith", "microservice", "component", "module", "dependency"},
    "security": {"security", "auth", "encryption", "vulnerability", "attack", "threat",
                 "compliance", "audit", "oauth", "jwt", "permission"},
    "performance": {"performance", "latency", "throughput", "optimize", "cache", "bottleneck",
                    "scalability", "load", "concurrent", "parallel"},
    "data": {"data", "database", "sql", "nosql", "schema", "migration", "etl", "pipeline",
             "query", "index", "model"},
    "api": {"api", "rest", "graphql", "endpoint", "rpc", "websocket", "grpc", "route"},
    "testing": {"test", "ci", "cd", "deployment", "quality", "coverage", "regression",
                "integration", "unit test"},
    "devops": {"deploy", "kubernetes", "docker", "container", "ci/cd", "pipeline",
               "terraform", "ansible"},
    "general": set(),
}


def classify_problem_domain(problem: str) -> str:
    """Classify a problem statement into a domain."""
    if not problem:
        return "general"
    text = problem.lower()
    scores: Dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if not keywords:
            continue
        scores[domain] = sum(1 for kw in keywords if kw in text)
    if not scores:
        return "general"
    best_score = max(scores.values())
    if best_score == 0:
        return "general"
    return max(scores, key=scores.get)
