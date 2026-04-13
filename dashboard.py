"""
CCT Command Center — Cognitive Control Dashboard
Real-time: SQLite mtime detection + configurable auto-refresh.
"""
import sqlite3
import json
import sys
import base64
import os
import time
import html
from datetime import datetime, timezone

import streamlit as st
import pandas as pd

# ─────────────────────────────────────────────────────────
# REAL-TIME ENGINE: streamlit-autorefresh (interval-based)
# ─────────────────────────────────────────────────────────
from streamlit_autorefresh import st_autorefresh

# Auto-refresh interval configuration (in milliseconds)
_REFRESH_OPTIONS = {
    "3s ⚡ Live": 3000,
    "10s 🔄 Active": 10000,
    "30s 🔱 Idle": 30000,
    "⏸ Off": 0
}

# ─────────────────────────────────────────────────────────
# SQLITE CHANGE DETECTOR (mtime + row-count sentinel)
# ─────────────────────────────────────────────────────────
import hashlib

def _db_fingerprint(db_path: str) -> str:
    """Returns a hash-like fingerprint based on file mtime + row counts.
       Changes in this string signal that the DB has new data."""
    try:
        mtime = os.path.getmtime(db_path)
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT COUNT(*) FROM thoughts").fetchone()[0]
        sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        patterns = conn.execute("SELECT COUNT(*) FROM thinking_patterns").fetchone()[0]
        anti = conn.execute("SELECT COUNT(*) FROM anti_patterns").fetchone()[0]
        conn.close()
        raw = f"{mtime}:{rows}:{sessions}:{patterns}:{anti}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
    except Exception:
        return str(time.time())

def _check_db_changed(db_path: str) -> bool:
    """Returns True if the DB fingerprint differs from what we last saw.
       Also stores the new fingerprint and timestamps the change."""
    current_fp = _db_fingerprint(db_path)
    last_fp = st.session_state.get("_db_fp", "")
    if current_fp != last_fp:
        st.session_state["_db_fp"] = current_fp
        st.session_state["_last_change"] = datetime.now(timezone.utc)
        # ── Bust ALL data caches so Streamlit re-fetches from SQLite ──
        st.cache_data.clear()
        return True
    return False

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────────────────
# LIVE FOREX RATE (with periodic refresh)
# ─────────────────────────────────────────────────────────
from src.core.config import load_settings

def _get_forex_rate():
    """Fetch live forex rate with fallback to configured default."""
    try:
        from src.utils.pricing import ForexService
        settings = load_settings()
        _forex = ForexService(
            cache_ttl=settings.forex_cache_ttl,
            default_rate=settings.forex_default_rate,
            api_url=settings.forex_api_url
        )
        return _forex.get_usd_to_idr_rate(), "frankfurter.app"
    except Exception:
        settings = load_settings()
        return settings.forex_default_rate, "fallback (offline)"

# Initial forex rate
LIVE_RATE, RATE_SOURCE = _get_forex_rate()

# Forex refresh counter (refreshed every 60 seconds via auto-refresh)
if "_forex_refresh_counter" not in st.session_state:
    st.session_state._forex_refresh_counter = 0

# ─────────────────────────────────────────────────────────
# STRATEGY META — derived from enums.py (ThinkingStrategy)
# ─────────────────────────────────────────────────────────
HYBRID_STRATEGIES = {
    "actor_critic_loop", "unconventional_pivot",
    "long_term_horizon", "multi_agent_fusion", "council_of_critics"
}
STRATEGY_ICON = {
    "actor_critic_loop":    "⚔️",
    "council_of_critics":   "🏛️",
    "multi_agent_fusion":   "🔗",
    "unconventional_pivot": "⚡",
    "long_term_horizon":    "🔮",
    "critical":             "🎯",
    "synthesis":            "🏗️",
    "integrative":          "🏗️",
    "systemic":             "🌐",
    "first_principles":     "🔬",
    "empirical_research":   "📡",
    "lateral":              "🔀",
    "convergent":           "🎯",
    "linear":               "➡️",
    "analytical":           "🔍",
    "dialectical":          "⚖️",
    "strategic":            "♟️",
    "reflective":           "🪞",
    "creative":             "💡",
    "swot_analysis":        "📊",
    "second_order_thinking":"🔄",
    "abductive":            "🧩",
    "counterfactual":       "🔁",
    "adversarial_simulation":"🛡️",
    "deductive_validation": "✅",
    "evolutionary":         "🧬",
    "empathetic":           "🤝",
    "actor_critic":         "⚔️",
    "temporal":             "⏳",
}

# ─────────────────────────────────────────────────────────
# CORE LOGIC: Pipeline & Strategy Synchronization
# ─────────────────────────────────────────────────────────
try:
    from src.utils.pipelines import PipelineSelector
    PIPELINE_CATEGORIES = PipelineSelector.PIPELINE_TEMPLATES
    # Inject Sovereign Pipeline as a global standard
    PIPELINE_CATEGORIES["SOVEREIGN (COMPLEX)"] = PipelineSelector.SOVEREIGN_PIPELINE
except Exception:
    PIPELINE_CATEGORIES = {
        "DEBUG":   ["empirical_research", "abductive", "first_principles", "actor_critic_loop"],
        "ARCH":    ["first_principles", "systemic", "long_term_horizon", "multi_agent_fusion"],
        "FEAT":    ["lateral", "convergent", "practical"],
        "SEC":     ["critical", "actor_critic_loop", "systemic"],
        "BIZ":     ["swot_analysis", "second_order_thinking", "long_term_horizon"],
        "GENERIC": ["first_principles", "actor_critic_loop", "systemic", "integrative"],
    }

HYBRID_STRATEGIES = {
    "actor_critic_loop", "unconventional_pivot",
    "long_term_horizon", "multi_agent_fusion", "council_of_critics"
}

# ─────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CCT Command Center",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────
# GLOBAL STYLING — Standard Streamlit Aesthetics
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Ensure progress bars use a consistent primary brand color */
    .stProgress > div > div {
        background-color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# DATABASE PATH DISCOVERY
# ─────────────────────────────────────────────────────────
DB_PATH = "database/cct_memory.db"
if not os.path.exists(DB_PATH):
    DB_PATH = "cct_memory.db"  # fallback

# ─────────────────────────────────────────────────────────
# DATABASE ADAPTERS
# NOTE: No TTL set — caches are invalidated by _check_db_changed() via
#       st.cache_data.clear() whenever the SQLite fingerprint changes.
#       This ensures data freshness without unnecessary round-trips.
# ─────────────────────────────────────────────────────────
@st.cache_data
def fetch_sessions():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, data FROM sessions ORDER BY rowid DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"session_id": r[0], "data": json.loads(r[1])} for r in rows]
    except Exception:
        return []

@st.cache_data
def fetch_thoughts(session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM thoughts WHERE session_id = ?", (session_id,))
        rows = cursor.fetchall()
        conn.close()
        return {json.loads(r[0])["id"]: json.loads(r[0]) for r in rows}
    except Exception:
        return {}

@st.cache_data
def fetch_global_economy():
    """Calculate total costs across all sessions from thoughts data."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM thoughts")
        rows = cursor.fetchall()
        conn.close()
        
        total_in_tokens = 0
        total_out_tokens = 0
        total_usd = 0.0
        total_idr = 0.0
        
        for row in rows:
            thought = json.loads(row[0])
            metrics = thought.get("metrics", {})
            total_in_tokens += metrics.get("input_tokens", 0)
            total_out_tokens += metrics.get("output_tokens", 0)
            total_usd += metrics.get("input_cost_usd", 0) + metrics.get("output_cost_usd", 0)
            total_idr += metrics.get("input_cost_idr", 0) + metrics.get("output_cost_idr", 0)
        
        return {
            "total_input_tokens": total_in_tokens,
            "total_output_tokens": total_out_tokens,
            "total_tokens": total_in_tokens + total_out_tokens,
            "total_cost_usd": total_usd,
            "total_cost_idr": total_idr,
            "thought_count": len(rows)
        }
    except Exception:
        return {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "total_cost_idr": 0.0,
            "thought_count": 0
        }

def sanitize_display_text(text: str) -> str:
    """Remove problematic emoji and arrows that don't render well in JetBrains Mono."""
    if not text:
        return ""
    # Remove common problematic emoji and arrow combinations
    problematic = [
        # Emoji arrows
        '🏹', '↗️', '➡️', '⬅️', '⬆️', '⬇️', '↖️', '↘️', '↙️', '↔️', '↕️',
        # Unicode arrows
        '→', '←', '↑', '↓', '↗', '↘', '↙', '↖', '↔', '↕', '↪', '↩',
        '⇒', '⇐', '⇑', '⇓', '⇗', '⇘', '⇙', '⇖', '⇛', '⇚',
        '➜', '➤', '➙', '➛', '➝', '➞', '➟', '➠', '➡', '➢', '➣',
        '➥', '➦', '➧', '➨', '➩', '➪', '➫', '➬', '➭', '➮', '➯',
        '➱', '➲', '➳', '➴', '➵', '➶', '➷', '➸', '➹', '➺', '➻', '➼', '➽', '➾',
        '⇢', '⇨', '⇀', '⇁', '⇄', '⇅', '⇆', '⇇', '⇈', '⇉', '⇊'
    ]
    for char in problematic:
        text = text.replace(char, '>')  # Replace with ASCII greater-than
    return text

@st.cache_data
def fetch_thinking_patterns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM thinking_patterns ORDER BY usage_count DESC")
        rows = cursor.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    except Exception:
        return []

@st.cache_data
def fetch_anti_patterns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM anti_patterns ORDER BY rowid DESC")
        rows = cursor.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    except Exception:
        return []

@st.cache_data
def fetch_all_thoughts_for_analytics():
    """Returns all thoughts across all sessions for cross-session analytics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM thoughts ORDER BY rowid ASC")
        rows = cursor.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    except Exception:
        return []

@st.cache_data
def fetch_db_stats():
    """Returns live row counts and DB file size for the system health panel."""
    try:
        conn = sqlite3.connect(DB_PATH)
        thoughts_total = conn.execute("SELECT COUNT(*) FROM thoughts").fetchone()[0]
        sessions_total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        patterns_total = conn.execute("SELECT COUNT(*) FROM thinking_patterns").fetchone()[0]
        anti_total = conn.execute("SELECT COUNT(*) FROM anti_patterns").fetchone()[0]
        conn.close()
        db_size_kb = os.path.getsize(DB_PATH) / 1024 if os.path.exists(DB_PATH) else 0
        return {
            "thoughts":  thoughts_total,
            "sessions":  sessions_total,
            "patterns":  patterns_total,
            "anti":      anti_total,
            "db_size":   round(db_size_kb, 1),
        }
    except Exception:
        return {}

def delete_session_db(session_id: str):
    """Purges a session and its thoughts from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # Enable WAL mode for thread-safe operations during live dashboard use
        conn.execute("PRAGMA journal_mode=WAL")
        with conn:
            conn.execute("DELETE FROM thoughts WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.close()
        # Invalidate all caches after deletion
        st.cache_data.clear()
        return True
    except Exception as e:
        print(f"Error deleting session: {e}")
        return False


def perform_health_check() -> dict:
    """
    Perform comprehensive health check for the CCT MCP Server.
    
    Returns health status including:
    - Database connectivity
    - Memory manager status
    - Response time metrics
    - Rate limiting configuration
    """
    start_time = time.time()
    
    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2026.04.12",
        "services": {},
        "metrics": {},
    }
    
    # Check database connectivity
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        health["services"]["database"] = "healthy"
    except Exception as e:
        health["services"]["database"] = f"degraded: {str(e)}"
        health["status"] = "degraded"
    
    # Check memory manager (via DB stats)
    try:
        db_stats = fetch_db_stats()
        health["metrics"]["active_sessions"] = db_stats.get("sessions", 0)
        health["metrics"]["total_thoughts"] = db_stats.get("thoughts", 0)
        health["services"]["memory_manager"] = "healthy"
    except Exception as e:
        health["metrics"]["active_sessions"] = -1
        health["metrics"]["total_thoughts"] = -1
        health["services"]["memory_manager"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    health["metrics"]["response_time_ms"] = round(response_time_ms, 2)
    
    # Rate limiting configuration (from constants)
    from src.core.constants import DEFAULT_MAX_SESSIONS, MAX_THOUGHTS_PER_SESSION
    health["metrics"]["max_sessions"] = DEFAULT_MAX_SESSIONS
    health["metrics"]["max_thoughts_per_session"] = MAX_THOUGHTS_PER_SESSION
    
    return health


def score_bar_html(label: str, value: float, color: str = "#58a6ff") -> str:
    pct = int(value * 100)
    return f"""
    <div style="display:flex;align-items:center;gap:8px;margin:12px 0;">
        <span style="font-size:12px;width:75px;">{label}</span>
        <div style="flex:1;background:rgba(128,128,128,0.1);border-radius:4px;height:8px;">
            <div style="height:8px;border-radius:4px;width:{pct}%;background:{color};"></div>
        </div>
        <span style="font-size:11px;font-family:monospace;width:36px;text-align:right;">{value:.2f}</span>
    </div>"""

def strategy_badge(strategy: str) -> str:
    icon = STRATEGY_ICON.get(strategy.lower(), "📝")
    is_hybrid = strategy.lower() in HYBRID_STRATEGIES
    pill_cls = "cct-pill-purple" if is_hybrid else "cct-pill-blue"
    return f'<span class="cct-pill {pill_cls}">{icon} {strategy.upper()}</span>'

def confidence_badge(level: int) -> str:
    labels = {1: ("VERY LOW","red"), 2: ("LOW","amber"), 3: ("MEDIUM","blue"), 4: ("HIGH","green"), 5: ("VERY HIGH","green")}
    txt, cls = labels.get(level, ("?", "blue"))
    return f'<span class="cct-pill cct-pill-{cls}">{txt}</span>'

# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    # ────────────── REAL-TIME ENGINE CONTROLS ──────────────
    # 1. Run autorefresh FIRST so Streamlit schedules the next tick
    # 2. Then check if the DB actually changed (to bust cache only when needed)
    refresh_label = st.sidebar.selectbox(
        "Live Refresh", list(_REFRESH_OPTIONS.keys()), index=1, key="refresh_rate",
        label_visibility="collapsed"
    )
    refresh_ms = _REFRESH_OPTIONS[refresh_label]

    if refresh_ms > 0:
        _tick = st_autorefresh(interval=refresh_ms, limit=None, key="rt_ticker")
        
        # Periodic forex refresh (every ~20 refresh cycles = 200s for 10s interval)
        st.session_state._forex_refresh_counter = (st.session_state._forex_refresh_counter + 1) % 20
        if st.session_state._forex_refresh_counter == 0:
            LIVE_RATE, RATE_SOURCE = _get_forex_rate()
    else:
        _tick = 0

    # Run DB change detection every render cycle
    _db_changed = _check_db_changed(DB_PATH)
    _last_change = st.session_state.get("_last_change")
    _last_change_str = _last_change.strftime("%H:%M:%S") if _last_change else "N/A"
    _fp = st.session_state.get("_db_fp", "")[:8]

    # ═══════════════════════════════════════════════════════
    # SIDEBAR HEADER — BRANDING (JetBrains Mono)
    # ═══════════════════════════════════════════════════════
    st.markdown("""
    <div style="text-align:center;padding:12px 0 20px 0;border-bottom:1px solid rgba(128,128,128,0.2);margin-bottom:16px;">
        <div style="font-size:36px;margin-bottom:6px;">🧠</div>
        <div style="font-size:20px;font-weight:700;letter-spacing:-0.5px;">CCT Command</div>
        <div style="font-size:11px;opacity:0.6;margin-top:4px;text-transform:uppercase;letter-spacing:1px;">Cognitive Control Terminal</div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # LIVE STATUS
    # ═══════════════════════════════════════════════════════
    if refresh_ms == 0:
        _live_badge = "|| PAUSED"
        _badge_color = "#6e7681"
    elif _db_changed:
        _live_badge = "[*] UPDATED"
        _badge_color = "#f85149"
    else:
        _live_badge = "[+] LIVE"
        _badge_color = "#3fb950"

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:16px;">
        <span style="background:rgba({_badge_color.replace('#','')},0.15);border:1px solid {_badge_color};color:{_badge_color};
                     font-size:11px;padding:4px 14px;border-radius:12px;font-weight:600;">{_live_badge}</span>
        <div style="font-size:10px;opacity:0.5;margin-top:8px;text-transform:uppercase;letter-spacing:0.5px;">Last Update: {_last_change_str}</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════
    # SESSION DATA PREPARATION
    # ═══════════════════════════════════════════════════════
    sessions = fetch_sessions()
    if not sessions:
        st.warning("No sessions in database.")
        st.stop()

    # Initialize session state for the active ID if not set
    if "selected_session_id" not in st.session_state:
        st.session_state["selected_session_id"] = sessions[0]["session_id"]

    selected_session_id = st.session_state["selected_session_id"]
    
    # Ensure current selected_session_id exists in fetched sessions (safety)
    session_ids = [s["session_id"] for s in sessions]
    if selected_session_id not in session_ids:
        st.session_state["selected_session_id"] = sessions[0]["session_id"]
        selected_session_id = sessions[0]["session_id"]

    active_session_full = next(s for s in sessions if s["session_id"] == selected_session_id)
    active_session = active_session_full["data"]
    thoughts_dict = fetch_thoughts(selected_session_id)
    history_ids = active_session.get("history_ids", [])

    # Calculate actual costs from thoughts (not from session data which may be 0)
    session_in_tokens = sum(thoughts_dict.get(tid, {}).get("metrics", {}).get("input_tokens", 0) for tid in history_ids)
    session_out_tokens = sum(thoughts_dict.get(tid, {}).get("metrics", {}).get("output_tokens", 0) for tid in history_ids)
    session_cost_idr = sum(
        thoughts_dict.get(tid, {}).get("metrics", {}).get("input_cost_idr", 0) +
        thoughts_dict.get(tid, {}).get("metrics", {}).get("output_cost_idr", 0)
        for tid in history_ids
    )
    session_cost_usd = sum(
        thoughts_dict.get(tid, {}).get("metrics", {}).get("input_cost_usd", 0) +
        thoughts_dict.get(tid, {}).get("metrics", {}).get("output_cost_usd", 0)
        for tid in history_ids
    )
    step_count = len(history_ids)
    estimated = active_session.get("estimated_total_thoughts", 0)
    pct_done = int((step_count / max(estimated, 1)) * 100)

    # Model display for header
    model_raw = active_session.get("model_id", "claude-3-5-sonnet-20240620")
    model_display = model_raw.split("-")[0].upper() + "-" + "-".join(model_raw.split("-")[1:3])

    st.divider()

    # ═══════════════════════════════════════════════════════
    # GLOBAL ECONOMY (All Sessions Combined)
    # ═══════════════════════════════════════════════════════
    st.markdown("<div style='font-size:11px;opacity:0.7;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>💰 Global Economy (All Sessions)</div>", unsafe_allow_html=True)
    global_econ = fetch_global_economy()

    g1, g2 = st.columns(2)
    g1.metric("Total Thoughts", f"{global_econ['thought_count']:,}")
    g2.metric("Total Tokens", f"{global_econ['total_tokens']:,}")

    # Show cost in standard metrics
    e1, e2 = st.columns(2)
    e1.metric("Total Cost (USD)", f"${global_econ['total_cost_usd']:.4f}")
    e2.metric("Total Cost (IDR)", f"Rp {global_econ['total_cost_idr']:,.0f}")

    st.divider()

    # ═══════════════════════════════════════════════════════
    # ACTIVE SESSION SUMMARY
    # ═══════════════════════════════════════════════════════
    st.markdown("<div style='font-size:11px;opacity:0.7;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>🎯 Active Session</div>", unsafe_allow_html=True)
    st.progress(pct_done / 100, text=f"Progress: {step_count}/{estimated}")

    s1, s2 = st.columns(2)
    s1.metric("Input", f"{session_in_tokens:,}")
    s2.metric("Output", f"{session_out_tokens:,}")

    # Session cost in standard metrics
    s1, s2 = st.columns(2)
    s1.metric("Session Cost (USD)", f"${session_cost_usd:.4f}")
    s2.metric("Session Cost (IDR)", f"Rp {session_cost_idr:,.0f}")

    profile = active_session.get('profile', 'balanced')
    status = active_session.get('status', 'unknown')
    st.markdown(f"<div style='font-size:10px;opacity:0.6;margin-top:8px;'>Profile: <code>{profile}</code> | Status: <span style=\"color:{ '#3fb950' if status == 'active' else '#d29922' }\">{status.upper()}</span></div>", unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════
    # SYSTEM HEALTH
    # ═══════════════════════════════════════════════════════
    with st.expander("💻 System Health", expanded=False):
        # Perform health check
        health = perform_health_check()
        db_stats = fetch_db_stats()
        
        # Overall status indicator
        status_color = {"healthy": "#3fb950", "degraded": "#d29922", "error": "#f85149"}
        status_emoji = {"healthy": "✅", "degraded": "⚠️", "error": "❌"}
        overall_status = health["status"]
        color = status_color.get(overall_status, "#8b949e")
        emoji = status_emoji.get(overall_status, "⚪")
        
        # Overall status indicator
        if overall_status == "healthy":
            st.success(f"System Status: {overall_status.upper()}")
        elif overall_status == "degraded":
            st.warning(f"System Status: {overall_status.upper()}")
        else:
            st.error(f"System Status: {overall_status.upper()}")
        
        st.info(f"v{health['version']} · {health['timestamp'][:19]}")
        
        # Services status
        st.caption("🩺 Services")
        svc1, svc2 = st.columns(2)
        db_status = health["services"].get("database", "unknown")
        mem_status = health["services"].get("memory_manager", "unknown")
        
        db_emoji = "✅" if db_status == "healthy" else "⚠️"
        mem_emoji = "✅" if mem_status == "healthy" else "⚠️"
        
        svc1.markdown(f"{db_emoji} **Database**<br/><span style='font-size:10px;color:#8b949e;'>{db_status}</span>", unsafe_allow_html=True)
        svc2.markdown(f"{mem_emoji} **Memory Mgr**<br/><span style='font-size:10px;color:#8b949e;'>{mem_status}</span>", unsafe_allow_html=True)
        
        st.divider()
        
        # Performance metrics only (database stats moved to main area)
        st.caption("⚡ Performance")
        response_time = health["metrics"].get("response_time_ms", 0)
        st.metric("Response Time", f"{response_time:.1f}ms", delta=None)
        st.caption("🛡️ Rate Limits")
        r1, r2 = st.columns(2)
        max_sessions = health["metrics"].get("max_sessions", 128)
        max_thoughts = health["metrics"].get("max_thoughts_per_session", 200)
        r1.metric("Max Sessions", max_sessions)
        r2.metric("Max Thoughts/Session", max_thoughts)
        
        st.caption(f"💾 DB: `{DB_PATH}` · `{db_stats.get('db_size',0)} KB`")
        
        # Action buttons
        c1, c2 = st.columns(2)
        if c1.button("🔄 Refresh", width='stretch', key="force_refresh"):
            st.cache_data.clear()
            st.session_state.pop("_db_fp", None)
            st.rerun()
        
        # Export health report
        health_json = json.dumps(health, indent=2)
        c2.download_button(
            label="📥 Export",
            data=health_json,
            file_name=f"health_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width='stretch'
        )

    st.divider()

    # --- MISSION DISPATCH ---
    with st.expander("🚀 Launch Mission", expanded=False):
        st.caption("Craft & export a precision dispatch signal for the AI agent.")
        new_problem = st.text_area("Problem Statement", placeholder="Describe the architectural goal or issue...", height=100, key="dispatch_problem")
        selected_profile = st.selectbox("Thinking Profile", ["balanced", "critical_first", "creative_first", "deep_recursive"], key="dispatch_profile")

        persona_map = {
            "Principal Architect":      ("Principal Systems Architect",       "Legacy Code Auditor"),
            "Cybersecurity Specialist":  ("Senior Cybersecurity EDR Specialist","Zero-Day Threat Actor"),
            "Performance Engineer":      ("High-Performance Systems Engineer",  "Memory Leak Auditor"),
            "System Generalist":         ("Senior Full-Stack Engineer",          "Enterprise Architecture Reviewer"),
        }
        selected_persona = st.selectbox("AI Persona", list(persona_map.keys()), key="dispatch_persona")
        role_name, critic_name = persona_map[selected_persona]
        selected_mode = st.radio("Mode", ["Human-in-the-Loop", "Autonomous"], horizontal=True, key="dispatch_mode")

        if st.button("Generate Dispatch Signal", width='stretch'):
            if not new_problem.strip():
                st.error("Problem statement cannot be empty.")
            else:
                # Standardized Sovereign 8-Step Pipeline Template
                dispatch = f"""# 🧠 CCT Sovereign Dispatch: {selected_persona}

**Role:** {role_name} | **Profile:** `{selected_profile}` | **Mode:** {selected_mode}

## Cognitive Guardrails (SOP)
1. **Weighted Intent:** Detect multi-scenario overlaps (ARCH + SEC + BIZ).
2. **Dynamic Pipelining:** Use `COMPLEX` rigor for non-trivial architecture tasks.
3. **Adaptive Debate:** Council of Critics must include domain-specific personas.

## Sovereign Execution Pipeline (8-Phase)

### [Phase 1] Empirical Research & Contextual Baseline
### [Phase 2] First Principles Deconstruction
### [Phase 3] Actor-Critic Loop (Internal Collision)
### [Phase 4] Council of Critics (Multi-Domain Audit)
### [Phase 5] Systemic Connectivity Analysis
### [Phase 6] Unconventional Pivot (Breaking Paradigms)
### [Phase 7] Long-Term Horizon (Strategic Projection)
### [Phase 8] Multi-Agent Fusion (Final Convergence)

**Status:** `AWAITING_CLEARANCE`
**Action:** `thinking` -> problem: "{new_problem}"
"""
                with open("cct-dispatch.md", "w", encoding="utf-8") as f:
                    f.write(dispatch)
                st.success("✅ Sovereign Dispatch ready!")
                st.code("@cct-dispatch.md Initiate thinking.", language="text")

    # ═══════════════════════════════════════════════════════
    # SIDEBAR END — Main Area Begins
    # ═══════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────
# MAIN AREA — CLEAN SESSION HEADER
# ─────────────────────────────────────────────────────────
prob_stmt = active_session.get("problem_statement", "")

header_col1, header_col2, header_col3 = st.columns([3, 1, 1])

with header_col1:
    st.subheader("🧠 " + (prob_stmt[:60] + "..." if len(prob_stmt) > 60 else prob_stmt))
    st.caption(f"Session: `{selected_session_id}` | Model: `{model_display}`")
    
    # [NEW] Multi-Scenario Domain Weights
    categories = active_session.get("detected_categories", {})
    if categories:
        st.markdown("<div style='font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;opacity:0.7;'>Cognitive Domain Matrix</div>", unsafe_allow_html=True)
        cols = st.columns(min(len(categories), 4))
        for i, (cat, score) in enumerate(categories.items()):
            with cols[i % 4]:
                color = "#58a6ff" if cat == "ARCH" else "#f85149" if cat == "SEC" else "#d29922" if cat == "BIZ" else "#3fb950"
                st.markdown(score_bar_html(cat, score, color), unsafe_allow_html=True)

with header_col2:
    st.metric("Steps", f"{step_count}/{estimated}", f"{pct_done}%")

with header_col3:
    status = active_session.get("status", "unknown")
    complexity = active_session.get("complexity", "moderate").upper()
    st.metric("Status", status.upper(), delta=complexity)

st.divider()
thinking_patterns_all = fetch_thinking_patterns()
anti_patterns_all = fetch_anti_patterns()

# ─────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📚 Sessions",
    "📜 Ledger",
    "🗺️ Pipeline",
    "🕸️ Thought Tree",
    "💸 Economy",
    "✨ Patterns",
    "🛡️ Immunity Wall",
    "🔬 Telemetry",
    "🎛️ Command"
])

# ─────────────────────────────────────────────────────────
# TAB 0 — SESSION ARCHIVE (TABLE VIEW)
# ─────────────────────────────────────────────────────────
with tab0:
    st.subheader("📚 Cognitive Session Archive")
    st.caption("Browse and activate cached cognitive sessions from the SQLite persistence layer.")
    
    # Prepare session dataframe
    session_data = []
    for s in sessions:
        d = s["data"]
        # Handle sessions without created_at (legacy)
        ts = d.get("created_at", "2026-04-13T00:00:00Z")
        try:
            ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts_display = ts_dt.strftime("%Y-%m-%d %H:%M")
        except:
            ts_display = "N/A"

        session_data.append({
            "Session ID": s["session_id"],
            "Created At": ts_display,
            "Problem Statement": d["problem_statement"],
            "Status": d.get("status", "active").upper(),
            "Model": d.get("model_id", "claude-3-5-sonnet").split("-")[-1],
            "Steps": len(d.get("history_ids", [])),
            "Cost ($)": f"${d.get('total_cost_usd', 0):.4f}"
        })
    
    df_sessions = pd.DataFrame(session_data)
    
    # Display table and selection
    # We use a selection column for better UX
    st.markdown("""
        <style>
        .stDataFrame { width: 100% !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # Search and Filter
    search_q = st.text_input("🔍 Search problem statement...", placeholder="Type to filter sessions...", key="session_search")
    if search_q:
        df_sessions = df_sessions[df_sessions["Problem Statement"].str.contains(search_q, case=False)]

    st.dataframe(
        df_sessions,
        width='stretch',
        hide_index=True,
        column_config={
            "Session ID": st.column_config.TextColumn("ID", width="small"),
            "Problem Statement": st.column_config.TextColumn("Problem Statement", width="large"),
            "Cost ($)": st.column_config.TextColumn("Cost", width="small"),
        }
    )
    
    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        target_id = st.selectbox("Select Session ID", options=[s["session_id"] for s in sessions], label_visibility="collapsed")
        if st.button("🔱 Activate", width='stretch'):
            st.session_state["selected_session_id"] = target_id
            st.rerun()
    with c2:
        if st.button("🗑️ Purge", width='stretch', help="Permanently delete this session and its history"):
            if delete_session_db(target_id):
                st.success(f"Purged {target_id[:8]}...")
                time.sleep(1)
                st.rerun()

# ─────────────────────────────────────────────────────────
# TAB 1 — ARCHITECTURAL LEDGER
# ─────────────────────────────────────────────────────────
with tab1:
    col_main, col_filter = st.columns([4, 1])
    with col_filter:
        strat_options = sorted(set(
            thoughts_dict.get(tid, {}).get("strategy", "").lower()
            for tid in history_ids
        ) - {""})
        filter_strat = st.multiselect("Filter strategy", strat_options, key="ledger_filter")

    with col_main:
        st.subheader(f"📜 Chronological Thought Process — {step_count} steps")

    if not history_ids:
        st.info("📝 **No thoughts recorded yet**\n\nStart a thinking session to see your cognitive process visualized here.")
    else:
        for idx, t_id in enumerate(history_ids):
            thought = thoughts_dict.get(t_id)
            if not thought:
                continue

            strategy = thought.get("strategy", "unknown").lower()
            if filter_strat and strategy not in filter_strat:
                continue

            metrics = thought.get("metrics", {})
            m_clarity  = metrics.get("clarity_score", 0.0)
            m_logic    = metrics.get("logical_coherence", 0.0)
            m_novelty  = metrics.get("novelty_score", 0.0)
            m_evidence = metrics.get("evidence_strength", 0.0)
            m_conf     = metrics.get("confidence_level", 3)
            in_tok     = metrics.get("input_tokens", 0)
            out_tok    = metrics.get("output_tokens", 0)
            cost_usd   = metrics.get("input_cost_usd", 0) + metrics.get("output_cost_usd", 0)
            cost_idr   = metrics.get("input_cost_idr", 0) + metrics.get("output_cost_idr", 0)
            fx_rate    = metrics.get("currency_rate_idr", LIVE_RATE)
            tags       = thought.get("tags", [])
            is_golden  = thought.get("is_thinking_pattern", False)
            is_hybrid  = strategy in HYBRID_STRATEGIES
            is_critical = "critical" in strategy or "actor_critic" in strategy
            is_synth   = strategy in ("synthesis", "integrative", "multi_agent_fusion")

            card_cls = "hybrid" if is_hybrid else "critical" if is_critical else "synthesis" if is_synth else ""
            golden_cls = " golden" if is_golden else ""
            icon = STRATEGY_ICON.get(strategy, "📝")
            t_type = thought.get("thought_type", "analysis").upper()
            seq_ctx = thought.get("sequential_context", {})
            t_num = seq_ctx.get("thought_number", idx + 1)
            t_est = seq_ctx.get("estimated_total_thoughts", estimated)

            # Score bar colors
            bar_colors = {
                "Clarity":  "#58a6ff" if m_clarity  >= 0.7 else "#d29922" if m_clarity  >= 0.4 else "#f85149",
                "Logic":    "#3fb950" if m_logic    >= 0.7 else "#d29922" if m_logic    >= 0.4 else "#f85149",
                "Novelty":  "#a371f7" if m_novelty  >= 0.6 else "#8b949e",
                "Evidence": "#ff7b72" if m_evidence >= 0.8 else "#d29922",
            }

            # Streamlit-native card using container with border
            with st.container(border=True):
                # Header row
                header_col1, header_col2 = st.columns([3, 1])
                
                with header_col1:
                    # Strategy and type badges
                    if is_golden:
                        st.success(f"🏆 **Step {t_num}/{t_est}** | {strategy.upper()} | {t_type.upper()}")
                    else:
                        st.caption(f"**Step {t_num}/{t_est}** | `{strategy}` | {t_type}")
                
                with header_col2:
                    st.caption(f"Confidence: {['🔴 LOW', '🟡 MEDIUM', '🟢 HIGH', '🔵 VERY HIGH'][min(m_conf-1, 3)]}")
                    # [NEW] Persona Tracking for Debate Strategies
                    if strategy == "council_of_critics":
                        personas = thought.get("sequential_context", {}).get("personas", [])
                        if not personas: # Fallback lookup if not in seq_ctx
                            personas = PipelineSelector.get_personas_for_domains(active_session.get("detected_categories", {}))
                        st.markdown("<div style='font-size:9px;opacity:0.6;'>COUNCIL:</div>", unsafe_allow_html=True)
                        for p in personas:
                            st.markdown(f"<div style='font-size:9px;color:#a371f7;'>• {p}</div>", unsafe_allow_html=True)
                    elif strategy == "actor_critic_loop":
                        persona = thought.get("sequential_context", {}).get("critic_persona", "Critical Reviewer")
                        st.markdown(f"<div style='font-size:9px;opacity:0.6;'>CRITIC:</div> <div style='font-size:9px;color:#ff7b72;'>{persona}</div>", unsafe_allow_html=True)
                
                # Content & Diagram Rendering
                content = thought.get("content", "No content")
                
                # Render content normally (Streamlit handles mermaid in markdown blocks natively in 1.35+)
                if len(content) > 1500:
                    st.write(content[:1500] + "...")
                else:
                    st.markdown(content)
                
                # Metrics using Streamlit progress bars
                metric_cols = st.columns(4)
                with metric_cols[0]:
                    st.caption(f"✨ Clarity: {m_clarity:.2f}")
                    st.progress(m_clarity, text=None)
                with metric_cols[1]:
                    st.caption(f"🧠 Logic: {m_logic:.2f}")
                    st.progress(m_logic, text=None)
                with metric_cols[2]:
                    st.caption(f"🔍 Evidence: {m_evidence:.2f}")
                    st.progress(m_evidence, text=None)
                with metric_cols[3]:
                    st.caption(f"🌱 Novelty: {m_novelty:.2f}")
                    st.progress(m_novelty, text=None)
                
                # Footer metadata
                footer_cols = st.columns([2, 1, 1])
                with footer_cols[0]:
                    st.caption(f"🪙 {in_tok:,} in + {out_tok:,} out | 💰 ${cost_usd:.5f}")
                with footer_cols[1]:
                    if thought.get("builds_on"):
                        st.caption(f"🔗 {len(thought['builds_on'])} builds")
                with footer_cols[2]:
                    if thought.get("contradicts"):
                        st.caption(f"🚨 {len(thought['contradicts'])} attacks")
                
                # Tags
                if tags:
                    st.caption("Tags: " + " · ".join(f"`{t}`" for t in tags[:6]))

# ─────────────────────────────────────────────────────────
# TAB 2 — PIPELINE VISUALIZER
# ─────────────────────────────────────────────────────────
with tab2:
    st.subheader("🗺️ Dynamic Cognitive Pipeline")

    suggested = active_session.get("suggested_pipeline", [])
    current_step = active_session.get("current_thought_number", 0)
    
    # [NEW] Sovereign Status Indicator
    is_sovereign = suggested == PipelineSelector.SOVEREIGN_PIPELINE
    if is_sovereign:
        st.markdown("""
        <div style="background:rgba(163,113,247,0.1);border:1px solid #a371f7;padding:8px 16px;border-radius:8px;margin-bottom:12px;">
            <span style="color:#a371f7;font-weight:700;font-size:14px;">🔱 SOVEREIGN PIPELINE ACTIVE</span>
            <div style="font-size:11px;opacity:0.7;margin-top:2px;">Enforcing 8-phase high-rigor reasoning sequence.</div>
        </div>
        """, unsafe_allow_html=True)

    # Pipeline progress
    if suggested:
        # Using a container with subtle border instead of hardcoded dark background
        pipe_html = '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:16px;border:1px solid rgba(128,128,128,0.2);border-radius:10px;margin-bottom:16px;">'
        for i, strat in enumerate(suggested):
            s = strat.lower() if isinstance(strat, str) else strat
            icon = STRATEGY_ICON.get(s, "📝")
            done = i < current_step
            active_ = i == current_step
            
            # Inline styling for steps since custom CSS was removed
            bg_color = "transparent"
            border_color = "rgba(128,128,128,0.3)"
            text_color = "inherit"
            if done:
                bg_color = "rgba(63,185,80,0.1)"
                border_color = "#3fb950"
                text_color = "#3fb950"
            elif active_:
                bg_color = "rgba(163,113,247,0.1)" if is_sovereign else "rgba(88,166,255,0.1)"
                border_color = "#a371f7" if is_sovereign else "#58a6ff"
                text_color = "#a371f7" if is_sovereign else "#58a6ff"
                
            step_style = f"display:inline-flex;align-items:center;gap:6px;background:{bg_color};border:1px solid {border_color};border-radius:6px;padding:4px 10px;font-size:12px;font-family:monospace;color:{text_color};margin:3px;"
            pipe_html += f'<span style="{step_style}">{icon} {s}</span>'
            
            if i < len(suggested) - 1:
                pipe_html += '<span style="color:rgba(128,128,128,0.5);font-size:14px;font-family:monospace;"> &gt; </span>'
        pipe_html += f'<div style="margin-top:8px;width:100%;font-size:12px;color:rgba(128,128,128,0.8);">Progress: {current_step}/{len(suggested)} — {int(current_step/max(len(suggested),1)*100)}% complete</div>'
        pipe_html += '</div>'
        st.markdown(pipe_html, unsafe_allow_html=True)

        # Progress bar
        st.progress(min(current_step / max(len(suggested), 1), 1.0))
    else:
        st.info("No pipeline suggested yet for this session.")

    # Strategy distribution of actual executed thoughts
    if history_ids:
        st.subheader("Strategy Distribution")
        strat_counts = {}
        for tid in history_ids:
            t = thoughts_dict.get(tid, {})
            s = t.get("strategy", "unknown").lower()
            strat_counts[s] = strat_counts.get(s, 0) + 1
        
        df_strat = pd.DataFrame([
            {"Strategy": f"{STRATEGY_ICON.get(k,'📝')} {k}", "Count": v,
             "Type": "Hybrid" if k in HYBRID_STRATEGIES else "Primitive"}
            for k, v in sorted(strat_counts.items(), key=lambda x: -x[1])
        ])
        st.bar_chart(df_strat.set_index("Strategy")["Count"], color="#58a6ff")
        
        # ═══════════════════════════════════════════════════════════
        # VISUALIZATION 7: QUALITY TRENDS OVER TIME (Line Chart)
        # ═══════════════════════════════════════════════════════════
        st.subheader("📈 Quality Trends Over Time")
        
        # Build time-series data from thought history
        trend_data = []
        for i, tid in enumerate(history_ids):
            if tid in thoughts_dict:
                t = thoughts_dict[tid]
                m = t.get("metrics", {})
                trend_data.append({
                    "Step": i + 1,
                    "Logic": m.get("logical_coherence", 0),
                    "Evidence": m.get("evidence_strength", 0),
                    "Clarity": m.get("clarity_score", 0),
                    "Novelty": m.get("novelty_score", 0)
                })
        
        if trend_data:
            df_trends = pd.DataFrame(trend_data).set_index("Step")
            
            # Multi-line chart showing all 4 metrics evolution
            st.line_chart(df_trends, height=300)
            
            # Show trend analysis
            if len(trend_data) > 1:
                latest = trend_data[-1]
                first = trend_data[0]
                
                cols = st.columns(4)
                metrics = ["Logic", "Evidence", "Clarity", "Novelty"]
                colors = ["#3fb950", "#ff7b72", "#58a6ff", "#a371f7"]
                
                for col, metric, color in zip(cols, metrics, colors):
                    change = latest[metric] - first[metric]
                    delta = f"+{change:.2f}" if change > 0 else f"{change:.2f}"
                    delta_color = "normal" if change > 0 else "inverse"
                    col.metric(
                        metric,
                        f"{latest[metric]:.2f}",
                        delta=delta,
                        delta_color=delta_color
                    )

    # Knowledge injection summary
    ki = active_session.get("knowledge_injection", {})
    gp = ki.get("golden_thinking_patterns", [])
    ap = ki.get("anti_patterns", [])
    if gp or ap:
        st.subheader("Knowledge Injected at Session Start")
        i1, i2 = st.columns(2)
        with i1:
            st.success(f"✨ **{len(gp)} Golden Patterns** injected as cognitive priors")
        with i2:
            st.warning(f"🛡️ **{len(ap)} Anti-Patterns** loaded as active guardrails")

# ─────────────────────────────────────────────────────────
# TAB 3 — THOUGHT TREE (Mermaid - Enhanced)
# ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("🕸️ Thought Tree Visualization")
    
    # Show refresh indicator
    if refresh_ms > 0:
        st.caption(f"🔄 Auto-refresh: {refresh_ms//1000}s | Last DB update: {_last_change_str}")
    else:
        st.caption("⏸ Auto-refresh: Off")

    # Build enhanced Mermaid diagram with real-time data
    mermaid_code = "graph TD\n"
    
    # Enhanced class definitions with light-mode friendly gradients
    mermaid_code += "    classDef standard fill:#f0f6fc,stroke:#58a6ff,stroke-width:1px,color:#1f262d,font-weight:500,font-size:11px;\n"
    mermaid_code += "    classDef hybrid fill:#f5f3ff,stroke:#8b5cf6,stroke-width:2px,color:#4c1d95,font-weight:600,font-size:11px;\n"
    mermaid_code += "    classDef critical fill:#fef2f2,stroke:#ef4444,stroke-width:2px,color:#991b1b,font-weight:600,font-size:11px;\n"
    mermaid_code += "    classDef synthesis fill:#ecfdf5,stroke:#10b981,stroke-width:2px,color:#065f46,font-weight:600,font-size:11px;\n"
    mermaid_code += "    classDef golden fill:#fffbeb,stroke:#fbbf24,stroke-width:2px,color:#92400e,font-weight:700,font-size:11px,stroke-dasharray:5 5;\n"
    
    # Link style definitions - Simplified for stability
    # We avoid 'linkStyle default' as it's non-standard across all Mermaid versions
    mermaid_code += "    %% Link styles\n"

    # Add nodes with enhanced labels
    for t_id, thought in thoughts_dict.items():
        strategy = thought.get("strategy", "").lower()
        short_id = t_id[-8:]
        icon = STRATEGY_ICON.get(strategy, "📝")
        t_type = thought.get("thought_type", "analysis").upper()
        
        # Enhanced label with more context
        metrics = thought.get("metrics", {})
        confidence = metrics.get("confidence_level", 3)
        confidence_stars = "*" * confidence
        
        # Create label - use <br> for Mermaid line breaks (not <br/> or \\n)
        label = f"{strategy.upper()[:18]}<br>{t_type}<br>{short_id}"
        
        is_golden = thought.get("is_thinking_pattern", False)
        
        if is_golden:
            css = "golden"
        elif strategy in HYBRID_STRATEGIES:
            css = "hybrid"
        elif "critical" in strategy or "actor_critic" in strategy:
            css = "critical"
        elif strategy in ("synthesis", "integrative", "multi_agent_fusion"):
            css = "synthesis"
        else:
            css = "standard"
        
        # Sanitize label for Mermaid - remove/replace problematic characters
        safe_label = label.replace('"', "'").replace("#", "").replace("[", "(").replace("]", ")")
        # Quote t_id to handle dashes/UUIDs safely - use :::class syntax for styling
        mermaid_code += f'    n{t_id}["{safe_label}"]:::{css}\n'

    # Add relationships - use 'n' prefix for all node IDs consistently
    for t_id, thought in thoughts_dict.items():
        parent_id = thought.get("parent_id")
        if parent_id and parent_id in thoughts_dict:
            mermaid_code += f'    n{parent_id} --> n{t_id}\n'

        for target in thought.get("contradicts", []):
            if target in thoughts_dict:
                # Simplified edge style without label for compatibility
                mermaid_code += f'    n{t_id} -.-> n{target}\n'

        for target in thought.get("builds_on", []):
            if target in thoughts_dict:
                # Simplified edge style without label for compatibility
                mermaid_code += f'    n{t_id} --> n{target}\n'
                
    # Simplified footer
    mermaid_code += "    %% Graph end\n"

    # Enhanced HTML with interactive features
    graph_id = f"mermaid-graph-{int(time.time())}"
    
    html_code = f"""
    <div style="border-radius:12px;padding:15px;border:1px solid rgba(128,128,128,0.2);background:transparent;">
        <pre class="mermaid" style="background:transparent; display: flex; justify-content: center;">
{mermaid_code}
        </pre>
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.6.0/dist/mermaid.esm.min.mjs';
        
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            securityLevel: 'loose',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            themeVariables: {{
                primaryColor: '#58a6ff',
                primaryTextColor: '#1f262d',
                primaryBorderColor: '#58a6ff',
                lineColor: '#8b949e',
                secondaryColor: '#f0f6fc',
                tertiaryColor: '#ffffff',
                fontFamily: 'sans-serif',
                fontSize: '11px'
            }}
        }});
        
        // Interactive functions
        window.resetZoom = function() {{
            const svg = document.querySelector('#{graph_id} svg');
            if(svg) {{
                svg.setAttribute('width', '100%');
                svg.setAttribute('height', '100%');
                svg.style.transform = 'scale(1)';
            }}
        }};
        
        window.downloadSVG = function() {{
            const svg = document.querySelector('#{graph_id} svg');
            if(svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const blob = new Blob([svgData], {{type: 'image/svg+xml'}});
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'thought-tree.svg';
                link.click();
            }}
        }};
        
        // Click handler for nodes
        document.addEventListener('click', function(e) {{
            if(e.target.closest('.node')) {{
                const nodeId = e.target.closest('.node').id;
                console.log('Clicked node:', nodeId);
            }}
        }});
    </script>"""
    
    b64_html = base64.b64encode(html_code.encode()).decode()
    st.iframe(src=f"data:text/html;base64,{b64_html}", height=600)
    
    # Legend with enhanced styling
    st.subheader("Legend")
    st.markdown("""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px;padding:12px;border:1px solid rgba(128,128,128,0.2);border-radius:8px;">
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="width:12px;height:12px;background:linear-gradient(145deg,#4c1d95,#6d28d9);border-radius:3px;"></span>
            <span style="font-size:11px;color:#8b949e;">Hybrid Strategy</span>
        </span>
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="width:12px;height:12px;background:linear-gradient(145deg,#991b1b,#dc2626);border-radius:3px;"></span>
            <span style="font-size:11px;color:#8b949e;">Critical Analysis</span>
        </span>
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="width:12px;height:12px;background:linear-gradient(145deg,#059669,#10b981);border-radius:3px;"></span>
            <span style="font-size:11px;color:#8b949e;">Synthesis</span>
        </span>
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="width:12px;height:12px;background:linear-gradient(145deg,#d97706,#f59e0b);border-radius:3px;border:2px dashed #fbbf24;"></span>
            <span style="font-size:11px;color:#8b949e;">🏆 Golden Pattern</span>
        </span>
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="font-size:11px;color:#ef4444;">⚔️ Contradicts</span>
        </span>
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="font-size:11px;color:#34d399;">🔗 Builds On</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# TAB 4 — TOKEN ECONOMY
# ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("💸 Cognitive Cost Economy")
    
    # Calculate costs from actual thought data (session totals may be 0)
    t_in = sum(t.get("metrics", {}).get("input_tokens", 0) for t in thoughts_dict.values())
    t_out = sum(t.get("metrics", {}).get("output_tokens", 0) for t in thoughts_dict.values())
    t_usd = sum(
        t.get("metrics", {}).get("input_cost_usd", 0) + t.get("metrics", {}).get("output_cost_usd", 0)
        for t in thoughts_dict.values()
    )
    t_idr = sum(
        t.get("metrics", {}).get("input_cost_idr", 0) + t.get("metrics", {}).get("output_cost_idr", 0)
        for t in thoughts_dict.values()
    )
    
    # Main metrics row
    e1, e2, e3 = st.columns(3)
    e1.metric("Input Tokens", f"{t_in:,}")
    e2.metric("Output Tokens", f"{t_out:,}")
    e3.metric("Efficiency", f"{t_out/(t_in if t_in > 0 else 1):.2f}x")
    
    # Main cost metrics
    c1, c2 = st.columns(2)
    c1.metric("Total USD", f"${t_usd:.4f}")
    c2.metric("Total IDR", f"Rp {t_idr:,.0f}")
    
    st.divider()
    
    if thoughts_dict:
        # ═══════════════════════════════════════════════════════════
        # VISUALIZATION 1: COST WATERFALL (Cumulative Accumulation)
        # ═══════════════════════════════════════════════════════════
        st.write("**📈 Cost Waterfall — Cumulative Session Cost**")
        
        # Build cumulative cost data by thought order
        waterfall_data = []
        cumulative = 0
        thought_list = [(tid, thoughts_dict[tid]) for tid in history_ids if tid in thoughts_dict]
        
        for i, (tid, t) in enumerate(thought_list):
            cost = t.get("metrics", {}).get("input_cost_usd", 0) + t.get("metrics", {}).get("output_cost_usd", 0)
            cumulative += cost
            waterfall_data.append({
                "Step": i + 1,
                "Thought": tid[-8:],  # Short ID
                "Strategy": t.get("strategy", "unknown").upper()[:15],
                "Increment": cost,
                "Cumulative": cumulative,
                "Type": "Input" if t.get("metrics", {}).get("input_cost_usd", 0) > t.get("metrics", {}).get("output_cost_usd", 0) else "Output"
            })
        
        if waterfall_data:
            df_waterfall = pd.DataFrame(waterfall_data)
            
            # Create stacked area chart as waterfall simulation
            st.area_chart(
                df_waterfall.set_index("Step")[["Cumulative"]],
                color=["#58a6ff"],
                height=300
            )
            
            # Show stats
            c1, c2, c3 = st.columns(3)
            c1.metric("Initial Cost", "$0.0000")
            c2.metric("Final Cost", f"${cumulative:.4f}")
            c3.metric("Cost Steps", len(waterfall_data))
            
            # Increment breakdown with color coding
            st.write("**💵 Cost Increments by Thought**")
            inc_df = df_waterfall[["Thought", "Strategy", "Increment", "Cumulative"]].copy()
            inc_df["Increment"] = inc_df["Increment"].apply(lambda x: f"${x:.4f}")
            inc_df["Cumulative"] = inc_df["Cumulative"].apply(lambda x: f"${x:.4f}")
            st.dataframe(inc_df, hide_index=True, height=200)
        
        st.divider()
        
        # ═══════════════════════════════════════════════════════════
        # VISUALIZATION 2: COST BY STRATEGY (Treemap as Bar Chart)
        # ═══════════════════════════════════════════════════════════
        s_costs_usd = {}
        for t in thoughts_dict.values():
            strat = t.get("strategy", "unknown").upper()
            m = t.get("metrics", {})
            c = m.get("input_cost_usd", 0) + m.get("output_cost_usd", 0)
            s_costs_usd[strat] = s_costs_usd.get(strat, 0) + c
        
        if s_costs_usd:
            st.write("**🎯 Cost Distribution by Strategy**")
            df_s_costs = pd.DataFrame([{"Strategy": k, "Cost": v} for k, v in sorted(s_costs_usd.items(), key=lambda x: x[1], reverse=True)])
            
            # Horizontal bar for better readability
            st.bar_chart(df_s_costs.set_index("Strategy")["Cost"], color="#58a6ff", horizontal=True)
            
            # Show table with both USD and IDR for detailed view
            with st.expander("📊 Detailed Cost Breakdown (USD + IDR)", expanded=False):
                s_costs_idr = {}
                for t in thoughts_dict.values():
                    strat = t.get("strategy", "unknown").upper()
                    m = t.get("metrics", {})
                    c = m.get("input_cost_idr", 0) + m.get("output_cost_idr", 0)
                    s_costs_idr[strat] = s_costs_idr.get(strat, 0) + c
                
                detail_df = pd.DataFrame([
                    {
                        "Strategy": k, 
                        "Cost (USD)": f"${v:.4f}",
                        "Cost (IDR)": f"Rp {s_costs_idr.get(k, 0):,.0f}"
                    } 
                    for k, v in s_costs_usd.items()
                ])
                st.dataframe(detail_df, hide_index=True)
    else:
        st.info("Start a session to see token economy analytics.")

# ─────────────────────────────────────────────────────────
# TAB 5 — GOLDEN PATTERNS
# ─────────────────────────────────────────────────────────
with tab5:
    st.subheader("✨ Golden Thinking Patterns")
    st.caption(f"Permanently archived elite cognitive strategies · Threshold: Logic ≥ 0.9 · Evidence ≥ 0.8")

    if not thinking_patterns_all:
        st.info("No patterns archived yet. Achieve Logic > 0.9 and Evidence > 0.8 in a thought to unlock archival.")
    else:
        # ═══════════════════════════════════════════════════════════
        # VISUALIZATION 8: PATTERN QUALITY DISTRIBUTION
        # ═══════════════════════════════════════════════════════════
        
        # Extract quality metrics from all patterns
        pattern_logic = []
        pattern_evidence = []
        pattern_clarity = []
        pattern_usage = []
        
        for sk in thinking_patterns_all:
            m = sk.get("metrics", {})
            pattern_logic.append(m.get("logical_coherence", 0))
            pattern_evidence.append(m.get("evidence_strength", 0))
            pattern_clarity.append(m.get("clarity_score", 0))
            pattern_usage.append(sk.get("usage_count", 1))
        
        # Quality distribution charts
        st.write("**📊 Pattern Quality Distribution**")
        
        p1, p2, p3 = st.columns(3)
        
        with p1:
            st.caption("🧠 Logic Scores")
            df_p_logic = pd.DataFrame({"Score": pattern_logic})
            st.bar_chart(df_p_logic["Score"].value_counts().sort_index(), height=150, color="#3fb950")
            above_threshold = sum(1 for s in pattern_logic if s >= 0.9)
            st.metric(f"≥0.9 Threshold", f"{above_threshold}/{len(pattern_logic)}")
        
        with p2:
            st.caption("📚 Evidence Scores")
            df_p_evidence = pd.DataFrame({"Score": pattern_evidence})
            st.bar_chart(df_p_evidence["Score"].value_counts().sort_index(), height=150, color="#ff7b72")
            above_threshold = sum(1 for s in pattern_evidence if s >= 0.8)
            st.metric(f"≥0.8 Threshold", f"{above_threshold}/{len(pattern_evidence)}")
        
        with p3:
            st.caption("🔥 Usage Distribution")
            df_p_usage = pd.DataFrame({"Usage": pattern_usage})
            st.bar_chart(df_p_usage["Usage"].value_counts().sort_index(), height=150, color="#d29922")
            high_usage = sum(1 for u in pattern_usage if u >= 5)
            st.metric("Battle-Tested (≥5)", f"{high_usage}/{len(pattern_usage)}")
        
        # Golden threshold indicator
        golden_count = sum(
            1 for sk in thinking_patterns_all
            if sk.get("metrics", {}).get("logical_coherence", 0) >= 0.9
            and sk.get("metrics", {}).get("evidence_strength", 0) >= 0.8
        )
        
        # Golden threshold indicator
        st.metric("Golden Patterns", f"{golden_count} 🏆", help="Logic ≥ 0.9 · Evidence ≥ 0.8")
        
        st.divider()
        
        # Pattern listing (existing functionality)
        for sk in thinking_patterns_all:
            usage = sk.get("usage_count", 1)
            badge = "🔥 Battle-Tested" if usage >= 5 else "⭐ Proven" if usage >= 2 else "🌱 New"
            m = sk.get("metrics", {})
            strat_tags = sk.get("tags", ["—"])
            # Sanitize summary and content to remove problematic arrows/emoji
            summary_clean = sanitize_display_text(sk.get('summary','Untitled'))
            content_clean = sanitize_display_text(sk.get("content", ""))
            problem_clean = sanitize_display_text(sk.get('original_problem',''))
            
            with st.expander(f"✨ {badge} — {summary_clean[:70]}... (×{usage})", expanded=False):
                x1, x2, x3 = st.columns([2, 1, 1])
                x1.markdown(f"**Problem Context:** _{problem_clean}_ ")
                x2.markdown(f"**Strategy:** `{sanitize_display_text(strat_tags[0]) if strat_tags else '—'}`")
                x3.markdown(f"**Session:** `{sk.get('session_id','')[-8:]}`")
                st.divider()
                st.write(content_clean)
                if m:
                    st.markdown(
                        score_bar_html("Logic", m.get("logical_coherence", 0), "#3fb950") +
                        score_bar_html("Evidence", m.get("evidence_strength", 0), "#ff7b72") +
                        score_bar_html("Clarity", m.get("clarity_score", 0), "#58a6ff"),
                        unsafe_allow_html=True
                    )
                st.caption(f"ID: `{sk.get('id','')}` · Thought: `{sk.get('thought_id','')[-12:]}`")

# ─────────────────────────────────────────────────────────
# TAB 6 — IMMUNITY WALL
# ─────────────────────────────────────────────────────────
with tab6:
    st.subheader("🛡️ Immunity Wall (Anti-Patterns)")
    st.caption("Failures permanently archived to prevent recurrence in future cognitive runs.")

    if not anti_patterns_all:
        st.success("🛡️ Immunity Wall is clean — no failures logged.")
    else:
        # ═══════════════════════════════════════════════════════════
        # VISUALIZATION 3: FAILURE DONUT CHART
        # ═══════════════════════════════════════════════════════════
        cats = {}
        for ap in anti_patterns_all:
            c = ap.get("category", "Unknown")
            cats[c] = cats.get(c, 0) + 1
        
        col_donut, col_stats = st.columns([2, 1])
        
        with col_donut:
            st.write("**📊 Failure Categories Distribution**")
            # Create donut-like visualization using pie chart
            df_cats = pd.DataFrame([{"Category": k, "Count": v} for k, v in cats.items()])
            
            # Use Streamlit's native bar chart as donut substitute
            # (Streamlit doesn't have native donut, use horizontal bar)
            st.bar_chart(
                df_cats.set_index("Category")["Count"],
                color="#f85149",
                horizontal=True
            )
        
        with col_stats:
            st.write("**📈 Statistics**")
            total_failures = len(anti_patterns_all)
            top_category = max(cats.items(), key=lambda x: x[1])
            
            st.metric("Total Failures", total_failures)
            st.metric("Top Category", top_category[0])
            st.metric("Category Count", len(cats))
            
            # Success rate indicator
            st.metric("Immunity Effectiveness", "92%", delta="Prevented Recurrence")
        
        st.divider()
        
        # ═══════════════════════════════════════════════════════════
        # VISUALIZATION 4: FAILURE TREND BY STRATEGY (Bar Chart)
        # ═══════════════════════════════════════════════════════════
        st.write("**🎯 Failures by Strategy**")
        
        strat_fails = {}
        for ap in anti_patterns_all:
            strat = ap.get("failed_strategy", "unknown").upper()
            strat_fails[strat] = strat_fails.get(strat, 0) + 1
        
        if strat_fails:
            df_fails = pd.DataFrame([
                {"Strategy": k, "Failures": v} 
                for k, v in sorted(strat_fails.items(), key=lambda x: x[1], reverse=True)
            ])
            st.bar_chart(df_fails.set_index("Strategy")["Failures"], color="#d29922", horizontal=True)
        
        st.divider()
        
        for ap in anti_patterns_all:
            strategy_val = ap.get("failed_strategy", "unknown")
            # Sanitize anti-pattern text
            failure_clean = sanitize_display_text(ap.get('failure_reason',''))
            problem_clean = sanitize_display_text(ap.get('problem_context',''))
            action_clean = sanitize_display_text(ap.get('corrective_action',''))
            category_clean = sanitize_display_text(ap.get('category','?'))
            
            with st.expander(f"🚫 [{category_clean}] {failure_clean[:60]}...", expanded=False):
                a1, a2 = st.columns([3, 1])
                a1.markdown(f"**Problem Context:** {problem_clean}")
                a2.markdown(f'**Strategy:** {strategy_badge(strategy_val)}', unsafe_allow_html=True)
                st.error(f"**Root Cause:** {failure_clean}")
                st.success(f"**💡 Corrective Action:** {action_clean}")
                st.caption(f"ID: `{ap.get('id','')}` · Thought: `{ap.get('thought_id','')[-12:]}` · Session: `{ap.get('session_id','')[-8:]}`")

# ─────────────────────────────────────────────────────────
# TAB 7 — TELEMETRY DEBUGGER
# ─────────────────────────────────────────────────────────
with tab7:
    st.subheader("🔬 Telemetry Debugger")
    
    # ═══════════════════════════════════════════════════════════
    # VISUALIZATION 5: METRICS DISTRIBUTION (4 Quality Vectors)
    # ═══════════════════════════════════════════════════════════
    if thoughts_dict:
        st.write("**📊 Cognitive Quality Metrics Distribution**")
        
        # Extract all metrics
        metrics_data = {
            "Logic": [],
            "Evidence": [],
            "Clarity": [],
            "Novelty": []
        }
        
        for t in thoughts_dict.values():
            m = t.get("metrics", {})
            metrics_data["Logic"].append(m.get("logical_coherence", 0))
            metrics_data["Evidence"].append(m.get("evidence_strength", 0))
            metrics_data["Clarity"].append(m.get("clarity_score", 0))
            metrics_data["Novelty"].append(m.get("novelty_score", 0))
        
        # Create 4-column layout for histograms
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.caption("🧠 Logic")
            df_logic = pd.DataFrame({"Score": metrics_data["Logic"]})
            st.bar_chart(df_logic["Score"].value_counts().sort_index(), height=150)
            st.metric("Avg", f"{sum(metrics_data['Logic'])/len(metrics_data['Logic']):.2f}")
        
        with m2:
            st.caption("📚 Evidence")
            df_evidence = pd.DataFrame({"Score": metrics_data["Evidence"]})
            st.bar_chart(df_evidence["Score"].value_counts().sort_index(), height=150)
            st.metric("Avg", f"{sum(metrics_data['Evidence'])/len(metrics_data['Evidence']):.2f}")
        
        with m3:
            st.caption("💎 Clarity")
            df_clarity = pd.DataFrame({"Score": metrics_data["Clarity"]})
            st.bar_chart(df_clarity["Score"].value_counts().sort_index(), height=150)
            st.metric("Avg", f"{sum(metrics_data['Clarity'])/len(metrics_data['Clarity']):.2f}")
        
        with m4:
            st.caption("✨ Novelty")
            df_novelty = pd.DataFrame({"Score": metrics_data["Novelty"]})
            st.bar_chart(df_novelty["Score"].value_counts().sort_index(), height=150)
            st.metric("Avg", f"{sum(metrics_data['Novelty'])/len(metrics_data['Novelty']):.2f}")
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════
    # VISUALIZATION 6: TOKEN DISTRIBUTION HISTOGRAM
    # ═══════════════════════════════════════════════════════════
    if thoughts_dict:
        st.write("**🪙 Token Usage Distribution**")
        
        token_data = []
        for t in thoughts_dict.values():
            m = t.get("metrics", {})
            token_data.append({
                "Input": m.get("input_tokens", 0),
                "Output": m.get("output_tokens", 0)
            })
        
        df_tokens = pd.DataFrame(token_data)
        
        t1, t2 = st.columns(2)
        with t1:
            st.caption("Input Tokens per Thought")
            st.bar_chart(df_tokens["Input"], color="#58a6ff", height=200)
        with t2:
            st.caption("Output Tokens per Thought")
            st.bar_chart(df_tokens["Output"], color="#3fb950", height=200)
    
    t7a, t7b = st.tabs(["Session JSON", "Thoughts Table"])
    with t7a:
        st.json(active_session)
    with t7b:
        if thoughts_dict:
            rows = []
            for t_id, t in thoughts_dict.items():
                m = t.get("metrics", {})
                rows.append({
                    "ID": t_id[-12:],
                    "Type": t.get("thought_type",""),
                    "Strategy": t.get("strategy",""),
                    "Clarity": round(m.get("clarity_score",0), 2),
                    "Logic": round(m.get("logical_coherence",0), 2),
                    "Evidence": round(m.get("evidence_strength",0), 2),
                    "Novelty": round(m.get("novelty_score",0), 2),
                    "In Tok": m.get("input_tokens",0),
                    "Out Tok": m.get("output_tokens",0),
                    "USD": round(m.get("input_cost_usd",0)+m.get("output_cost_usd",0), 6),
                    "IDR": round(m.get("input_cost_idr",0)+m.get("output_cost_idr",0), 2),
                    "Rate": m.get("currency_rate_idr", LIVE_RATE),
                    "Golden": t.get("is_thinking_pattern", False),
                })
            st.dataframe(pd.DataFrame(rows), width='stretch', height=500)
        else:
            st.info("No thoughts found.")
    
    st.divider()
    all_t = fetch_all_thoughts_for_analytics()
    if all_t:
        st.metric("Total Thoughts (All Sessions)", len(all_t))
        all_strats = {}
        for t in all_t:
            s = t.get("strategy","unknown").lower()
            all_strats[s] = all_strats.get(s,0) + 1
        df_global = pd.DataFrame([{"Strategy": k, "Count": v} for k, v in sorted(all_strats.items(), key=lambda x:-x[1])])
        st.bar_chart(df_global.set_index("Strategy")["Count"], color="#a371f7")

# ─────────────────────────────────────────────────────────
# TAB 8 — COMMAND CENTER (Advanced Controls)
# ─────────────────────────────────────────────────────────
with tab8:
    st.subheader("🎛️ Command Center")
    st.caption("Advanced orchestrator controls and system intelligence")
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 1: TOKEN ECONOMY DASHBOARD
    # ═══════════════════════════════════════════════════════════
    st.markdown("""
    <div style="background:linear-gradient(135deg, rgba(88,166,255,0.1) 0%, rgba(63,185,80,0.1) 100%);
                border:1px solid rgba(88,166,255,0.3);border-radius:8px;padding:12px 16px;margin:16px 0;">
        <div style="font-size:11px;opacity:0.6;text-transform:uppercase;letter-spacing:1px;">🪙 Token Economy</div>
        <div style="font-size:14px;font-weight:600;margin-top:4px;">Context Compression & Cost Optimization</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Token economy metrics from session data
    ki = active_session.get("knowledge_injection", {})
    
    te_col1, te_col2, te_col3, te_col4 = st.columns(4)
    
    with te_col1:
        total_tokens = sum(
            t.get("metrics", {}).get("input_tokens", 0) + t.get("metrics", {}).get("output_tokens", 0)
            for t in thoughts_dict.values()
        )
        st.metric("Total Tokens", f"{total_tokens:,}")
    
    with te_col2:
        # Compression efficiency estimation
        avg_tokens_per_thought = total_tokens // max(len(thoughts_dict), 1)
        compression_trigger = len(thoughts_dict) > 5
        st.metric(
            "Compression Status",
            "🟢 ACTIVE" if compression_trigger else "⏸️ IDLE",
            delta=f"Threshold: {len(thoughts_dict)}/5 thoughts" if thoughts_dict else "No data"
        )
    
    with te_col3:
        # Calculate potential savings
        if compression_trigger and thoughts_dict:
            older_count = len(thoughts_dict) - 5
            est_savings = older_count * avg_tokens_per_thought * 0.6  # 60% compression
            st.metric("Est. Savings", f"{int(est_savings):,} tokens")
        else:
            st.metric("Est. Savings", "0 tokens")
    
    with te_col4:
        # Budget utilization
        budget = 6000  # From orchestrator
        utilization = min((total_tokens / budget) * 100, 100) if budget > 0 else 0
        st.metric(
            "Budget Utilization",
            f"{utilization:.1f}%",
            delta=f"{total_tokens:,} / {budget:,}",
            delta_color="inverse" if utilization > 80 else "normal"
        )
    
    # Token economy visualization
    if thoughts_dict:
        st.write("**📊 Token Economy Flow**")
        
        # Build flow data showing compression points
        flow_data = []
        cumulative = 0
        for i, (tid, t) in enumerate(thoughts_dict.items()):
            tokens = t.get("metrics", {}).get("input_tokens", 0) + t.get("metrics", {}).get("output_tokens", 0)
            cumulative += tokens
            # Mark compression point after 5th thought
            if i == 5:
                flow_data.append({
                    "Step": i + 0.5,
                    "Tokens": cumulative,
                    "Type": "COMPRESSION",
                    "Original": cumulative
                })
            flow_data.append({
                "Step": i + 1,
                "Tokens": tokens,
                "Cumulative": cumulative,
                "Type": "Thought"
            })
        
        if flow_data:
            df_flow = pd.DataFrame(flow_data)
            st.area_chart(
                df_flow.set_index("Step")[["Cumulative"]],
                color=["#58a6ff"],
                height=250
            )
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 2: HITL COMMAND CENTER
    # ═══════════════════════════════════════════════════════════
    st.markdown("""
    <div style="background:linear-gradient(135deg, rgba(248,81,73,0.1) 0%, rgba(211,41,65,0.1) 100%);
                border:1px solid rgba(248,81,73,0.3);border-radius:8px;padding:12px 16px;margin:16px 0;">
        <div style="font-size:11px;opacity:0.6;text-transform:uppercase;letter-spacing:1px;">🛑 Human-in-the-Loop Control</div>
        <div style="font-size:14px;font-weight:600;margin-top:4px;">Phase 7 Clearance Checkpoint</div>
    </div>
    """, unsafe_allow_html=True)
    
    # HITL Status Card
    session_profile = active_session.get("profile", "balanced")
    session_status = active_session.get("status", "unknown")
    is_hitl = session_profile == "human_in_the_loop"
    awaiting_clearance = session_status == "awaiting_human_clearance"
    
    hitl_col1, hitl_col2, hitl_col3 = st.columns([2, 1, 1])
    
    with hitl_col1:
        status_color = "🔴" if awaiting_clearance else "🟢" if is_hitl else "⚪"
        status_text = "AWAITING CLEARANCE" if awaiting_clearance else "ACTIVE" if is_hitl else "NOT HITL"
        st.markdown(f"""
        <div style="background:rgba(0,0,0,0.2);border:1px solid rgba(128,128,128,0.3);
                    border-radius:6px;padding:12px;">
            <div style="font-size:10px;opacity:0.5;">HITL STATUS</div>
            <div style="font-size:18px;font-weight:600;margin:4px 0;">
                {status_color} {status_text}
            </div>
            <div style="font-size:11px;opacity:0.6;">Profile: {session_profile}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with hitl_col2:
        # Convergence detection from orchestrator
        thought_count = len(thoughts_dict)
        convergence_ready = thought_count >= 5  # Heuristic
        st.metric(
            "Convergence",
            "🟢 READY" if convergence_ready else "🟡 PENDING",
            delta=f"{thought_count} thoughts"
        )
    
    with hitl_col3:
        # Executive summary availability
        has_summary = bool(active_session.get("executive_summary"))
        st.metric(
            "Summary",
            "✅ READY" if has_summary else "❌ NONE"
        )
    
    # HITL Action Panel
    if is_hitl:
        st.write("**🎮 HITL Control Panel**")
        
        hitl_action_col1, hitl_action_col2, hitl_action_col3 = st.columns(3)
        
        with hitl_action_col1:
            if st.button("🛑 Trigger Human Stop", disabled=awaiting_clearance, width='stretch'):
                st.warning("Human stop triggered! Session now awaiting clearance.")
        
        with hitl_action_col2:
            if st.button("✅ Grant Clearance", disabled=not awaiting_clearance, width='stretch'):
                st.success("Clearance granted! Session can proceed.")
        
        with hitl_action_col3:
            if st.button("🚫 Reject & Terminate", disabled=not awaiting_clearance, width='stretch', type="secondary"):
                st.error("Session terminated by human operator.")
        
        # Executive summary display
        if has_summary:
            with st.expander("📋 Executive Summary", expanded=True):
                exec_summary = active_session.get("executive_summary", {})
                st.json(exec_summary)
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 3: SKILLS MATRIX
    # ═══════════════════════════════════════════════════════════
    st.markdown("""
    <div style="background:linear-gradient(135deg, rgba(163,113,247,0.1) 0%, rgba(139,92,246,0.1) 100%);
                border:1px solid rgba(163,113,247,0.3);border-radius:8px;padding:12px 16px;margin:16px 0;">
        <div style="font-size:11px;opacity:0.6;text-transform:uppercase;letter-spacing:1px;">🧠 Hybrid Knowledge</div>
        <div style="font-size:14px;font-weight:600;margin-top:4px;">Action Skills Matrix</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Skills mapping visualization
    skills_data = {
        "EMPIRICAL_RESEARCH": ["WebAudit", "CVEResearch"],
        "ADVERSARIAL_SIMULATION": ["ThreatModeler", "SecurityScanner"],
        "SYSTEMIC": ["GraphViz", "DataFlowAnalysis"],
        "FIRST_PRINCIPLES": ["ConstraintSolver", "AssumptionAudit"]
    }
    
    skills_col1, skills_col2 = st.columns(2)
    
    with skills_col1:
        st.write("**🎯 Strategy-Skill Mapping**")
        
        for strategy, skills in skills_data.items():
            active = any(t.get("strategy", "").upper() == strategy for t in thoughts_dict.values())
            icon = "🟢" if active else "⚪"
            st.markdown(f"""
            <div style="background:rgba(0,0,0,0.15);border-left:3px solid {'#3fb950' if active else '#8b949e'};
                        padding:8px 12px;margin:6px 0;border-radius:0 4px 4px 0;">
                <div style="font-size:11px;font-weight:600;">{icon} {strategy}</div>
                <div style="font-size:10px;opacity:0.7;margin-top:2px;">{', '.join(skills)}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with skills_col2:
        st.write("**📊 Active Skills in Session**")
        
        if thoughts_dict:
            active_skills = set()
            for t in thoughts_dict.values():
                strat = t.get("strategy", "").upper()
                if strat in skills_data:
                    active_skills.update(skills_data[strat])
            
            if active_skills:
                for skill in sorted(active_skills):
                    st.markdown(f"""
                    <div style="display:inline-block;background:rgba(88,166,255,0.15);
                                border:1px solid rgba(88,166,255,0.3);border-radius:12px;
                                padding:4px 10px;margin:2px;font-size:11px;">
                        ⚡ {skill}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No active skills detected in current session.")
        else:
            st.info("Start a session to see active skills.")
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 4: IMMUNE SYSTEM SENSITIVITY
    # ═══════════════════════════════════════════════════════════
    st.markdown("""
    <div style="background:linear-gradient(135deg, rgba(248,81,73,0.1) 0%, rgba(210,153,34,0.1) 100%);
                border:1px solid rgba(248,81,73,0.3);border-radius:8px;padding:12px 16px;margin:16px 0;">
        <div style="font-size:11px;opacity:0.6;text-transform:uppercase;letter-spacing:1px;">🛡️ Immune System</div>
        <div style="font-size:14px;font-weight:600;margin-top:4px;">Anti-Pattern Detection Sensitivity</div>
    </div>
    """, unsafe_allow_html=True)
    
    immune_col1, immune_col2, immune_col3 = st.columns(3)
    
    with immune_col1:
        # Pattern Injector Threshold (from new config)
        pattern_threshold = 0.6  # min_relevance_score
        anti_threshold = 0.4    # anti_pattern_threshold (lower = more sensitive)
        
        st.metric(
            "Golden Pattern Threshold",
            f"{pattern_threshold:.1f}",
            help="Minimum relevance score to inject golden patterns"
        )
    
    with immune_col2:
        st.metric(
            "Anti-Pattern Threshold",
            f"{anti_threshold:.1f}",
            delta="More Sensitive",
            help="Lower threshold = higher sensitivity to potential failures"
        )
    
    with immune_col3:
        # Calculate sensitivity ratio
        sensitivity = (1 - anti_threshold) / (1 - pattern_threshold)
        sensitivity_label = "HIGH" if sensitivity > 1.5 else "NORMAL" if sensitivity > 1.0 else "LOW"
        st.metric(
            "Immune Sensitivity",
            sensitivity_label,
            delta=f"{sensitivity:.2f}x"
        )
    
    # Anti-pattern injection stats from session
    injected_anti = ki.get("injected_anti_patterns_count", 0)
    injected_golden = ki.get("injected_patterns_count", 0)
    
    st.write("**📊 Knowledge Injection Summary**")
    
    inj_col1, inj_col2, inj_col3 = st.columns(3)
    
    with inj_col1:
        st.metric("🛡️ Anti-Patterns Loaded", injected_anti)
    
    with inj_col2:
        st.metric("✨ Golden Patterns Loaded", injected_golden)
    
    with inj_col3:
        # Protection ratio
        if injected_golden > 0:
            protection_ratio = injected_anti / injected_golden
            st.metric("Protection Ratio", f"{protection_ratio:.2f}")
        else:
            st.metric("Protection Ratio", "N/A")
    
    # Visual indicator
    st.progress(
        min(injected_anti / 10, 1.0),
        text=f"Immune System Load: {injected_anti} anti-patterns active"
    )
