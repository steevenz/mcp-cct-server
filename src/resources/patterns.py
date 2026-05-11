"""
MCP Resources: Expose cognitive data (patterns, sessions, anti-patterns) as standard MCP Resources.

URI Scheme:
  cct://patterns/golden/{id}      — Golden Thinking Pattern
  cct://patterns/anti/{id}        — Anti-Pattern (cognitive failure)
  cct://sessions/{id}             — Session with full thought history
  cct://patterns/list             — All patterns summary

Enables LLMs to browse, read, and subscribe to cognitive memory directly.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.engines.memory.manager import MemoryManager
from src.core.models.domain import GoldenThinkingPattern, AntiPattern

logger = logging.getLogger(__name__)


RESOURCE_SCHEMES = {
    "pattern": "cct://patterns/golden/",
    "anti_pattern": "cct://patterns/anti/",
    "session": "cct://sessions/",
    "patterns_list": "cct://patterns/list",
}


def list_resources(memory: MemoryManager) -> List[Dict[str, Any]]:
    """List all available MCP resources from the cognitive memory."""
    resources = []

    # Add pattern list as a resource
    resources.append({
        "uri": RESOURCE_SCHEMES["patterns_list"],
        "name": "Golden Thinking Patterns Index",
        "title": "All Golden Thinking Patterns",
        "description": "Complete index of archived golden thinking patterns with usage counts and relevance scores",
        "mimeType": "application/json",
    })

    # Add individual golden patterns
    try:
        patterns = memory.get_all_thinking_patterns()
        for p in patterns[:50]:
            pid = p.get("id") or p.get("tp_id", "")
            if not pid:
                continue
            summary = p.get("summary", "") or p.get("content_summary", "") or ""
            resources.append({
                "uri": f"{RESOURCE_SCHEMES['pattern']}{pid}",
                "name": f"Pattern: {pid[:12]}...",
                "title": f"Thinking Pattern: {summary[:80]}",
                "description": f"Golden thinking pattern (usage: {p.get('usage_count', 0)}x, coherence: {p.get('metrics', {}).get('logical_coherence', 'N/A')})",
                "mimeType": "application/json",
            })
    except Exception as e:
        logger.warning(f"Failed to list pattern resources: {e}")

    # Add anti-patterns
    try:
        anti_patterns = memory.get_all_anti_patterns()
        for ap in anti_patterns[:20]:
            ap_id = ap.get("id") or ap.get("failure_id", "")
            if not ap_id:
                continue
            resources.append({
                "uri": f"{RESOURCE_SCHEMES['anti_pattern']}{ap_id}",
                "name": f"Anti-Pattern: {ap_id[:12]}...",
                "title": f"Cognitive Failure: {ap.get('category', 'unknown')}",
                "description": f"Anti-pattern ({ap.get('category', 'unknown')}): {ap.get('failure_reason', '')[:100]}",
                "mimeType": "application/json",
            })
    except Exception as e:
        logger.warning(f"Failed to list anti-pattern resources: {e}")

    return resources


def read_resource(uri: str, memory: MemoryManager) -> Optional[Dict[str, Any]]:
    """Read a specific MCP resource by URI."""
    if uri == RESOURCE_SCHEMES["patterns_list"]:
        return _read_patterns_list(memory)

    if uri.startswith(RESOURCE_SCHEMES["pattern"]):
        pattern_id = uri[len(RESOURCE_SCHEMES["pattern"]):]
        return _read_pattern(pattern_id, memory)

    if uri.startswith(RESOURCE_SCHEMES["anti_pattern"]):
        ap_id = uri[len(RESOURCE_SCHEMES["anti_pattern"]):]
        return _read_anti_pattern(ap_id, memory)

    if uri.startswith(RESOURCE_SCHEMES["session"]):
        session_id = uri[len(RESOURCE_SCHEMES["session"]):]
        return _read_session(session_id, memory)

    return None


def _read_patterns_list(memory: MemoryManager) -> Dict[str, Any]:
    """Read the complete patterns index."""
    try:
        patterns = memory.get_all_thinking_patterns()
        anti_patterns = memory.get_all_anti_patterns()
        return {
            "uri": RESOURCE_SCHEMES["patterns_list"],
            "mimeType": "application/json",
            "text": json.dumps({
                "total_golden_patterns": len(patterns),
                "total_anti_patterns": len(anti_patterns),
                "golden_patterns": [
                    {
                        "id": p.get("id") or p.get("tp_id"),
                        "usage_count": p.get("usage_count", 0),
                        "summary": (p.get("summary") or p.get("content_summary", ""))[:150],
                        "strategy": p.get("strategy", "unknown"),
                        "tags": p.get("tags", []),
                    }
                    for p in patterns[:100] if p.get("id") or p.get("tp_id")
                ],
                "anti_patterns": [
                    {
                        "id": ap.get("id") or ap.get("failure_id"),
                        "category": ap.get("category", "unknown"),
                        "failure_reason": ap.get("failure_reason", "")[:150],
                    }
                    for ap in anti_patterns[:50] if ap.get("id") or ap.get("failure_id")
                ],
            }, indent=2),
        }
    except Exception as e:
        logger.error(f"Failed to read patterns list: {e}")
        return {"uri": uri, "mimeType": "application/json", "text": json.dumps({"error": str(e)})}


def _read_pattern(pattern_id: str, memory: MemoryManager) -> Optional[Dict[str, Any]]:
    """Read a specific golden thinking pattern."""
    try:
        pattern = memory.get_thinking_pattern_by_id(pattern_id)
        if not pattern:
            return None
        return {
            "uri": f"{RESOURCE_SCHEMES['pattern']}{pattern_id}",
            "mimeType": "application/json",
            "text": json.dumps(pattern, indent=2, default=str),
        }
    except Exception as e:
        logger.error(f"Failed to read pattern {pattern_id}: {e}")
        return None


def _read_anti_pattern(ap_id: str, memory: MemoryManager) -> Optional[Dict[str, Any]]:
    """Read a specific anti-pattern."""
    try:
        anti_patterns = memory.get_all_anti_patterns()
        for ap in anti_patterns:
            if ap.get("id") == ap_id or ap.get("failure_id") == ap_id:
                return {
                    "uri": f"{RESOURCE_SCHEMES['anti_pattern']}{ap_id}",
                    "mimeType": "application/json",
                    "text": json.dumps(ap, indent=2, default=str),
                }
        return None
    except Exception as e:
        logger.error(f"Failed to read anti-pattern {ap_id}: {e}")
        return None


def _read_session(session_id: str, memory: MemoryManager) -> Optional[Dict[str, Any]]:
    """Read a session with full thought history."""
    try:
        session = memory.get_session(session_id)
        if not session:
            return None
        history = memory.get_session_history(session_id)
        data = session.model_dump(mode="json")
        data["thoughts"] = [t.model_dump(mode="json") for t in history]
        return {
            "uri": f"{RESOURCE_SCHEMES['session']}{session_id}",
            "mimeType": "application/json",
            "text": json.dumps(data, indent=2, default=str),
        }
    except Exception as e:
        logger.error(f"Failed to read session {session_id}: {e}")
        return None
