from nicegui import ui
from ..services.dm import DataManager

class SessionsView:
    """
    Paperclip-Grade Session Archive.
    High clarity management grid for Kernel Logs.
    """
    
    def __init__(self, data_manager: DataManager, on_open_session):
        self.dm = data_manager
        self._on_open_session = on_open_session
        
    def render(self):
        """Build the TailAdmin-grade session table."""
        sessions = self.dm.fetch_session_rollups()
        
        with ui.column().classes('w-full px-5 py-8 sm:px-10 gap-8'):
            with ui.row().classes('w-full items-end justify-between gap-4 flex-col sm:flex-row'):
                with ui.column().classes('gap-1'):
                    ui.label('Sessions').classes('text-2xl font-black pc-title')
                    ui.label('Browse, activate, and purge persisted cognitive sessions.').classes('text-[12px] font-bold text-slate-500')

                with ui.row().classes('items-center gap-3'):
                    search = ui.input(placeholder='Search session ID, status...').classes('w-[260px] sm:w-[320px]').props('outlined dense')
                    status_filter = ui.select(
                        options=['ALL', 'ACTIVE', 'COMPLETED', 'FAILED', 'UNKNOWN'],
                        value='ALL',
                        label='STATUS',
                    ).classes('w-[160px]').props('outlined dense')
            
            columns = [
                {'name': 'session_id', 'label': 'SESSION', 'field': 'session_id', 'required': True, 'align': 'left'},
                {'name': 'created_at', 'label': 'CREATED', 'field': 'created_at', 'sortable': True},
                {'name': 'status', 'label': 'STATUS', 'field': 'status', 'align': 'center'},
                {'name': 'tokens', 'label': 'TOKENS', 'field': 'tokens', 'align': 'right'},
                {'name': 'cost', 'label': 'COST (USD)', 'field': 'cost', 'align': 'right'},
                {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'}
            ]
            
            rows_all = []
            for s in sessions:
                d = s.get('data', {})
                created_raw = d.get('created_at', 'N/A')
                created = created_raw[:19].replace('T', ' ') if isinstance(created_raw, str) else 'N/A'
                steps = int(s.get('steps', 0) or 0)
                cost_usd = float(s.get('cost_usd', 0.0) or 0.0)
                tokens = int(s.get('total_tokens', 0) or 0)
                rows_all.append({
                    'session_id': f"LOG_{s['session_id'][-8:].upper()}",
                    'created_at': created,
                    'status': d.get('status', 'unknown').upper(),
                    'tokens': f"{tokens:,}",
                    'cost': f"${cost_usd:.4f}",
                    'full_id': s['session_id'],
                    'steps': steps,
                })
            
            with ui.card().classes('w-full p-0 overflow-hidden pc-clip'):
                with ui.element('div').classes('w-full overflow-x-auto'):
                    grid = ui.table(columns=columns, rows=rows_all, row_key='session_id').classes('min-w-[820px] w-full bg-transparent')
                grid.props('flat separator=horizontal')
                
                grid.add_slot('body-cell-session_id', '''
                    <q-td :props="props">
                        <div class="flex items-center gap-3">
                            <div class="w-9 h-9 rounded-xl flex items-center justify-center" style="background: rgba(60, 80, 224, 0.10); border: 1px solid rgba(60, 80, 224, 0.16);">
                                <i class="material-icons" style="color: rgba(60, 80, 224, 0.92); font-size: 18px;">confirmation_number</i>
                            </div>
                            <div class="flex flex-col">
                                <div class="text-[12px] font-black text-slate-900 tracking-tight">{{ props.value }}</div>
                                <div class="text-[10px] font-bold text-slate-400">Kernel Log</div>
                            </div>
                        </div>
                    </q-td>
                ''')
                
                grid.add_slot('body-cell-created_at', '''
                    <q-td :props="props">
                        <div class="text-[11px] font-bold text-slate-600">{{ props.value }}</div>
                    </q-td>
                ''')
                
                grid.add_slot('body-cell-status', '''
                    <q-td :props="props">
                        <q-badge
                            :color="props.value === 'COMPLETED' ? 'green-1' : (props.value === 'FAILED' ? 'red-1' : 'blue-1')"
                            :text-color="props.value === 'COMPLETED' ? 'green-8' : (props.value === 'FAILED' ? 'red-8' : 'blue-8')"
                            unelevated
                            dense
                            class="text-[10px] font-black px-2 py-1 rounded-lg"
                        >
                            {{ props.value }}
                        </q-badge>
                    </q-td>
                ''')

                grid.add_slot('body-cell-tokens', '''
                    <q-td :props="props">
                        <div class="text-[11px] font-black text-slate-700">{{ props.value }}</div>
                    </q-td>
                ''')

                grid.add_slot('body-cell-cost', '''
                    <q-td :props="props">
                        <div class="text-[11px] font-black text-slate-900">{{ props.value }}</div>
                    </q-td>
                ''')
                
                grid.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn unelevated dense icon="open_in_new" color="indigo-7" size="sm" class="q-px-sm q-py-xs rounded-lg" @click="$parent.$emit('open', props.row)" />
                        <q-btn flat dense icon="delete_outline" color="red-6" size="sm" class="q-ml-sm" @click="$parent.$emit('delete', props.row)" />
                    </q-td>
                ''')
                
                grid.on('open', lambda msg: self._open_session(msg.args['full_id']))
                grid.on('delete', lambda msg: self._confirm_delete(msg.args['full_id']))

            def _apply_filters():
                q = (search.value or '').strip().lower()
                st = (status_filter.value or 'ALL').upper()
                filtered = []
                for r in rows_all:
                    if st != 'ALL' and r.get('status', 'UNKNOWN') != st:
                        continue
                    hay = f"{r.get('session_id', '')} {r.get('status', '')} {r.get('created_at', '')}".lower()
                    if q and q not in hay:
                        continue
                    filtered.append(r)
                grid.rows = filtered
                grid.update()

            search.on('update:model-value', lambda _: _apply_filters())
            status_filter.on('update:model-value', lambda _: _apply_filters())

    def _open_session(self, session_id: str):
        try:
            self._on_open_session(session_id)
        except Exception:
            ui.notify('Open Failed', type='negative', position='bottom-right')

    def _confirm_delete(self, session_id):
        with ui.dialog() as dialog, ui.card().classes('bg-white border border-slate-200 p-8 rounded-2xl'):
            ui.label("Delete session?").classes('text-lg font-black text-slate-900')
            ui.label(f"LOG_{session_id[-8:].upper()} will be permanently removed.").classes('text-sm font-bold text-slate-600 mt-2')
            ui.label("This action is irreversible and will purge associated thought history.").classes('text-xs text-slate-500 leading-relaxed mt-2')
            
            with ui.row().classes('w-full justify-end mt-8 gap-3'):
                ui.button('Cancel', on_click=dialog.close).props('flat color=slate-7').classes('font-black')
                ui.button('Delete', on_click=lambda: self._do_delete(session_id, dialog)).props('unelevated color=red-6').classes('font-black rounded-lg')
        dialog.open()

    def _do_delete(self, session_id, dialog):
        if self.dm.delete_session(session_id):
            ui.notify('Session Purged', type='info', color='rose-600', position='bottom-right')
            dialog.close()
        else:
            ui.notify('Purge Failed', type='negative', position='bottom-right')
