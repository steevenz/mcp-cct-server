from nicegui import ui
from typing import Dict, List, Any

class Ledger:
    """
    Paperclip-Grade Thought Ledger.
    High clarity, minimal borders, and airy spacing.
    """
    
    STRATEGY_ICONS = {
        "actor_critic_loop":    "⚔️",
        "council_of_critics":   "🏛️",
        "multi_agent_fusion":   "🔗",
        "unconventional_pivot": "⚡",
        "long_term_horizon":    "🔮",
        "critical":             "🎯",
        "synthesis":            "🏗️",
        "empirical_research":   "📡",
        "first_principles":     "🔬"
    }

    @staticmethod
    def strategy_badge(strategy: str):
        """Renders a clean badge for cognitive strategies."""
        icon = Ledger.STRATEGY_ICONS.get(strategy.lower(), "📝")
        with ui.element('div').classes('px-3 py-1 rounded-lg flex items-center gap-2').style('background: rgba(31, 75, 153, 0.08); border: 1px solid rgba(31, 75, 153, 0.14);'):
            ui.label(f"{icon} {strategy.upper()}").classes('text-[9px] font-black tracking-wider').style('color: #1F4B99;')

    @staticmethod
    def render_thought(thought: Dict[str, Any]):
        """Renders a single cognitive step in the ledger (Paperclip Style)."""
        t_id = thought.get("id", "??")
        strategy = thought.get("strategy", "unknown")
        t_type = thought.get("thought_type", "analysis")
        content = thought.get("thought_content", "")
        metrics = thought.get("metrics", {})
        
        with ui.card().classes('w-full p-5 sm:p-6 pc-clip pc-tilt'):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.row().classes('items-center gap-4'):
                    ui.label(t_type.upper()).classes('text-[10px] font-black text-slate-600 pc-kicker')
                    Ledger.strategy_badge(strategy)
                ui.label(f"KERNEL_LOG::{t_id[-8:]}").classes('text-[9px] font-bold text-slate-500')
            
            ui.separator().classes('my-4 bg-slate-50')
            
            # Clean Markdown rendering
            ui.markdown(content).classes('text-[14px] sm:text-[15px] leading-relaxed max-w-none').style('color: rgba(11, 18, 32, 0.78);')
            
            with ui.row().classes('mt-4 items-center gap-6 w-full flex-wrap'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('token').classes('text-sm text-slate-300')
                    ui.label(f"{metrics.get('total_tokens', 0)} Tokens").classes('text-[10px] font-bold text-slate-400')
                with ui.row().classes('items-center gap-2'):
                    ui.icon('verified').classes('text-sm text-blue-300')
                    ui.label(f"Confidence: {metrics.get('confidence_level', 3)}/5").classes('text-[10px] font-bold text-slate-400')
                
                # Dynamic Confidence Bar
                conf = metrics.get('confidence_level', 3)
                with ui.element('div').classes('flex-grow h-1 bg-slate-100 rounded-full overflow-hidden'):
                    ui.element('div').classes('h-full').style(f'width: {conf * 20}%; background: linear-gradient(90deg, rgba(31, 75, 153, 0.92), rgba(180, 83, 9, 0.85));')
