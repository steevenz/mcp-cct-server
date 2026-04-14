# 🧠 CCT MCP Server: The Cognitive OS for Elite Architects

> "Most AI models are just fast talkers. This server turns them into Deep Thinkers."

## 🚀 What is this?

**CCT (Creative Critical Thinking) MCP Server** isn't just another set of tools; it's a **Cognitive Exoskeleton** for LLMs. While other MCP servers focus on giving AI *access* (reading files, searching the web), CCT focuses on giving AI **Reasoning Structure**.

It forces the LLM to stop giving "shallow-first" answers and instead utilize a high-fidelity, multi-layered thinking pipeline—persisting every single neuron-fire into a SQLite database.

## ⚙️ Execution Paradigms (Dual Modes)

CCT is built for both velocity and extreme safety. The execution mode is automatically determined or manually toggled:

*   **🤖 Autonomous Mode:** The AI acts as the "Digital Architect". Powered by a server-side LLM (Gemini/OpenAI/Anthropic/Ollama), it performs synthesis, criticism, and persona generation internally. Perfect for extreme velocity and deep autonomous reasoning.
*   **🛑 Guided Mode (Cognitive Advisor):** For environments without direct server-side LLM access. The AI acts as a **War Room Advisor**. It provides high-fidelity structured instructions and templates, guiding your IDE's LLM through the complex thinking protocols.

## 🔄 The Pipeline: How it Thinks

When a Mission is dispatched, the AI follows this strict SOP:

1.  **Phase 0 (Meta-Cognitive Routing):** AI dynamically selects its thinking pipeline (DEBUG, ARCH, FEAT) based on detected complexity.
2.  **Phase 1 (Engineering Deconstruction):** Mandatory SOP. Define success criteria (Eval-First) and break work into 15-minute units.
3.  **Phase 2 (Planning & Pattern Execution):** Apply the optimal reasoning model (ReAct, ToT, CoT).
4.  **Phase 3 (Empirical Grounding):** Search the web. Validate facts. Ground the mission in real-world data.
5.  **Phase 4 (The Crucible):** Run the Actor-Critic debate to find vulnerabilities and edge cases.
6.  **Phase 5 (Future-Proofing):** Project technical debt and scalability via Temporal Horizon.
7.  **Phase 6 (Final Execution):** Output the battle-tested code/architecture.

## 🛠️ Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/steevenz/mcp-cct-server.git
cd mcp-cct-server

# 2. Setup Virtual Environment (Required)
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate
# Activate (macOS/Linux)
source .venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Configure Environment
cp .env.example .env
# Edit .env and set your CCT_LLM_PROVIDER and API keys

> [!NOTE]
> For detailed instructions on integration with Windsurf, Verdent.ai, and other IDEs, check the [Full Setup Guide](docs/guides/how-to-setup.md).

## 🔌 IDE Integration (MCP Setup)

We recommend naming the server **`cct-cognitive-server`** in your configuration.

### Optimized JSON Configuration (Windsurf / Verdent.ai / Claude Desktop)

Replace `C:/PATH/TO/mcp-cct-server` with your actual absolute path.

```json
{
  "mcpServers": {
    "cct-cognitive-server": {
      "command": "C:/PATH/TO/mcp-cct-server/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/PATH/TO/mcp-cct-server/src/main.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        "CCT_TRANSPORT": "stdio",
        "CCT_LOG_LEVEL": "INFO",
        "CCT_LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CCT_LLM_PROVIDER` | Active LLM (gemini, openai, anthropic, ollama) | None (Guided) |
| `GEMINI_API_KEY` | Google AI Studio Key | None |
| `OPENAI_API_KEY` | OpenAI Key | None |
| `ANTHROPIC_API_KEY` | Anthropic Key | None |
| `OLLAMA_BASE_URL` | Local Ollama Endpoint | http://localhost:11434 |
| `CCT_LOG_LEVEL` | Log severity (DEBUG, INFO, ERROR) | INFO |

---

*Created by Steeven Andrian — Senior Systems Architect.*
*Built for those who believe AI should be a Co-Pilot, not an Autopilot.*
