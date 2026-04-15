"""
Windows Widget Integration for CCT Cognitive OS

Integrates with Windows 11 Widgets and Windows AI Components.
Provides a lightweight UI surface for quick cognitive tasks.

Author: Steeven Andrian — Senior Systems Architect

Features:
- Quick thought capture widget
- Session status display
- Recent patterns showcase
- Mini orchestration for simple queries

Requires: Windows 11 (Build 22000+)
Optional: Windows AI Components SDK
"""
from __future__ import annotations

import json
import logging
import asyncio
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Widget state management
_widget_instance: Optional['CCTWidget'] = None


@dataclass
class WidgetState:
    """State for the CCT Widget."""
    active_sessions: int
    recent_patterns: list[str]
    last_thought_preview: str
    status: str  # "idle", "thinking", "error"
    quick_actions: list[Dict[str, str]]


@dataclass
class WidgetConfig:
    """Configuration for the CCT Widget."""
    max_recent_patterns: int = 3
    enable_quick_capture: bool = True
    theme: str = "auto"  # "light", "dark", "auto"
    refresh_interval_ms: int = 5000
    enable_windows_ai: bool = False  # Windows AI Components integration


class CCTWidget:
    """
    CCT Windows Widget for Windows 11.
    
    Provides lightweight cognitive task interface without full dashboard.
    Integrates with Windows AI Components when available.
    """
    
    def __init__(
        self,
        orchestrator: Any,  # CognitiveOrchestrator
        config: Optional[WidgetConfig] = None
    ):
        self.orchestrator = orchestrator
        self.config = config or WidgetConfig()
        self.state = WidgetState(
            active_sessions=0,
            recent_patterns=[],
            last_thought_preview="",
            status="idle",
            quick_actions=[
                {"id": "quick_think", "label": "Quick Think", "icon": "💭"},
                {"id": "summarize", "label": "Summarize", "icon": "📋"},
                {"id": "pattern_search", "label": "Find Pattern", "icon": "🔍"},
            ]
        )
        self._callbacks: Dict[str, list[Callable]] = {}
        self._running = False
        self._update_thread: Optional[threading.Thread] = None
        
        # Windows AI Components integration (optional)
        self._windows_ai = None
        if self.config.enable_windows_ai:
            self._init_windows_ai()
    
    def _init_windows_ai(self) -> None:
        """Initialize Windows AI Components integration."""
        try:
            # Attempt to import Windows AI SDK
            # This is optional - widget works without it
            import winrt.windows.ai.machinelearning as winml
            self._windows_ai = winml
            logger.info("[WIDGET] Windows AI Components initialized")
        except ImportError:
            logger.info("[WIDGET] Windows AI Components not available")
            self._windows_ai = None
    
    def start(self) -> None:
        """Start the widget background updates."""
        if self._running:
            return
        
        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
        logger.info("[WIDGET] CCT Widget started")
    
    def stop(self) -> None:
        """Stop the widget."""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=1.0)
        logger.info("[WIDGET] CCT Widget stopped")
    
    def _update_loop(self) -> None:
        """Background update loop for widget state."""
        while self._running:
            try:
                self._refresh_state()
                self._notify_update()
            except Exception as e:
                logger.error(f"[WIDGET] Update error: {e}")
            
            # Sleep in small increments to allow clean shutdown
            slept = 0
            while slept < self.config.refresh_interval_ms and self._running:
                import time
                time.sleep(0.1)
                slept += 100
    
    def _refresh_state(self) -> None:
        """Refresh widget state from orchestrator."""
        try:
            # Count active sessions
            sessions = self.orchestrator.memory.list_sessions()
            active = len([s for s in sessions if not s.startswith("archived")])
            self.state.active_sessions = active
            
            # Get recent patterns
            patterns = self.orchestrator.pattern_archiver.get_top_patterns(n=self.config.max_recent_patterns)
            self.state.recent_patterns = [
                f"{p.content_summary[:40]}..." if len(p.content_summary) > 40 else p.content_summary
                for p in patterns
            ]
            
            # Get last thought preview
            if sessions:
                latest_session = sessions[-1]
                history = self.orchestrator.memory.get_session_history(latest_session)
                if history:
                    last = history[-1]
                    self.state.last_thought_preview = last.content[:80] + "..." if len(last.content) > 80 else last.content
            
            self.state.status = "idle"
            
        except Exception as e:
            logger.error(f"[WIDGET] State refresh error: {e}")
            self.state.status = "error"
    
    def _notify_update(self) -> None:
        """Notify all registered callbacks of state update."""
        for callback in self._callbacks.get("update", []):
            try:
                callback(self.state)
            except Exception as e:
                logger.error(f"[WIDGET] Callback error: {e}")
    
    def on_update(self, callback: Callable[[WidgetState], None]) -> None:
        """Register a callback for widget updates."""
        if "update" not in self._callbacks:
            self._callbacks["update"] = []
        self._callbacks["update"].append(callback)
    
    # Widget Actions
    
    async def quick_think(self, query: str) -> Dict[str, Any]:
        """
        Quick thinking action from widget.
        Creates a minimal session for rapid queries.
        """
        self.state.status = "thinking"
        
        try:
            # Create a quick session
            from src.core.models.enums import CCTProfile, ThinkingStrategy
            
            session_id = self.orchestrator.create_session(
                problem_statement=f"[WIDGET] {query}",
                model_id="widget",
                profile=CCTProfile.BALANCED,
                estimated_thoughts=2
            )
            
            # Execute quick linear thinking
            result = await self.orchestrator.execute_strategy(
                session_id,
                ThinkingStrategy.LINEAR,
                {"thought_content": query, "thought_number": 1, "estimated_total_thoughts": 2}
            )
            
            self.state.status = "idle"
            return {
                "success": True,
                "session_id": session_id,
                "result": result,
                "preview": result.get("thought_result", {}).get("content", "")[:100]
            }
            
        except Exception as e:
            self.state.status = "error"
            logger.error(f"[WIDGET] Quick think error: {e}")
            return {"success": False, "error": str(e)}
    
    async def quick_summarize(self, text: str) -> Dict[str, Any]:
        """Quick summarize action from widget."""
        self.state.status = "thinking"
        
        try:
            from src.core.services.analysis.summarization import generate_summary
            
            summary = generate_summary(text, max_length=100)
            
            self.state.status = "idle"
            return {
                "success": True,
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary)
            }
            
        except Exception as e:
            self.state.status = "error"
            logger.error(f"[WIDGET] Summarize error: {e}")
            return {"success": False, "error": str(e)}
    
    def find_similar_patterns(self, query: str) -> Dict[str, Any]:
        """Find patterns similar to query."""
        try:
            patterns = self.orchestrator.pattern_archiver.find_similar_patterns(query, threshold=0.5)
            
            return {
                "success": True,
                "patterns_found": len(patterns),
                "patterns": [
                    {
                        "id": p.id,
                        "summary": p.content_summary[:60],
                        "usage_count": p.usage_count
                    }
                    for p in patterns[:3]
                ]
            }
            
        except Exception as e:
            logger.error(f"[WIDGET] Pattern search error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_widget_data(self) -> Dict[str, Any]:
        """Get current widget data for UI rendering."""
        return {
            "state": {
                "active_sessions": self.state.active_sessions,
                "recent_patterns": self.state.recent_patterns,
                "last_thought_preview": self.state.last_thought_preview,
                "status": self.state.status,
            },
            "config": {
                "theme": self.config.theme,
                "refresh_interval_ms": self.config.refresh_interval_ms,
            },
            "quick_actions": self.state.quick_actions,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_for_windows_widget(self) -> str:
        """
        Export widget data in format compatible with Windows 11 Widgets.
        Returns JSON string for Adaptive Cards or Widget platform.
        """
        data = self.get_widget_data()
        
        # Format as Windows Adaptive Card
        adaptive_card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Large",
                    "weight": "Bolder",
                    "text": "CCT Cognitive OS"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "Status:", "value": data["state"]["status"]},
                        {"title": "Active Sessions:", "value": str(data["state"]["active_sessions"])},
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "Recent Patterns:",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": "\n".join(f"• {p}" for p in data["state"]["recent_patterns"]) or "No recent patterns",
                    "wrap": True
                }
            ],
            "actions": [
                {
                    "type": "Action.Execute",
                    "title": action["label"],
                    "verb": action["id"]
                }
                for action in data["quick_actions"]
            ]
        }
        
        return json.dumps(adaptive_card, indent=2)


def get_widget(orchestrator: Any = None, config: Optional[WidgetConfig] = None) -> CCTWidget:
    """
    Get or create the global widget instance.
    Singleton pattern for widget management.
    """
    global _widget_instance
    
    if _widget_instance is None and orchestrator is not None:
        _widget_instance = CCTWidget(orchestrator, config)
    
    return _widget_instance


def destroy_widget() -> None:
    """Destroy the global widget instance."""
    global _widget_instance
    
    if _widget_instance:
        _widget_instance.stop()
        _widget_instance = None
