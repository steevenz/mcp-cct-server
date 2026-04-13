from nicegui import ui
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.dashboard.services.dm import DataManager
from src.dashboard.views.telemetry import TelemetryView
from src.dashboard.views.analytics import AnalyticsView
from src.dashboard.views.sessions import SessionsView
from src.dashboard.components.metrics import Metrics

# ─────────────────────────────────────────────────────────
# APP INITIALIZATION
# ─────────────────────────────────────────────────────────
PRD_ID = "20260413-tailadmin-ui"
dm = DataManager()
telemetry_view = TelemetryView(dm)
analytics_view = AnalyticsView(dm)
sessions_view = None
_econ_tokens_label = None
_econ_usd_label = None
_econ_idr_label = None

def init_layout():
    """Build the TailAdmin-grade Shell."""

    ui.colors(primary='#3C50E0', secondary='#64748B', accent='#0F172A')
    ui.query('body').style('font-family: "Spline Sans", ui-sans-serif, system-ui; background-color: #F1F5F9; color: #0F172A;')

    ui.add_head_html('''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500..900&family=Spline+Sans:wght@400..700&display=swap');

            :root {
                --ta-bg: #F1F5F9;
                --ta-panel: #FFFFFF;
                --ta-ink: #0F172A;
                --ta-muted: #64748B;
                --ta-line: rgba(226, 232, 240, 1);
                --ta-line-2: rgba(148, 163, 184, 0.25);
                --ta-shadow: 0 18px 45px rgba(2, 6, 23, 0.10);
                --ta-shadow-soft: 0 10px 28px rgba(2, 6, 23, 0.08);
                --ta-primary: #3C50E0;
                --ta-primary-2: #0EA5E9;
                --ta-danger: #E11D48;
                --ta-success: #22C55E;
                --ta-focus: rgba(60, 80, 224, 0.35);
                --ta-sidebar: #0B1220;
                --ta-sidebar-2: #0F172A;
                --ta-sidebar-line: rgba(148, 163, 184, 0.16);
            }

            body {
                background: linear-gradient(180deg, rgba(248, 250, 252, 1), var(--ta-bg));
                color: var(--ta-ink);
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }

            .pc-title {
                font-family: "Outfit", ui-sans-serif, system-ui;
                letter-spacing: -0.02em;
            }

            .pc-kicker {
                letter-spacing: 0.16em;
                text-transform: uppercase;
            }

            .q-header {
                background: rgba(248, 250, 252, 0.82) !important;
                border-bottom: 1px solid var(--ta-line) !important;
                backdrop-filter: blur(12px);
            }

            .q-drawer {
                background: linear-gradient(180deg, var(--ta-sidebar), var(--ta-sidebar-2)) !important;
                border-right: 1px solid var(--ta-sidebar-line) !important;
            }

            .q-tab--active { color: var(--ta-primary) !important; }
            .q-tab__indicator { height: 3px !important; border-radius: 999px !important; background: var(--ta-primary) !important; }

            .q-card {
                background: var(--ta-panel) !important;
                border: 1px solid var(--ta-line) !important;
                border-radius: 16px !important;
                box-shadow: var(--ta-shadow-soft) !important;
            }

            .pc-clip {
                position: relative !important;
                overflow: hidden !important;
            }
            .pc-clip::before {
                content: none;
            }
            .pc-clip::after {
                content: none;
            }

            .pc-tilt:hover {
                transform: translateY(-2px);
                box-shadow: var(--ta-shadow) !important;
            }

            .pc-tilt {
                transition: transform 220ms cubic-bezier(.2,.8,.2,1), box-shadow 220ms cubic-bezier(.2,.8,.2,1);
                will-change: transform;
            }

            .q-btn:focus-visible,
            .q-field__control:focus-within {
                outline: 2px solid var(--ta-focus);
                outline-offset: 2px;
                border-radius: 14px;
            }

            @media (max-width: 640px) {
                .pc-pad-x { padding-left: 18px !important; padding-right: 18px !important; }
                .pc-pad-y { padding-top: 14px !important; padding-bottom: 14px !important; }
            }

            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: rgba(15, 23, 42, 0.14); border-radius: 999px; }
            ::-webkit-scrollbar-thumb:hover { background: rgba(15, 23, 42, 0.20); }
            .nicegui-tab-panel { padding: 0 !important; background: transparent !important; }
            .q-drawer--standard { background: linear-gradient(180deg, var(--ta-sidebar), var(--ta-sidebar-2)) !important; }
            .mermaid-card { background: #FFFFFF !important; border-radius: 16px; border: 1px solid var(--ta-line); box-shadow: var(--ta-shadow-soft); }

            .ta-sidebar { width: 288px !important; }
            .ta-sidebar.ta-collapsed { width: 88px !important; }
            .ta-nav-btn { width: 100%; justify-content: flex-start; border-radius: 14px; padding: 10px 12px; }
            .ta-nav-btn:hover { background: rgba(148, 163, 184, 0.10); }
            .ta-nav-btn.ta-active { background: rgba(60, 80, 224, 0.16); border: 1px solid rgba(60, 80, 224, 0.20); }
            .ta-nav-icon { color: rgba(226, 232, 240, 0.90); }
            .ta-nav-label { color: rgba(226, 232, 240, 0.92); font-weight: 800; font-size: 12px; letter-spacing: 0.06em; }
            .ta-sidebar.ta-collapsed .ta-nav-label { display: none; }
            .ta-sidebar.ta-collapsed .ta-brand-text { display: none; }
            .ta-sidebar .q-card { background: rgba(2, 6, 23, 0.22) !important; border: 1px solid rgba(148, 163, 184, 0.14) !important; box-shadow: none !important; }
            .ta-sidebar .q-card * { color: rgba(226, 232, 240, 0.86); }
            .ta-sidebar .text-slate-900,
            .ta-sidebar .text-slate-800,
            .ta-sidebar .text-slate-700 { color: rgba(226, 232, 240, 0.94) !important; }
            .ta-sidebar .text-slate-600,
            .ta-sidebar .text-slate-500,
            .ta-sidebar .text-slate-400 { color: rgba(226, 232, 240, 0.72) !important; }
            .ta-sidebar .text-slate-300 { color: rgba(226, 232, 240, 0.58) !important; }
            .ta-sidebar .text-emerald-500 { color: #34D399 !important; }
            .ta-sidebar .text-emerald-600 { color: #10B981 !important; }
            .ta-sidebar .text-amber-500 { color: #F59E0B !important; }
            .ta-sidebar .text-amber-600 { color: #D97706 !important; }
            .ta-sidebar .text-rose-500 { color: #FB7185 !important; }
            .ta-sidebar .text-rose-600 { color: #E11D48 !important; }
            .ta-sidebar .text-blue-600 { color: #60A5FA !important; }
        </style>
    ''')

    # ─── LEFT DRAWER (SIDEBAR) ───
    sidebar_is_collapsed = {"value": False}
    with ui.left_drawer(value=True, fixed=True).classes('p-5 gap-6 ta-sidebar') as drawer:
        with ui.row().classes('items-center justify-between w-full'):
            with ui.row().classes('items-center gap-3'):
                with ui.element('div').classes('w-10 h-10 rounded-2xl flex items-center justify-center').style('background: rgba(60, 80, 224, 0.18); border: 1px solid rgba(60, 80, 224, 0.26);'):
                    ui.icon('dashboard').classes('text-white text-xl')
                with ui.column().classes('gap-0 ta-brand-text'):
                    ui.label('CCT ADMIN').classes('text-base font-black')
                    ui.label(PRD_ID).classes('text-[9px] font-bold pc-kicker').style('color: rgba(226, 232, 240, 0.72);')

            def _toggle_sidebar():
                sidebar_is_collapsed["value"] = not sidebar_is_collapsed["value"]
                drawer.classes(add='ta-collapsed' if sidebar_is_collapsed["value"] else '', remove='' if sidebar_is_collapsed["value"] else 'ta-collapsed')

            ui.button(on_click=_toggle_sidebar).props('flat round dense icon=chevron_left').classes('text-white/90')

        with ui.column().classes('w-full gap-2 mt-2'):
            def _nav_to(tab):
                main_tabs.value = tab

            ui.button(on_click=lambda: _nav_to(sessions_tab)).props('flat no-caps').classes('ta-nav-btn ta-active').add_slot('default', '''
                <div class="flex items-center gap-3 w-full">
                    <i class="material-icons ta-nav-icon">confirmation_number</i>
                    <div class="ta-nav-label">SESSIONS</div>
                </div>
            ''')
            ui.button(on_click=lambda: _nav_to(telemetry_tab)).props('flat no-caps').classes('ta-nav-btn').add_slot('default', '''
                <div class="flex items-center gap-3 w-full">
                    <i class="material-icons ta-nav-icon">description</i>
                    <div class="ta-nav-label">LEDGER</div>
                </div>
            ''')
            ui.button(on_click=lambda: _nav_to(analytics_tab)).props('flat no-caps').classes('ta-nav-btn').add_slot('default', '''
                <div class="flex items-center gap-3 w-full">
                    <i class="material-icons ta-nav-icon">inventory_2</i>
                    <div class="ta-nav-label">ARCHIVE</div>
                </div>
            ''')
            ui.button(on_click=lambda: _nav_to(economy_tab)).props('flat no-caps').classes('ta-nav-btn').add_slot('default', '''
                <div class="flex items-center gap-3 w-full">
                    <i class="material-icons ta-nav-icon">savings</i>
                    <div class="ta-nav-label">ECONOMY</div>
                </div>
            ''')

        health = dm.get_health()
        Metrics.health_indicator(health['status'], "V3.0.0")

        stats = dm.fetch_db_stats()
        with ui.card().classes('w-full p-5 pc-clip pc-tilt'):
            ui.label('DATABASE').classes('text-[10px] font-black text-slate-500 pc-kicker')
            with ui.row().classes('w-full justify-between items-baseline mt-3'):
                ui.label('SIZE').classes('text-[10px] font-bold text-slate-400 pc-kicker')
                ui.label(f"{stats.get('db_size_kb', 0)} KB").classes('text-[10px] font-black text-slate-900')

            with ui.row().classes('w-full gap-3 mt-4'):
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('SESSIONS').classes('text-[9px] font-bold text-slate-400 pc-kicker')
                    ui.label(f"{int(stats.get('sessions', 0) or 0):,}").classes('text-base font-black')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('THOUGHTS').classes('text-[9px] font-bold text-slate-400 pc-kicker')
                    ui.label(f"{int(stats.get('thoughts', 0) or 0):,}").classes('text-base font-black')

            with ui.row().classes('w-full gap-3 mt-3'):
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('PATTERNS').classes('text-[9px] font-bold text-slate-400 pc-kicker')
                    ui.label(f"{int(stats.get('patterns', 0) or 0):,}").classes('text-base font-black')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('THREATS').classes('text-[9px] font-bold text-slate-400 pc-kicker')
                    ui.label(f"{int(stats.get('anti_patterns', 0) or 0):,}").classes('text-base font-black')

        with ui.row().classes('items-center gap-2 px-3 py-2 rounded-2xl').style('background: rgba(226, 232, 240, 0.10); border: 1px solid rgba(148, 163, 184, 0.14);'):
            ui.icon('favorite').classes('text-emerald-400 text-base')
            ui.label('HEARTBEAT: 3s').classes('text-[10px] font-black pc-kicker').style('color: rgba(226, 232, 240, 0.86);')

        with ui.column().classes('mt-auto pt-5'):
            ui.label('© 2026 ANTIGRAVITY ENGINE').classes('text-[9px] font-bold tracking-widest').style('color: rgba(226, 232, 240, 0.55);')

    # ─── HEADER ───
    with ui.header().classes('px-8 py-4 flex items-center justify-between shadow-none text-slate-900 pc-pad-x pc-pad-y'):
        with ui.row().classes('items-center gap-4'):
            ui.button(on_click=drawer.toggle, color='blue-600').props('flat round dense icon=menu').classes('pc-tilt sm:hidden')
            with ui.element('div').classes('w-10 h-10 rounded-2xl flex items-center justify-center shadow-lg').style('background: linear-gradient(135deg, rgba(60, 80, 224, 0.95), rgba(14, 165, 233, 0.85)); box-shadow: 0 12px 24px rgba(60, 80, 224, 0.20);'):
                ui.icon('auto_graph').classes('text-white text-xl')
            with ui.column().classes('gap-0'):
                ui.label('Dashboard').classes('text-xl font-black pc-title')
                ui.label('TailAdmin-grade Command Center').classes('text-[10px] font-bold text-slate-500 pc-kicker')

            with ui.row().classes('items-center gap-2 ml-4 px-4 py-2 rounded-2xl').style('background: rgba(255, 255, 255, 0.70); border: 1px solid rgba(226, 232, 240, 1);'):
                ui.icon('search').classes('text-slate-500 text-base')
                ui.input(placeholder='Search sessions, IDs, status...').classes('w-[260px] md:w-[360px]').props('borderless dense')

        with ui.row().classes('items-center gap-6'):
            econ = dm.fetch_global_economy()
            global _econ_tokens_label, _econ_usd_label, _econ_idr_label
            with ui.row().classes('items-center gap-3 px-4 py-2 rounded-2xl').style('background: rgba(255, 255, 255, 0.40); border: 1px solid rgba(15, 23, 42, 0.10);'):
                ui.icon('token').classes('text-slate-600 text-base')
                _econ_tokens_label = ui.label(f"{int(econ.get('total_tokens', 0) or 0):,} TOKENS").classes('text-[10px] font-black text-slate-800 pc-kicker')

            with ui.row().classes('items-center gap-3 px-4 py-2 rounded-2xl').style('background: rgba(255, 255, 255, 0.40); border: 1px solid rgba(15, 23, 42, 0.10);'):
                ui.icon('payments').classes('text-slate-600 text-base')
                _econ_usd_label = ui.label(f"${float(econ.get('cost_usd', 0.0) or 0.0):.4f} USD").classes('text-[10px] font-black text-slate-800 pc-kicker')
                _econ_idr_label = ui.label(f"Rp {float(econ.get('cost_idr', 0.0) or 0.0):,.0f}").classes('text-[9px] font-bold text-slate-500')

            with ui.row().classes('items-center gap-2 px-4 py-1.5 rounded-full').style('background: rgba(16, 185, 129, 0.10); border: 1px solid rgba(16, 185, 129, 0.18);'):
                ui.element('div').classes('w-2 h-2 rounded-full bg-emerald-500 animate-pulse')
                ui.label('SYSTEM_ACTIVE').classes('text-[10px] font-black text-emerald-700 pc-kicker')

            ui.button(on_click=lambda: _force_refresh(), color='blue-600').props('flat round icon=sync').classes('pc-tilt')

    # ─── MAIN CONTENT AREA ───
    def _open_session(session_id: str):
        telemetry_view._update_session(session_id)
        main_tabs.value = telemetry_tab
        ui.notify(f"Session Activated: {session_id[-8:].upper()}", type='info', color='blue-600', position='bottom-right')

    global sessions_view
    sessions_view = SessionsView(dm, _open_session)

    def _render_economy():
        econ = dm.fetch_global_economy()
        rollups = dm.fetch_session_rollups()
        rollups.sort(key=lambda r: float(r.get("cost_usd", 0.0) or 0.0), reverse=True)

        with ui.column().classes('w-full px-5 py-8 sm:px-10 gap-8'):
            ui.label('BUDGETS // ECONOMY').classes('text-[11px] font-black text-slate-600 pc-kicker mb-4')
            with ui.row().classes('w-full gap-4 sm:gap-6 flex-col sm:flex-row'):
                Metrics.stat_card("TOTAL_TOKENS", f"{int(econ.get('total_tokens', 0) or 0):,}", "token", color="blue-600")
                Metrics.stat_card("USD", f"${float(econ.get('cost_usd', 0.0) or 0.0):.4f}", "payments", color="emerald-600")
                Metrics.stat_card("IDR", f"Rp {float(econ.get('cost_idr', 0.0) or 0.0):,.0f}", "currency_exchange", color="amber-600")

            if rollups:
                ui.label('TOP_SPENDERS').classes('text-[11px] font-black text-slate-600 pc-kicker mt-2')
                rows = []
                for r in rollups[:12]:
                    sid = r.get("session_id", "")
                    steps = int(r.get("steps", 0) or 0)
                    usd = float(r.get("cost_usd", 0.0) or 0.0)
                    tok = int(r.get("total_tokens", 0) or 0)
                    rows.append(
                        {
                            "id": f"LOG_{sid[-8:].upper()}",
                            "steps": steps,
                            "tokens": f"{tok:,}",
                            "cost": f"${usd:.4f}",
                            "full_id": sid,
                        }
                    )

                columns = [
                    {"name": "id", "label": "SESSION", "field": "id", "align": "left"},
                    {"name": "steps", "label": "STEPS", "field": "steps", "align": "right"},
                    {"name": "tokens", "label": "TOKENS", "field": "tokens", "align": "right"},
                    {"name": "cost", "label": "COST", "field": "cost", "align": "right"},
                    {"name": "actions", "label": "OPEN", "field": "actions", "align": "right"},
                ]
                with ui.card().classes('w-full p-0 overflow-hidden pc-clip'):
                    with ui.element('div').classes('w-full overflow-x-auto'):
                        grid = ui.table(columns=columns, rows=rows, row_key="id").classes('min-w-[640px] w-full bg-transparent')
                    grid.props('flat dense separator=horizontal')
                    grid.add_slot('body-cell-actions', '''
                        <q-td :props="props">
                            <q-btn flat round dense icon="open_in_new" color="blue-7" size="sm" @click="$parent.$emit('open', props.row)" />
                        </q-td>
                    ''')
                    grid.on('open', lambda msg: _open_session(msg.args['full_id']))

    with ui.column().classes('w-full flex-grow p-0'):
        with ui.tabs().classes('hidden') as main_tabs:
            sessions_tab = ui.tab('SESSIONS', icon='confirmation_number')
            telemetry_tab = ui.tab('LEDGER', icon='description')
            analytics_tab = ui.tab('ARCHIVE', icon='inventory_2')
            economy_tab = ui.tab('ECONOMY', icon='savings')

        with ui.tab_panels(main_tabs, value=sessions_tab).classes('w-full flex-grow pt-0'):
            with ui.tab_panel(sessions_tab):
                sessions_view.render()
            with ui.tab_panel(telemetry_tab):
                telemetry_view.render()
            with ui.tab_panel(analytics_tab):
                analytics_view.render()
            with ui.tab_panel(economy_tab):
                _render_economy()

    ui.timer(3.0, lambda: _poll_db())

def _poll_db():
    if dm.has_changed():
        _force_refresh()

def _force_refresh():
    telemetry_view._refresh_all()
    econ = dm.fetch_global_economy()
    if _econ_tokens_label is not None:
        _econ_tokens_label.text = f"{int(econ.get('total_tokens', 0) or 0):,} TOKENS"
    if _econ_usd_label is not None:
        _econ_usd_label.text = f"${float(econ.get('cost_usd', 0.0) or 0.0):.4f} USD"
    if _econ_idr_label is not None:
        _econ_idr_label.text = f"Rp {float(econ.get('cost_idr', 0.0) or 0.0):,.0f}"
    ui.notify('System Synchronized', type='info', color='blue-600', position='bottom-right')

# ─────────────────────────────────────────────────────────
# RUNTIME
# ─────────────────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    init_layout()
    ui.run(
        title='CCT Command Center',
        port=8080,
        dark=False,
        show=False,
        favicon='🎯'
    )
