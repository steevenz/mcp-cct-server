from nicegui import ui
from ..services.dm import DataManager
from ..components.metrics import Metrics

class AnalyticsView:
    """
    Paperclip-Grade Cognitive Analytics.
    Clean, minimal, and informative.
    """
    
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        
    def render(self):
        """Build the Paperclip analytics layout."""
        patterns, antis = self.dm.fetch_patterns()
        
        with ui.column().classes('w-full px-5 py-8 sm:px-10 gap-10'):
            # ────────────── GOLDEN PATTERNS ──────────────
            with ui.column().classes('w-full'):
                ui.label('ARCHIVE // GOLDEN_PATTERNS').classes('text-[11px] font-black text-slate-600 pc-kicker mb-6')
                
                if not patterns:
                    ui.label("NO_KERNEL_PATTERNS_DETECTED").classes('text-sm text-slate-300 italic p-4')
                else:
                    with ui.row().classes('w-full gap-6 flex-wrap'):
                        for p in patterns:
                            with ui.card().classes('w-full sm:w-[340px] p-6 pc-clip pc-tilt'):
                                with ui.row().classes('items-center gap-2 mb-2'):
                                    ui.icon('workspace_premium').classes('text-amber-500 text-lg')
                                    ui.label(p.get('name', 'PATTERN')).classes('font-black text-base pc-title').style('color: #0B1220;')
                                ui.label(p.get('description', '')).classes('text-sm leading-relaxed mb-4').style('color: rgba(11, 18, 32, 0.62);')
                                ui.separator().classes('bg-slate-50')
                                m = p.get('metrics', {})
                                with ui.row().classes('justify-between w-full mt-2'):
                                    ui.label("LOGICAL_COHERENCE").classes('text-[10px] font-bold text-slate-600 pc-kicker')
                                    ui.label(f"{m.get('logical_coherence', 0):.2f}").classes('text-[10px] font-black').style('color: #B45309;')

            # ────────────── IMMUNITY WALL ──────────────
            with ui.column().classes('w-full'):
                ui.label('SECURITY // IMMUNITY_WALL').classes('text-[11px] font-black text-slate-600 pc-kicker mb-6')
                
                if not antis:
                    with ui.card().classes('w-full p-6 flex items-center gap-4 pc-tilt transition-all duration-300').style('background: rgba(16, 185, 129, 0.08) !important; border: 1px solid rgba(16, 185, 129, 0.14) !important;'):
                        ui.icon('verified_user').classes('text-emerald-500 text-3xl')
                        with ui.column().classes('gap-0'):
                            ui.label("IMMUNITY_OPTIMAL").classes('font-black text-lg pc-title').style('color: rgba(11, 18, 32, 0.88);')
                            ui.label("System kernel has verified 0 cognitive threats.").classes('text-sm').style('color: rgba(11, 18, 32, 0.58);')
                else:
                    with ui.column().classes('w-full gap-4'):
                        for ap in antis:
                            with ui.expansion(f"THREAT_MITIGATION: {ap.get('category','N/A').upper()}", icon='security').classes('w-full rounded-2xl text-slate-900 overflow-hidden pc-tilt'):
                                with ui.column().classes('p-6 gap-3'):
                                    with ui.row().classes('items-start gap-3'):
                                        ui.element('div').classes('w-1 h-10 bg-rose-500 rounded-full mt-1')
                                        with ui.column().classes('gap-1'):
                                            ui.label('FAILURE_REASON').classes('text-[10px] font-black text-rose-500 pc-kicker')
                                            ui.label(ap.get('failure_reason', '')).classes('text-base').style('color: rgba(11, 18, 32, 0.72);')
                                    
                                    with ui.row().classes('items-start gap-3 mt-4'):
                                        ui.element('div').classes('w-1 h-10 bg-emerald-500 rounded-full mt-1')
                                        with ui.column().classes('gap-1'):
                                            ui.label('CORRECTIVE_PROTOCOL').classes('text-[10px] font-black text-emerald-600 pc-kicker')
                                            ui.label(ap.get('corrective_action', '')).classes('text-base italic').style('color: rgba(11, 18, 32, 0.72);')
                                    
                                    with ui.row().classes('mt-6 pt-6 border-t border-slate-50 w-full justify-between items-center'):
                                        ui.label(f"STRATEGY: {ap.get('failed_strategy', 'unknown').upper()}").classes('text-[9px] font-black text-slate-300')
                                        ui.badge('Mitigated').props('color=emerald-100 text-color=emerald-800 outline')
