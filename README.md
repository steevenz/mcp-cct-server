# 🧠 CCT MCP Server: The Cognitive OS for Elite Architects

[![System: Critical & Creative](https://img.shields.io/badge/Framework-C%26C-FF4B4B?style=for-the-badge)](https://github.com/steevenz/mcp-cct-server)
[![Memory: SQLite Persistent](https://img.shields.io/badge/Memory-SQLite-003B57?style=for-the-badge)](https://sqlite.org)
[![Engine: Hybrid Reasoning](https://img.shields.io/badge/Engine-Multi--Strategy-brightgreen?style=for-the-badge)](https://github.com/steevenz/mcp-cct-server)

> "Most AI models are just fast talkers. This server turns them into Deep Thinkers."

## 🚀 What is this?
**CCT (Creative Critical Thinking) MCP Server** isn't just another set of tools; it's a **Cognitive Exoskeleton** for LLMs. While other MCP servers focus on giving AI *access* (reading files, searching web), CCT focuses on giving AI **Reasoning Structure**.

It forces the LLM to stop giving "shallow-first" answers and instead utilize a high-fidelity, multi-layered thinking pipeline—persisting every single neuron-fire into a SQLite database.

### ⚡ How is this different from other MCP Servers?
* **Persistent Cognition:** Unlike stateless chats, CCT remembers *why* a decision was made 3 months ago via its SQLite-backed `MemoryManager`.
* **Strategy Enforcer:** It's not a suggestion; it's a protocol. The AI must follow specific cognitive primitives (First Principles, Abductive, etc.) before writing a single line of code.
* **Anti-Hallucination Backbone:** With our `SequentialEngine`, the server tracks the "state of thought," making it nearly impossible for the AI to lose the plot in complex architectures.

## 🎯 The Goal
To bridge the gap between **AI Speed** and **Human Criticality**. We follow the **C&C Framework**:
1.  **Creative:** Generative exploration of unconventional solutions.
2.  **Critical:** Brutal stress-testing and architectural auditing.
3.  **Empirical:** Real-world grounding via data research.

## ⚙️ The Thinking Engines
CCT is built on a modular "Plug-and-Think" architecture. You can expand it indefinitely.

### 1. Primitive Engines (The Atoms)
22+ core modes of thought (e.g., `linear`, `lateral`, `first_principles`, `metacognitive`). These are the building blocks used to deconstruct any problem.

### 2. Hybrid Engines (The Molecules)
Advanced, multi-step reasoning loops:
* **Actor-Critic Loop:** One sub-persona proposes, another (The Critic) attacks. Only the refined synthesis survives.
* **Temporal Horizon:** Projects the architecture across NOW (immediate), NEXT (scaling), and LATER (legacy/technical debt).
* **Empirical Research:** Explicitly forces the AI to fetch real-world benchmarks and CVEs before theorizing.

### 3. Sequential Engine (The Nervous System)
Manages the flow. It tracks `thought_number`, prevents logical loops, and ensures the AI doesn't "skip steps" in its reasoning chain.

## 🔄 The Pipeline: How it Thinks
When a Mission is dispatched, the AI follows this strict SOP:

1.  **Mission Start:** Initialize session in SQLite.
2.  **Empirical Grounding:** Search the web. Validate facts. No "lazy" internal knowledge.
3.  **Deconstruction:** Break the problem down using Primitives.
4.  **The Crucible:** Run the Actor-Critic debate to find vulnerabilities.
5.  **Future-Proofing:** Project technical debt via Temporal Horizon.
6.  **Human/Autonomous Clearance:** A veteran persona (25+ years exp) or YOU must grant clearance.
7.  **Final Execution:** Only now, the code is written.

## 🖥️ Mission Control Dashboard
We don't do "Black Box" AI. The **Streamlit Dashboard** is your proactive Dispatch Hub.

* **Proactive Dispatch:** Launch new missions directly from the UI. It generates a `CCT_DISPATCH.md` signal for your IDE.
* **Tree of Thought:** A real-time Graphviz visualization of how the AI is branching and contradicting its own ideas.
* **Architectural Ledger:** A searchable, persistent history of every architectural debate ever held in your system.

---

## 🛠️ Quick Start
1.  **Clone & Install:** `pip install -r requirements.txt`
2.  **Run Server:** `python src/main.py`
3.  **Launch Mission Control:** `streamlit run dashboard.py`
4.  **Connect to IDE:** Add the MCP server to Cursor, Trae, or Claude Desktop.

---
*Created by Steeven Andrian — Senior Systems Architect.*
*Built for those who believe AI should be a Co-Pilot, not an Autopilot.*