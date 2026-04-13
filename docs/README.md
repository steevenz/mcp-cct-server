# CCT MCP Server: Autonomous Cognitive OS

The **Creative Critical Thinking (CCT) MCP Server** is an advanced reasoning engine that transforms standard LLMs into self-improving Systems Architects. Built on Python and SQLite, it enforces dynamic cognitive pipelines, empirical research grounding, and evolutionary memory (Thinking Patterns & Anti-Patterns) to solve complex architectural and coding challenges without hallucination.

-----

## 📋 Prerequisites

  * **Python 3.10+**
  * An MCP-compatible AI IDE (e.g., **Cursor**, **Trae AI**, or Windsurf)
  * *Optional but recommended:* Samsung DeX environment or a multi-monitor setup for side-by-side IDE and Dashboard execution.

-----

## 🚀 Quick Start & Installation

### 1\. Clone & Setup Environment

```bash
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install core dependencies
pip install -r requirements.txt
```

### 2\. Configure the MCP in your IDE

Add the CCT server to your IDE's MCP configuration settings.

**For Cursor (in `Settings > Features > MCP`):**

  * **Name:** `CCT-Server`
  * **Type:** `command`
  * **Command:** `python -m src.main` (or the exact path to your MCP entry point).

### 3\. Apply the Global Rules

Copy the provided autonomous system instructions to your project root.

```bash
cp docs/rules/system-prompt.md .cursorrules
```

### 4\. Launch the Mission Control Dashboard

In a separate terminal, launch the Streamlit interface to monitor the AI's cognitive tree in real-time:

```bash
streamlit run dashboard.py
```

-----

## 📂 Repository Structure

```text
mcp-cct-server/
├── src/
│   ├── core/               # Domain models, Enums, and Pydantic schemas
│   ├── engines/            
│   │   ├── memory/         # SQLite Manager, PatternArchiver
│   │   ├── sequential/     # Sequential step processing
│   │   └── orchestrator.py # Dynamic pipeline routing & execution
│   ├── analysis/           # ScoringEngine (Clarity, Logic, Novelty, Evidence)
│   └── utils/              # PipelineSelector, Skills Loader, Economy tools
├── docs/
│   ├── rules/              # SOPs, System Prompts, Pipeline definitions
│   └── context-tree/       # Auto-generated Markdown exports
│       ├── Thinking-Patterns/  # Archived Golden Skills (e.g., GS_91ddde72.md)
│       └── Anti-Patterns/      # Logged failures and corrective actions
├── tests/                  # Unit and integration tests
├── dashboard.py            # Streamlit real-time telemetry UI
├── cct_memory.db           # SQLite database (Auto-generated on first run)
├── cct-dispatch.md         # Dynamic mission briefing template
├── requirements.txt
└── README.md
```

-----

## 🕹️ Operational Workflow

### The "Dispatch to Execution" Loop

1.  **Generate Mission:** Open `http://localhost:8501` (Dashboard). Define your problem statement (e.g., *"Design an event-driven microservices architecture"*).
2.  **Dispatch:** Save the generated mission briefing to `cct-dispatch.md` in your project root.
3.  **Trigger AI:** In your IDE chat, simply type:
    > *"Execute mission @CCT\_DISPATCH.md autonomously."*
4.  **Monitor:** Watch the Dashboard as the AI dynamically selects its pipeline, queries the SQLite DB for past *Thinking Patterns*, conducts empirical research, and prunes inefficient cognitive branches.
5.  **Review:** Once the AI hits the `Logic > 0.95` threshold, it will automatically converge, grant itself clearance, and output the final code/architecture.

-----

## 🧠 Memory Management (Evolutionary Layer)

  * **Thinking Patterns (Internal Wisdom):** If a thought step scores highly across logic and evidence, it is automatically archived into the database and exported to `docs/context-tree/thinking-patterns/` for future reuse.
  * **Anti-Patterns (Immune System):** Avoids historical traps by injecting `corrective_action` directives during Phase 0 if a similar failure context is detected.
  * **Action Skills (External Tools):** Extend capabilities dynamically via `src/utils/skills_loader.py` to fetch executable tools from external repositories.

-----

**Architect:** Steeven Andrian (Creator of O2System)
**License:** Proprietary / Internal Use