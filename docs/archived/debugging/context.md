---
title: "Domain: Debugging (Self-Reflection)"
tags: ["debugging", "introspection", "self-reflection", "failure-recovery"]
keywords: ["failure-capture", "root-cause-diagnosis", "contained-recovery", "introspection"]
importance: 90
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Domain: Debugging

## Purpose
The Debugging domain defines the systematic protocols for AI self-reflection and failure recovery. It ensures that when the agent fails, captures the state first, diagnoses strictly, and recovers safely before burning additional tokens on blind retries.

## Scope
Included in this domain:
- **Failure Capture**: Methodologies for recording error state and tool sequences.
- **Root-Cause Diagnosis**: Pattern matching for loops, drift, and state mismatches.
- **Contained Recovery**: Heuristics for safe, minimal interventions to resume progress.
- **Introspection Reporting**: Frameworks for human-auditable debug reports.

Excluded from this domain:
- **General Reasonings**: Handled by the `ThinkingPatterns` domain.
- **Engineering Standards**: Handled by the `Engineering` domain.

## Usage
AI Agents should activate the `SELF_DEBUGGING` strategy when encountering tool loops, context drift, or repeated implementation failures. This domain provides the "laws of physics" for that recovery track.
