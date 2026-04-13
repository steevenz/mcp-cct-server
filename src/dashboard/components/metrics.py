from nicegui import ui
from typing import Optional

class Metrics:
    """
    Paperclip-Grade UI Components.
    Focuses on minimalism, clarity, and organic spacing.
    """
    
    @staticmethod
    def cost_card(title: str, usd_value: float, idr_value: float, icon: str = "payments"):
        """Paperclip-style cost display. Clean, white, and airy."""
        with ui.card().classes('w-full p-5 pc-clip pc-tilt'):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.row().classes('items-center gap-4'):
                    with ui.element('div').classes('p-2.5 rounded-xl').style('background: rgba(31, 75, 153, 0.08); border: 1px solid rgba(31, 75, 153, 0.14);'):
                        ui.icon(icon).classes('text-2xl').style('color: #1F4B99;')
                    with ui.column().classes('gap-0'):
                        ui.label(title).classes('text-[11px] font-bold text-slate-600 pc-kicker')
                        with ui.row().classes('items-baseline gap-2'):
                            ui.label(f"${usd_value:.4f}").classes('text-2xl font-black').style('color: #0B1220;')
                            ui.label("USD").classes('text-xs font-bold text-slate-500')
                
                with ui.column().classes('items-end gap-0'):
                    ui.label(f"Rp {idr_value:,.0f}").classes('text-lg font-bold').style('color: rgba(11, 18, 32, 0.86);')
                    ui.label("IDR_CONVERSION").classes('text-[9px] text-slate-400 font-bold tracking-tighter')

    @staticmethod
    def stat_card(label: str, value: str, icon: str, color: str = "blue-600"):
        """Minimalist Paperclip stat block."""
        with ui.card().classes('flex-1 p-4 pc-clip pc-tilt'):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.row().classes('items-center gap-4'):
                    with ui.element('div').classes('w-10 h-10 rounded-2xl flex items-center justify-center').style('background: rgba(255, 255, 255, 0.42); border: 1px solid rgba(15, 23, 42, 0.10);'):
                        ui.icon(icon).classes(f'text-xl text-{color}')
                    with ui.column().classes('gap-0'):
                        ui.label(label).classes('text-[10px] font-bold text-slate-600 pc-kicker')
                        ui.label(value).classes('text-xl font-black').style('color: #0B1220;')
                ui.element('div').classes('w-2 h-2 rounded-full').style('background: rgba(31, 75, 153, 0.34);')

    @staticmethod
    def health_indicator(status: str, version: str):
        """Clean system health status with soft indicator."""
        color = "emerald" if status == "healthy" else "amber" if status == "degraded" else "rose"
        icon = "check_circle" if status == "healthy" else "warning" if status == "degraded" else "error"
        
        with ui.card().classes(f'w-full p-4 pc-clip pc-tilt').style(f'border-color: rgba(15, 23, 42, 0.10) !important;'):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon(icon).classes(f'text-xl text-{color}-500')
                    with ui.column().classes('gap-0'):
                        ui.label("SYSTEM_STATUS").classes('text-[10px] font-bold text-slate-400 uppercase')
                        ui.label(status.upper()).classes(f'font-black text-sm text-{color}-600 tracking-widest')
                ui.label(f"v{version}").classes('text-[9px] font-bold text-slate-300')
