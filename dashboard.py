import sqlite3
import json
import streamlit as st
import pandas as pd

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="CCT Command Center", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# DATABASE ADAPTER
# ==========================================
DB_PATH = "cct_memory.db"

@st.cache_data(ttl=2) # Cache data for 2 seconds to allow near real-time updates
def fetch_sessions():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, data FROM sessions ORDER BY rowid DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"session_id": r[0], "data": json.loads(r[1])} for r in rows]
    except Exception as e:
        return []

@st.cache_data(ttl=2)
def fetch_thoughts(session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM thoughts WHERE session_id = ?", (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        thoughts_dict = {json.loads(r[0])["id"]: json.loads(r[0]) for r in rows}
        return thoughts_dict
    except Exception as e:
        return {}

@st.cache_data(ttl=5)
def fetch_thinking_patterns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM thinking_patterns ORDER BY rowid DESC")
        rows = cursor.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    except Exception as e:
        return []
@st.cache_data(ttl=5)
def fetch_anti_patterns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM anti_patterns ORDER BY rowid DESC")
        rows = cursor.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    except Exception as e:
        return []

# ==========================================
# SIDEBAR: SESSION NAVIGATOR
# ==========================================
st.sidebar.title("🧠 CCT Sessions")

# --- MISSION CONTROL ---
with st.sidebar.expander("🚀 Launch New Mission", expanded=False):
    st.markdown("Dispatch a new architectural objective to the CCT Agent.")
    new_problem = st.text_area("Problem Statement:", placeholder="Describe the goal or issue to solve...", height=100)
    
    selected_persona = st.selectbox(
        "AI Persona / Lens:", 
        ["Principal Architect", "Cybersecurity Specialist", "Performance Engineer", "System Generalist"]
    )
    selected_mode = st.radio("Operating Mode:", ["Human-in-the-Loop", "Autonomous Mode"])
    selected_profile = st.selectbox("Thinking Profile:", ["balanced", "critical_first", "creative_first", "deep_recursive"])

    role_mapping = {
        "Principal Architect": "Principal Systems Architect",
        "Cybersecurity Specialist": "Senior Cybersecurity EDR Specialist",
        "Performance Engineer": "High-Performance Systems Engineer",
        "System Generalist": "Senior Full-Stack Engineer"
    }

    critic_mapping = {
        "Principal Architect": "Legacy Code Auditor",
        "Cybersecurity Specialist": "Zero-Day Threat Actor",
        "Performance Engineer": "Memory Leak & Bottleneck Auditor",
        "System Generalist": "Enterprise Architecture Reviewer"
    }
    
    if st.button("Generate Dispatch Signal", use_container_width=True):
        if not new_problem.strip():
            st.error("Problem statement cannot be empty.")
        else:
            dispatch_content = f"""# 🧠 CCT Mission Briefing: {selected_persona}

You are operating as an elite {role_mapping[selected_persona]} powered by the CCT MCP Server. 
Current Mode: **{selected_mode}**

## 🎯 Core Directives
1. **Empirical Grounding First:** Before theorizing, you MUST gather evidence. No "lazy" internal knowledge for critical technical data.
2. **Autonomous Gatekeeping:** If in Autonomous Mode, you must simulate the 25-year veteran persona to approve your own work.
3. **No Blind Coding:** Architecture design is a prerequisite for implementation.

## 🔄 The Empirical-CCT Pipeline (SOP)

### Phase 1: Mission Initiation
* **Action:** Call `start_cct_session` with profile `{selected_profile}`.
* **Problem Statement:** {new_problem}

### Phase 1.5: Empirical Research (Scientific Basis)
* **Action:** Identify if the problem statement requires external benchmarks, CVEs, or modern documentation.
* **Tactic:** Use `@Web` or Search tools. Record findings via `cct_think_step` using `strategy: empirical_research` and `thought_type: observation`.
* **Requirement:** Every claim in later phases must cite these observations in its `tags`.

### Phase 2: Deconstruction & First Principles
* **Action:** Use `first_principles` to break the research data into fundamental truths.

### Phase 3: The Crucible (Stress-Testing)
* **Action:** Call `actor_critic_dialog` with persona "{critic_mapping[selected_persona]}". 
* **Tactic:** Ruthlessly attack the proposed architecture based on the empirical data found in Phase 1.5.

### Phase 4: Future-Proofing (Temporal Horizon)
* **Action:** Call `temporal_horizon_projection`. Project across NOW, NEXT, and LATER scales.

### Phase 6: Quality Audit
* **Action:** Call `analyze_session`. If `consistency_score` < 0.8, loop back to Phase 2.

### Phase 6.5: Clearance (FORK)
* **[HUMAN-IN-THE-LOOP]:** STOP. Present the summary and ask: *"Do you approve this empirical architecture, or should we pivot?"*
* **[AUTONOMOUS]:** Adopt the persona of a veteran {role_mapping[selected_persona]} (25+ years exp). Ask: *"Is this practically scalable and secure?"* Grant yourself clearance only if it meets elite standards.

### Phase 7: Final Execution
* **Action:** Write the code and implementation details only after Phase 6.5 clearance.
"""
            with open("CCT_DISPATCH.md", "w", encoding="utf-8") as f:
                f.write(dispatch_content)
            st.success("✅ **Dispatch Created!**")
            st.info("In Cursor/Claude, type: `@CCT_DISPATCH.md Please execute this mission.`")

st.sidebar.markdown("---")

sessions = fetch_sessions()

if not sessions:
    st.sidebar.warning("No sessions found in SQLite database.")
    st.stop()

# Format session list for selectbox
session_options = {s["session_id"]: f"{s['data']['problem_statement'][:40]}..." for s in sessions}
selected_session_id = st.sidebar.selectbox(
    "Select Architecture Session:", 
    options=list(session_options.keys()), 
    format_func=lambda x: session_options[x]
)

# Load selected session data
active_session = next(s["data"] for s in sessions if s["session_id"] == selected_session_id)
thoughts_dict = fetch_thoughts(selected_session_id)
history_ids = active_session.get("history_ids", [])

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Profile:** `{active_session.get('profile', 'unknown')}`")
st.sidebar.markdown(f"**Total Steps:** {len(history_ids)} / {active_session.get('estimated_total_thoughts', 0)}")

# --- BUDGET MONITOR & EFFICIENCY ---
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Budget Monitor")

total_tokens = active_session.get("total_prompt_tokens", 0) + active_session.get("total_completion_tokens", 0)
total_cost = active_session.get("total_cost_usd", 0.0)
avg_cost = total_cost / len(history_ids) if history_ids else 0.0
model_name = active_session.get("model_id", "claude-3-5-sonnet").split("-")[0].upper()

col_a, col_b = st.sidebar.columns(2)
col_a.metric("Total Cost", f"${total_cost:.4f}")
col_b.metric("Avg/Step", f"${avg_cost:.4f}")

st.sidebar.caption(f"Model Stack: `{model_name}` | Tokens: `{total_tokens:,}`")

st.sidebar.subheader("🎯 Evolutionary Intelligence")

# 1. GPA Calculation (Composite)
# GPA = (Consistency * 1.6) + (SkillReuse * 1.6) + (Efficiency * 0.8)
consistency = active_session.get("consistency_score", 0.0)
thinking_patterns = fetch_thinking_patterns()
total_pattern_usage = sum(sk.get('usage_count', 1) for sk in thinking_patterns)
reuse_rate = (total_pattern_usage / (len(thinking_patterns) + 1)) if thinking_patterns else 0.0
norm_reuse = min(reuse_rate / 5.0, 1.0) # Normalized: 1.0 at 5x avg reuse

total_tokens = active_session.get("total_prompt_tokens", 0) + active_session.get("total_completion_tokens", 0)
efficiency = (1.0 - (total_tokens / 1000000)) if total_tokens > 0 else 1.0 # Token cost penalty
norm_efficiency = max(0.0, min(1.0, efficiency))

gpa = (consistency * 1.6) + (norm_reuse * 1.6) + (norm_efficiency * 0.8)
st.sidebar.metric("Architectural GPA", f"{gpa:.2f} / 4.0")

# 2. Evolutionary Stats
col1, col2 = st.sidebar.columns(2)
anti_patterns = fetch_anti_patterns()
col1.metric("Pattern Recycling", f"{total_pattern_usage}x")
col2.metric("Immunity Depth", f"{len(anti_patterns)} Failures")

st.sidebar.caption("System evolves with every pattern archived and failure logged.")

# ==========================================
# MAIN DASHBOARD AREA
# ==========================================
st.title("Architectural Command Center")
st.info(f"**Problem Statement:** {active_session.get('problem_statement')}")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📜 Architectural Ledger", 
    "🕸️ Tree of Thought", 
    "✨ Thinking Patterns", 
    "🛡️ Anti-Patterns",
    "📊 Raw Telemetry"
])

# --- TAB 1: ARCHITECTURAL LEDGER ---
with tab1:
    st.markdown("### Chronological Thought Process")
    if not history_ids:
        st.write("No thoughts recorded yet.")
        
    for idx, t_id in enumerate(history_ids):
        thought = thoughts_dict.get(t_id)
        if not thought:
            continue
            
        # Get strategy (enum value)
        strategy = thought.get("strategy", "UNKNOWN").upper()
        content = thought.get("content", "")
        
        # Determine UI color based on strategy
        if strategy in ["CRITICAL", "ACTOR_CRITIC_LOOP", "actor_critic_loop"]:
            icon = "⚔️"
        elif strategy in ["SYNTHESIS", "INTEGRATIVE", "SYSTEMIC", "synthesis", "systemic"]:
            icon = "🏗️"
        elif strategy in ["LATERAL", "UNCONVENTIONAL_PIVOT", "lateral", "unconventional_pivot"]:
            icon = "⚡"
        elif strategy in ["TEMPORAL", "LONG_TERM_HORIZON", "temporal", "long_term_horizon"]:
            icon = "🔮"
        else:
            icon = "📝"

        with st.chat_message("ai", avatar=icon):
            header_suffix = " 🏆 GOLDEN PATTERN" if thought.get("is_thinking_pattern") else ""
            st.markdown(f"**Step {idx+1} | {strategy}** `({t_id})` {header_suffix}")
            st.write(content)
            
            # --- COGNITIVE SCORES (New) ---
            metrics = thought.get("metrics", {})
            if metrics:
                c1, c2, c3, c4 = st.columns(4)
                c1.caption(f"✨ Clarity: {metrics.get('clarity_score', 0):.2f}")
                c2.caption(f"🧠 Logic: {metrics.get('logical_coherence', 0):.2f}")
                c3.caption(f"🌱 Novelty: {metrics.get('novelty_score', 0):.2f}")
                c4.caption(f"🔍 Evidence: {metrics.get('evidence_strength', 0):.2f}")
            
            # Show relations if any
            contradicts = thought.get("contradicts", [])
            builds_on = thought.get("builds_on", [])
            if contradicts:
                st.caption(f"🚨 *Contradicts/Attacks:* `{', '.join(contradicts)}`")
            if builds_on:
                st.caption(f"🔗 *Builds upon:* `{', '.join(builds_on)}`")

# --- TAB 2: TREE OF THOUGHT VISUALIZER ---
with tab2:
    st.markdown("### Cognitive Graph (Relationships)")
    
    # We construct a Graphviz DOT string dynamically
    dot_graph = "digraph CCT {\n"
    dot_graph += '  node [shape=box, style=rounded, fontname="Helvetica"];\n'
    dot_graph += '  rankdir=TB;\n' # Top to Bottom
    
    for t_id, thought in thoughts_dict.items():
        # Handle strategy case consistency
        strategy = thought.get("strategy", "").upper()
        label = f"{strategy}\\n{t_id[-6:]}"
        
        # Node styling
        color = "lightblue"
        if strategy in ["CRITICAL", "ACTOR_CRITIC_LOOP"]: color = "lightcoral"
        elif strategy in ["SYNTHESIS", "INTEGRATIVE"]: color = "lightgreen"
        elif strategy in ["LATERAL", "UNCONVENTIONAL_PIVOT"]: color = "gold"
        
        dot_graph += f'  "{t_id}" [label="{label}", style="filled,rounded", fillcolor="{color}"];\n'
        
        # Edges (Parent to Child)
        parent_id = thought.get("parent_id")
        if parent_id and parent_id in thoughts_dict:
            dot_graph += f'  "{parent_id}" -> "{t_id}" [color="gray50"];\n'
            
        # Contradiction Edges (Red dotted)
        for target in thought.get("contradicts", []):
            if target in thoughts_dict:
                dot_graph += f'  "{t_id}" -> "{target}" [color="red", style="dotted", constraint=false];\n'
                
    dot_graph += "}"
    
    try:
        st.graphviz_chart(dot_graph)
        st.caption("🟦 Standard | 🟩 Synthesis | 🟥 Critical Attack | 🟨 Lateral Pivot")
        st.caption("➔ *Solid line:* Sequential/Parent | ⇢ *Red dotted line:* Contradiction/Attack")
    except Exception as e:
        st.error("Graphviz is not installed on your system. Tree visualization requires it.")

# --- TAB 3: THINKING PATTERNS REPOSITORY ---
with tab3:
    st.markdown("### 🏆 Global Thinking Patterns Repository")
    st.caption("Permanent archive of elite cognitive patterns identified across missions.")
    
    thinking_patterns = fetch_thinking_patterns()
    if not thinking_patterns:
        st.info("No Thinking Patterns archived yet. Achieve Logic > 0.9 and Evidence > 0.8 to archive a pattern.")
    else:
        for sk in thinking_patterns:
            usage = sk.get('usage_count', 1)
            usage_badge = "🔥 Battle-Tested" if usage > 5 else "🌱 New Pattern"
            with st.expander(f"✨ {sk.get('summary', 'Untitled Pattern')[:70]}... ({usage_badge})", expanded=False):
                st.markdown(f"**Pattern ID:** `{sk.get('id')}` | **Usage Count:** `{usage}`")
                st.markdown(f"**Strategy:** `{sk.get('tags', [''])[0]}`")
                st.markdown(f"**Problem Origin:** {sk.get('original_problem')}")
                st.markdown("---")
                st.write(sk.get('content'))
                metrics = sk.get('metrics', {})
                st.caption(f"Logic: {metrics.get('logical_coherence', 0):.2%} | Evidence: {metrics.get('evidence_strength', 0):.2%}")

# --- TAB 4: ANTI-PATTERNS (Immunity Wall) ---
with tab4:
    st.markdown("### 🚫 Global Anti-Pattern Library")
    st.caption("Active Guardrails. Failures archived to prevent regression in future cognitive runs.")
    
    if not anti_patterns:
        st.info("The Immunity Wall is empty. No terminal failures logged yet.")
    else:
        for ap in anti_patterns:
            with st.expander(f"🚫 {ap.get('category')} - {ap.get('failure_reason')[:50]}...", expanded=True):
                c1, c2 = st.columns([2, 1])
                c1.markdown(f"**Problem Context:** {ap.get('problem_context')}")
                c2.markdown(f"**Failed Strategy:** `{ap.get('failed_strategy')}`")
                
                st.error(f"**Failure Reason:** {ap.get('failure_reason')}")
                st.success(f"**💡 Required Correction:** {ap.get('corrective_action')}")
                st.caption(f"Failure ID: `{ap.get('id')}` | Linked Thought: `{ap.get('thought_id')}`")

# --- TAB 5: RAW TELEMETRY ---
with tab5:
    st.markdown("### State Debugger")
    st.json(active_session)
    
    st.markdown("### Thoughts Metadata")
    # Convert dict to pandas dataframe for a clean table view
    if thoughts_dict:
        df = pd.DataFrame(list(thoughts_dict.values()))
        # Select only relevant columns to avoid clutter
        cols_to_show = ["id", "thought_type", "strategy", "parent_id"]
        available_cols = [c for c in cols_to_show if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
