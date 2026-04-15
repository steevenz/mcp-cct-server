# 🧠 CCT MCP Server: The Cognitive Exocortex for Sovereign Intelligence

> "Intelligence without discipline is just noise; a sovereign AI must be audited by its own metacognition before it is granted the authority to act."
> — *CCT Whitepaper*

## 🚀 What is CCT?

**CCT (Creative Critical Thinking) MCP Server** is not just another set of tools; it is a **Cognitive Exocortex**—an external prefrontal cortex that transforms LLMs from stateless "text predictors" into **Sovereign Cognitive Systems** with persistent memory, self-auditing capabilities, and evolutionary learning.

While other MCP servers provide ephemeral thinking patterns (linear sequences without memory or quality assurance), CCT delivers **cognitive infrastructure** with:
- **Digital Hippocampus**: Persistent memory that learns from every reasoning session
- **Metacognitive Scoring**: 4-vector quality analysis (Clarity, Coherence, Novelty, Evidence)
- **Adversarial Auditing**: Actor-Critic cross-model validation to eliminate sycophancy bias
- **Financial Conscience**: Token economics with forensic cost tracking (USD/IDR)
- **Identity Layer**: Digital Twin personalization through USER_MINDSET and CCT_SOUL

📄 **Read the [CCT Whitepaper](docs/whitepaper.md)** for the complete architectural vision and technical specification.

📚 **Concept Documentation**:
- [How Memory Works](docs/concepts/how-memory-works.md) — Digital Hippocampus & Pattern Archiver
- [How Sequential Thinking Works](docs/concepts/how-sequential-thinking-works.md) — Cognitive Timeline Management
- [How Analysis Works](docs/concepts/how-analysis-works.md) — Scoring Engine & Bias Wall
- [How Token and Costs Calculated](docs/concepts/how-token-and-costs-calculated.md) — Cognitive Economics
- [How This Helps AI Think](docs/concepts/how-this-help-ai-have-creative-critical-thinking.md) — Creative & Critical Mechanisms
- [Full Concept Library →](docs/concepts/)

## ⚙️ Execution Paradigms (Dual Modes)

CCT is built for both velocity and extreme safety. The execution mode is automatically determined or manually toggled:

*   **🤖 Autonomous Mode:** The AI acts as the "Digital Architect". Powered by a server-side LLM (Gemini/OpenAI/Anthropic/Ollama), it performs synthesis, criticism, and persona generation internally. Perfect for extreme velocity and deep autonomous reasoning.
*   **🛑 Guided Mode (Cognitive Advisor):** For environments without direct server-side LLM access. The AI acts as a **War Room Advisor**. It provides high-fidelity structured instructions and templates, guiding your IDE's LLM through the complex thinking protocols.

See [How Autonomous/HITL Works](docs/concepts/how-autonomous-hitl-works.md) for detailed mode selection and clearance management.

## 🏆 Why CCT vs Other MCP Thinking Servers?

The MCP ecosystem now hosts multiple thinking-oriented servers—Sequential Thinking (official), CognitiveCompass, Thinking Patterns MCP, and others. While these tools provide structured reasoning, they share a fundamental limitation: **they are stateless, static, and lack evolutionary capability**.

| Capability | Sequential Thinking MCP | Thinking Patterns MCP | **CCT (This Server)** |
|:-----------|:----------------------|:----------------------|:----------------------|
| **Memory Persistence** | ❌ Stateless | ❌ Stateless | ✅ **Digital Hippocampus** (SQLite) |
| **Quality Assurance** | ❌ None | ❌ Schema validation only | ✅ **4-Vector Scoring** + Bias Wall |
| **Cross-Model Auditing** | ❌ Single model | ❌ Single model | ✅ **Actor-Critic** (External API support) |
| **Evolutionary Learning** | ❌ None | ❌ None | ✅ **Golden Patterns & Anti-Patterns** |
| **Financial Transparency** | ❌ None | ❌ None | ✅ **Forensic Cost Tracking** (USD/IDR) |
| **Identity Personalization** | ❌ None | ❌ None | ✅ **USER_MINDSET + CCT_SOUL** |
| **Dynamic Routing** | ❌ Static pipelines | ❌ Static frameworks | ✅ **Weighted 3-Tier Policy Engine** |

**The architectural difference**: Other servers treat thinking as a **transactional process** (input → framework → output). CCT treats thinking as **cognitive infrastructure**—cumulative, adaptive, and self-correcting.

📄 Read the [Preface: Why LLMs Need Cognitive Infrastructure](docs/whitepaper.md#preface-why-llms-need-cognitive-infrastructure) for the full analysis.

## 🔄 The Sovereign Cognitive Loop

When a Mission is dispatched, the AI follows the **6-Step Algorithmic Trace** defined in the [whitepaper](docs/whitepaper.md#8-the-sovereign-cognitive-loop-system-workflow--algorithm):

1.  **Zero-State Bootstrap:** Dependency injection initializes SQLite (WAL mode), Forex sync for pricing precision, and the library of Atomic Workers and Hybrid Molecules.
2.  **Ignition Scan (Discovery):** The `ComplexityService` and `PolicyService` run a weighted lexical scan to dynamically select the optimal thinking pipeline (DEBUG, ARCH, SEC, FEAT) based on domain complexity.
3.  **3-Tiered Policy Routing:** The `RoutingService` enforces the Sovereign Hierarchy—complex missions are forced into the **9-Step Master Pipeline**, while routine tasks follow domain-specific templates to avoid over-thinking.
4.  **Metacognitive Audit & Bias Wall:** Every thought is forensically audited by the `ScoringService` (4-vector metrics) while the Bias Wall monitors for hallucination flags. Quality drops trigger `UNCONVENTIONAL_PIVOT` to break cognitive plateaus.
5.  **Persistence & Long-Term Potentiation:** Thought data commits to the **Digital Hippocampus**. Elite thoughts (Clarity/Coherence > 0.9) are promoted to **Golden Thinking Patterns** for cross-session learning.
6.  **Forensic Closure & Telemetry Return:** The `PricingManager` performs final micro-cost audit. The user receives the result with a **Forensic Ledger** of every cognitive step and its cost.

**Detailed Documentation:**
- [How Routing Works](docs/concepts/how-routing-works.md) — 3-Tier Policy Engine
- [How Primitives Thinking Engine Works](docs/concepts/how-primitives-thinking-engine-works.md) — Atomic Workers
- [How Hybrid Thinking Engine Works](docs/concepts/how-hybrid-thinking-engine-works.md) — Actor-Critic & CouncilOfCritics
- [How Fusion Thinking Engine Works](docs/concepts/how-fusion-thinking-engine-works.md) — Multi-Agent Synthesis
- [How Continuous Learning Works](docs/concepts/how-continous-learning-works.md) — LTP & Pattern Archiver

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

# 5. Initialize Identity Layer (Optional but Recommended)
# CCT auto-generates high-fidelity mindset.md and soul.md if missing
```

> [!NOTE]
> For detailed integration instructions with Windsurf, Verdent.ai, Claude Desktop, and other IDEs, see the [Full Setup Guide](docs/guides/how-to-setup.md).
> For identity configuration and the "Lazy Failover" protocol, see [How Guidance Works](docs/concepts/how-guidance-works.md).

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

## 📖 Documentation Architecture

| Document | Purpose |
|:---------|:--------|
| **[CCT Whitepaper](docs/whitepaper.md)** | Complete architectural vision, 12-section technical specification |
| **[Concept Docs](docs/concepts/)** | 14 deep-dive guides for each CCT subsystem |
| **[Setup Guide](docs/guides/how-to-setup.md)** | IDE integration & configuration |
| **[Health Check](docs/guides/health-check.md)** | Diagnostics & troubleshooting |

---

**Created by Steeven Andrian Salim** — *Principal Systems Architect & Cybersecurity Expert*  
**CCT Whitepaper v5.0** — *Hardened for Sovereign Intelligence*  

> "Intelligence without discipline is just noise; a sovereign AI must be audited by its own metacognition before it is granted the authority to act."
