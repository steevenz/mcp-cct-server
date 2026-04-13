# 🧠 CCT MCP Server: The Cognitive OS for Elite Architects

[](https://github.com/steevenz/mcp-cct-server)
[](https://sqlite.org)
[](https://github.com/steevenz/mcp-cct-server)
[](https://github.com/steevenz/mcp-cct-server)

> "Most AI models are just fast talkers. This server turns them into Deep Thinkers."

## 🚀 What is this?

**CCT (Creative Critical Thinking) MCP Server** isn't just another set of tools; it's a **Cognitive Exoskeleton** for LLMs. While other MCP servers focus on giving AI *access* (reading files, searching the web), CCT focuses on giving AI **Reasoning Structure**.

It forces the LLM to stop giving "shallow-first" answers and instead utilize a high-fidelity, multi-layered thinking pipeline—persisting every single neuron-fire into a SQLite database.

### ⚡ How is this different from other MCP Servers?

  * **Persistent Cognition:** Unlike stateless chats, CCT remembers *why* a decision was made 3 months ago via its SQLite-backed `MemoryManager`.
  * **Evolutionary Memory:** Automatically archives high-scoring logic into **Thinking Patterns** (Golden Skills) and logs failures as **Anti-Patterns** to prevent recursive mistakes.
  * **Planning Orchestration:** Native support for advanced reasoning patterns including ReAct, ReWOO, Tree of Thoughts (ToT), and Plan-and-Execute.
  * **Standardized Engineering SOP:** Enforces an **Engineering Deconstruction** phase (Eval-First + 15-Minute Rule) before any implementation begins.
  * **Self-Debugging Intelligence:** Built-in protocol to detect tool loops and task drift, switching to an Introspection mode to diagnose and recover before burning tokens.
  * **Socratic Gate (Brainstorming):** Mandatory discovery phase for vague tasks. Enforces 3 critical questions before any code is written.
  * **Four-Voice Council:** Multi-persona decision architecture (Architect, Skeptic, Pragmatist, Critic) for high-stakes trade-offs.
  * **Evolutionary Archive (Learning):** Automatic session post-mortems that extract "Instincts" and promote them to durable Thinking Patterns.

## 🎯 The Goal

To bridge the gap between **AI Speed** and **Human Criticality**. We follow the **C\&C Framework**:

1.  **Creative:** Generative exploration of unconventional solutions.
2.  **Critical:** Brutal stress-testing and architectural auditing.
3.  **Empirical:** Real-world grounding via data research to kill hallucination.

## ⚙️ Execution Paradigms (Dual Modes)

CCT is built for both velocity and extreme safety. The execution mode is enforced during the final clearance phase:

  * **🤖 Autonomous Mode:** The AI acts as the "Digital Architect". It audits its own reasoning against a 25-year veteran persona standard. If the `logic_score` \> 0.95, it grants itself clearance and writes the implementation immediately. Perfect for velocity.
  * **🛑 Human-in-the-Loop (Human Stop):** For mission-critical infrastructure (e.g., Security, EDR). The AI acts as an advisory War Room. It builds the architecture, stress-tests it, but triggers a **Hard Stop** to present an Executive Summary. It will not write code until you grant explicit authorization.

## 🔄 The Pipeline: How it Thinks

When a Mission is dispatched, the AI follows this strict SOP:

1.  **Phase 0 (Meta-Cognitive Routing):** AI dynamically selects its thinking pipeline (DEBUG, ARCH, FEAT). It injects past *Thinking Patterns* and *Anti-Patterns*.
2.  **Phase 1 (Engineering Deconstruction):** Mandatory SOP. Define success criteria (Eval-First) and break work into 15-minute atomized units.
3.  **Phase 2 (Planning & Pattern Execution):** Apply the optimal reasoning model (ReAct for tools, ToT for complexity, CoT for logic).
4.  **Phase 3 (Empirical Grounding):** Search the web. Validate facts. Ground the mission in real-world data.
5.  **Phase 4 (The Crucible):** Run the Actor-Critic debate to find vulnerabilities and edge cases.
6.  **Phase 5 (Future-Proofing):** Project technical debt and scalability via Temporal Horizon.
7.  **Phase 6 (Final Execution):** Output the battle-tested code/architecture under Autonomous or HITL protocols.

## �️ Production Features

### Rate Limiting (New in v2026.04)

CCT includes enterprise-grade rate limiting to prevent abuse and ensure fair resource allocation:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `cct_think_step` | 120 requests | 60 seconds |
| `actor_critic_dialog` | 30 requests | 60 seconds |

**Response Format (when rate limited):**
```json
{
  "status": "error",
  "code": 429,
  "error": "Rate limit exceeded",
  "retry_after": 45,
  "message": "Too many requests. Retry after 45 seconds."
}
```

### Health Check Endpoint

Monitor system health for Docker/Kubernetes deployments:

```bash
# Call health check via MCP tool
health_check()
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-13T05:15:00+00:00",
  "version": "2026.04.12",
  "services": {
    "database": "healthy",
    "memory_manager": "healthy"
  },
  "metrics": {
    "active_sessions": 5,
    "total_thoughts": 127,
    "response_time_ms": 12.34,
    "max_sessions": 128,
    "max_thoughts_per_session": 200
  }
}
```

**Docker Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.post('http://localhost:8000/health_check')" || exit 1
```

### 🧠 Cognitive Strategies & Planning

CCT supports specialized reasoning patterns for different classes of complexity:

| Strategy | Usage | Best For |
|----------|-------|----------|
| `REACT` | Reasoning-and-Acting loop | Tool-intensive discovery |
| `TREE_OF_THOUGHTS` | Branching exploration | Complex multi-path problems |
| `REWOO` | Plan-First, Execute-Parallel | High-latency, multi-step tasks |
| `PLAN_AND_EXECUTE` | Structured task sequencing | Large engineering implementations |
| `CHAIN_OF_THOUGHT` | Step-by-step linear logic | Deep mathematical or logic proofs |
| `ENGINEERING_DECONSTRUCTION` | Mandatory Engineering SOP | Breaking down `FEAT` and `ARCH` tasks |
| `SELF_DEBUGGING` | Fail-Safe Introspection | Recovering from loops, drift, and burn |

---

### 🚦 Model Routing (Operational Intelligence)

Optimal engineering requires matching the task to the right "intelligence tier":

*   **⚡ Haiku**: Classification, simple boilerplate, and localized documentation.
*   **🧠 Sonnet**: Standard feature implementation and complex logic.
*   **🏛️ Opus**: Root-cause analysis, architecture design, and high-impact invariants.

---


## �🖥️ Mission Control Dashboard

We don't do "Black Box" AI. The **Streamlit Dashboard** is your proactive Dispatch Hub.

  * **Proactive Dispatch:** Launch new missions directly from the UI. It generates a `cct-dispatch.md` signal for your IDE.
  * **Tree of Thought:** A real-time visualization of how the AI is branching and contradicting its own ideas.
  * **Architectural Ledger:** A searchable history of every architectural debate, highlighting your archived *Thinking Patterns*.

-----

## 🛠️ Installation & Setup

Get the engine running locally in minutes.

```bash
# 1. Clone the repository
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server

# 2. Setup Virtual Environment (Highly Recommended)
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Initialize Database & Launch Dashboard
streamlit run dashboard.py
```

-----

## 🔌 IDE Integration (MCP Setup)

CCT is agnostic and works with almost all MCP-supported AI IDEs (Cursor, Trae AI, Windsurf, Claude Desktop).

We recommend naming the server **`cct-cognitive-os`** in your configuration to clearly distinguish it from standard utility servers.

### The Universal JSON Configuration

For IDEs that use a raw JSON configuration (like **Claude Desktop** via `claude_desktop_config.json`, or **Windsurf**), append this block to your `mcpServers` object.

*(**Note:** Replace `ABSOLUTE_PATH_TO_REPO` with the actual path on your machine, e.g., `C:/Users/steevenz/MCP/mcp-cct-server`)*:

```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "command": "python",
      "args": [
        "-m",
        "src.main"
      ],
      "env": {
        "PYTHONPATH": "ABSOLUTE_PATH_TO_REPO"
      }
    }
  }
}
```

### Setup for Cursor / Trae AI (GUI)

If your IDE uses a GUI for MCP configuration:

1.  Navigate to **Settings \> Features \> MCP Servers** (or equivalent MCP tab).
2.  Click **+ Add New MCP Server**.
3.  Fill in the details:
      * **Name:** `cct-cognitive-server`
      * **Type:** `command`
      * **Command:** `ABSOLUTE_PATH_TO_REPO/venv/Scripts/python -m src.main` *(Use the python executable inside your venv to ensure dependencies are loaded)*.
4.  Save and ensure the status shows as **🟢 Connected**.

### Final Step: Inject the Laws of Physics

For the LLM to know *how* to use the server, you must provide it with the System Prompt. We use a universal **`.iderules`** file in the project root to ensure behavioral alignment across all AI IDEs (Cursor, Windsurf, Trae, etc.).

```bash
# Copy the global rules to your project root
cp docs/rules/system-prompt.md .iderules
```

Check the [System Prompt Deployment Guide](docs/guides/how-to-system-prompt.md) for more details.

-----

*Created by Steeven Andrian — Senior Systems Architect.*
*Built for those who believe AI should be a Co-Pilot, not an Autopilot.*