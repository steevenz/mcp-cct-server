"""
MCP Prompts: Structured prompt templates for LLM thinking guidance.

Exposes reusable prompt templates that guide LLM behavior:
  - critical_review: Sharp adversarial critique of a proposal
  - architectural_decomposition: Break down complex architecture
  - security_audit: Security-focused code review
  - debug_root_cause: Root cause analysis for bugs
  - decision_framework: Structured decision making

Each prompt includes system message + user message template.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def list_prompts() -> List[Dict[str, Any]]:
    """List all available prompt templates."""
    return [
        {
            "name": "critical_review",
            "title": "Critical Review",
            "description": "Sharp adversarial critique of a technical proposal. Use when you need to stress-test an architecture, design, or implementation plan.",
            "arguments": [
                {"name": "proposal", "description": "The technical proposal, architecture, or code to review", "required": True},
                {"name": "persona", "description": "Reviewer persona: 'Security Expert', 'Performance Engineer', 'Principal Architect', 'UX Designer'", "required": False},
            ],
        },
        {
            "name": "architectural_decomposition",
            "title": "Architectural Decomposition",
            "description": "Break down a complex system into modules, bounded contexts, and interfaces following DDD principles.",
            "arguments": [
                {"name": "problem", "description": "The system or problem to decompose", "required": True},
                {"name": "constraints", "description": "Key constraints: tech stack, scale, team size", "required": False},
            ],
        },
        {
            "name": "security_audit",
            "title": "Security Audit",
            "description": "Security-focused review of code or architecture. Checks for OWASP Top 10, auth flaws, data exposure, and injection risks.",
            "arguments": [
                {"name": "target", "description": "The code, architecture, or design to audit", "required": True},
                {"name": "focus_area", "description": "Focus: 'authentication', 'data_protection', 'input_validation', 'all'", "required": False},
            ],
        },
        {
            "name": "debug_root_cause",
            "title": "Root Cause Analysis",
            "description": "Systematic root cause analysis for bugs and incidents. Follows the '5 Whys' methodology with evidence tracking.",
            "arguments": [
                {"name": "symptoms", "description": "Observed symptoms, error messages, or failure patterns", "required": True},
                {"name": "environment", "description": "Environment details: OS, versions, deployment context", "required": False},
            ],
        },
        {
            "name": "decision_framework",
            "title": "Decision Framework",
            "description": "Structured decision-making comparing alternatives. Use when choosing between technologies, architectures, or approaches.",
            "arguments": [
                {"name": "decision", "description": "The decision to be made", "required": True},
                {"name": "options", "description": "Comma-separated list of options being considered", "required": True},
                {"name": "criteria", "description": "Evaluation criteria: 'cost', 'performance', 'maintainability', 'security', 'scalability'", "required": False},
            ],
        },
    ]


def get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Get a specific prompt with arguments applied."""
    args = arguments or {}

    prompts = {
        "critical_review": _critical_review_prompt,
        "architectural_decomposition": _architectural_decomposition_prompt,
        "security_audit": _security_audit_prompt,
        "debug_root_cause": _debug_root_cause_prompt,
        "decision_framework": _decision_framework_prompt,
    }

    builder = prompts.get(name)
    if not builder:
        return None

    return builder(args)


def _critical_review_prompt(args: Dict[str, str]) -> Dict[str, Any]:
    proposal = args.get("proposal", "")
    persona = args.get("persona", "Principal Architect")

    system = f"""You are a {persona} conducting a critical review.
Your job is to find flaws, vulnerabilities, and improvements.
Be specific and actionable. Rate each finding by severity (CRITICAL, HIGH, MEDIUM, LOW).
Always suggest concrete fixes."""

    user = f"""Please critically review the following proposal:

{proposal}

For each issue found, provide:
1. Severity (CRITICAL/HIGH/MEDIUM/LOW)
2. The specific problem
3. Why it matters
4. A concrete fix or alternative"""

    return {
        "description": f"Critical review by {persona}",
        "messages": [
            {"role": "user", "content": {"type": "text", "text": system + "\n\n" + user}},
        ],
    }


def _architectural_decomposition_prompt(args: Dict[str, str]) -> Dict[str, Any]:
    problem = args.get("problem", "")
    constraints = args.get("constraints", "")

    system = """You are a Principal Systems Architect applying Domain-Driven Design.
Decompose the system into bounded contexts with clear interfaces.
Follow the Lego Principle: loose coupling, high cohesion."""

    user = f"""Decompose the following system:

PROBLEM: {problem}

CONSTRAINTS: {constraints}

Provide:
1. Bounded contexts (with responsibilities)
2. Context boundaries and interfaces
3. Aggregate roots and entities per context
4. Integration patterns between contexts"""

    return {
        "description": "Architectural decomposition following DDD",
        "messages": [
            {"role": "user", "content": {"type": "text", "text": system + "\n\n" + user}},
        ],
    }


def _security_audit_prompt(args: Dict[str, str]) -> Dict[str, Any]:
    target = args.get("target", "")
    focus = args.get("focus_area", "all")

    system = """You are a Security Engineer performing a code/architecture audit.
Check for: Injection flaws, broken auth, data exposure, XXE, broken access control,
security misconfiguration, XSS, insecure deserialization, known vulnerable components,
and insufficient logging/monitoring."""

    user = f"""Audit the following for security vulnerabilities:

TARGET: {target}

FOCUS: {focus}

For each finding:
1. OWASP category
2. Severity
3. Location
4. Exploit scenario
5. Remediation"""

    return {
        "description": f"Security audit focused on {focus}",
        "messages": [
            {"role": "user", "content": {"type": "text", "text": system + "\n\n" + user}},
        ],
    }


def _debug_root_cause_prompt(args: Dict[str, str]) -> Dict[str, Any]:
    symptoms = args.get("symptoms", "")
    environment = args.get("environment", "")

    system = """You are a Debugging Specialist using systematic root cause analysis.
Apply the '5 Whys' technique. Distinguish between symptoms and root causes.
Provide evidence for each conclusion."""

    user = f"""Analyze the root cause of this issue:

SYMPTOMS: {symptoms}

ENVIRONMENT: {environment}

Provide:
1. Symptom analysis
2. First-principles decomposition
3. 5-Whys trace
4. Root cause statement
5. Fix recommendation
6. Prevention strategy"""

    return {
        "description": "Root cause analysis with 5 Whys methodology",
        "messages": [
            {"role": "user", "content": {"type": "text", "text": system + "\n\n" + user}},
        ],
    }


def _decision_framework_prompt(args: Dict[str, str]) -> Dict[str, Any]:
    decision = args.get("decision", "")
    options = args.get("options", "")
    criteria = args.get("criteria", "cost, performance, maintainability, security, scalability")

    system = """You are a Technology Advisor applying a structured decision framework.
Compare options objectively against defined criteria.
Use a weighted decision matrix. Provide a clear recommendation with rationale."""

    user = f"""Help decide: {decision}

OPTIONS: {options}

CRITERIA: {criteria}

Provide:
1. Weighted decision matrix (each option scored 1-5 per criterion)
2. Pros and cons per option
3. Risk assessment per option
4. Clear recommendation with rationale
5. Implementation considerations"""

    return {
        "description": f"Decision framework for: {decision}",
        "messages": [
            {"role": "user", "content": {"type": "text", "text": system + "\n\n" + user}},
        ],
    }
