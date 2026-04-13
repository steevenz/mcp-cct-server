from nicegui import ui
from ..services.dm import DataManager
from ..components.metrics import Metrics
from ..components.visualizer import Visualizer
from ..components.ledger import Ledger

class TelemetryView:
    """
    Paperclip-Grade Telemetry Orchestrator.
    Clean, informative, and airy.
    """
    
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.active_session_id = None
        # Containers
        self.ledger_container = None
        self.tree_container = None
        
    def render(self):
        """Build the Paperclip telemetry view."""
        with ui.column().classes('w-full h-full px-5 py-6 sm:px-8 sm:py-8 gap-8 overflow-y-auto'):
            
            # ─── TOP BAR: MINIMAL METRICS ───
            with ui.row().classes('w-full gap-4 sm:gap-6 items-center flex-col sm:flex-row'):
                econ = self.dm.fetch_global_economy()
                Metrics.stat_card("INPUT_TOKENS", f"{econ['input_tokens']:,}", "login", color="blue-600")
                Metrics.stat_card("OUTPUT_TOKENS", f"{econ['output_tokens']:,}", "logout", color="emerald-600")
                Metrics.stat_card("SYSTEM_LATENCY", "1.8s", "bolt", color="amber-600")

            # ─── MONITORING CORE ───
            with ui.row().classes('w-full gap-8 flex-col lg:flex-row'):
                
                # LEFT: VISUAL ARCHITECTURE
                with ui.column().classes('w-full lg:w-2/3 gap-4'):
                    ui.label("COGNITIVE_ARCHITECTURE").classes('text-[11px] font-black text-slate-600 pc-kicker')
                    with ui.card().classes('w-full h-[520px] sm:h-[600px] p-4 sm:p-6 items-center flex justify-center pc-clip pc-tilt'):
                        self.tree_container = ui.column().classes('w-full items-center')
                        self._refresh_tree()

                # RIGHT: FORENSIC LEDGER
                with ui.column().classes('flex-1 gap-4'):
                    ui.label("THOUGHT_TIMELINE").classes('text-[11px] font-black text-slate-600 pc-kicker')
                    self.ledger_container = ui.column().classes('w-full gap-4')
                    self._refresh_ledger()

    def _update_session(self, session_id):
        self.active_session_id = session_id
        self._refresh_all()

    def _refresh_all(self):
        self._refresh_ledger()
        self._refresh_tree()

    def _refresh_ledger(self):
        if not self.ledger_container:
            return
        self.ledger_container.clear()
        if not self.active_session_id:
            with self.ledger_container:
                ui.label("Select a session to view activities").classes('text-slate-300 italic p-4 text-center w-full')
            return
            
        thoughts = self.dm.fetch_thoughts(self.active_session_id)
        with self.ledger_container:
            for t_id in list(thoughts.keys())[::-1]:
                Ledger.render_thought(thoughts[t_id])

    def _refresh_tree(self):
        if not self.tree_container:
            return
        self.tree_container.clear()
        if not self.active_session_id:
            return
            
        thoughts = self.dm.fetch_thoughts(self.active_session_id)
        mermaid_code = Visualizer.generate_mermaid(thoughts)
        
        with self.tree_container:
            ui.mermaid(mermaid_code).classes('w-full h-full')
