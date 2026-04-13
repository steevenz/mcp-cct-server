# 📖 Operational Guide: Deploying the CCT SYSTEM_PROMPT

To ensure the AI strictly follows the C&C Framework, empirical grounding, and token economy, you must inject `system-prompt.md` directly into the AI's core context window. 

## ⚙️ Step 1: File Placement (IDE Injection)

You do not paste this into the chat manually. You save it as a "Rules" file in the root directory of your project (or your global workspace) so the IDE reads it automatically in the background.

Depending on your AI IDE, copy the contents of `docs/rules/system-prompt.md` into the corresponding file at the root of your project:

* **Universal Approach:** Create a file named **`.iderules`** (Recommended Standard).
* **For Cursor:** Create a file named `.cursorrules`
* **For Windsurf:** Create a file named `.windsurfrules`
* **For Trae AI:** Create a file named `.traerules` (or add it to the Workspace AI Knowledge settings).
* **For Claude Desktop/Generic:** Paste the contents into the "System Prompt" or "Custom Instructions" configuration UI.

```bash
# Terminal quick-command (Example for the Universal Standard)
cp docs/rules/system-prompt.md .iderules
```

## 🧠 Step 2: The Behavioral Shift (What to Expect)

Once the prompt is active, the AI's behavior will fundamentally change. **Do not be alarmed if the AI refuses to write code immediately.**

1.  **The End of "Blind Coding":** If you ask, *"Write a login system in Kotlin"*, the AI will no longer just dump code. It will reply acknowledging the directive, initialize a CCT session, and begin Phase 1.5 (Empirical Grounding) and Phase 2 (Deconstruction).
2.  **Tool Usage:** You will see the AI autonomously making MCP tool calls (like `start_cct_session` or `cct_think_step`) before generating human-readable chat responses.
3.  **Persona Adoption:** The tone of the AI will shift to be more authoritative, analytical, and critical, matching the "Elite Principal Systems Architect" persona defined in the prompt.

## ⚖️ Step 3: Global Rules vs. Mission Dispatch

It is crucial to understand the separation of concerns between your two main documents:

| Document | Nature | What it Controls | How often to change? |
| :--- | :--- | :--- | :--- |
| **`.iderules`** | **STATIC** (The Law) | *How* the AI thinks (The 7 Phases, tool usage, scoring). | **Rarely.** Only when upgrading the CCT Framework. |
| **`cct-dispatch.md`** | **DYNAMIC** (The Mission) | *What* the AI thinks about (Problem, Anti-Patterns, Skills). | **Every session.** Generated fresh from the Dashboard. |

**Pro-Tip:** Do NOT edit the `.iderules` (System Prompt) to add project-specific details (like "We are using PostgreSQL"). Put project-specific details into the `cct-dispatch.md`. This keeps your System Prompt clean and globally applicable to any project.

## 🛠️ Step 4: Forcing Compliance

If the LLM starts acting lazy, skipping phases, or hallucinating without doing empirical research, you can "crack the whip" in the chat using the authority of the System Prompt.

**Compliance Prompts:**
* *"Halt. You are violating Phase 1.5 of your `.iderules`. You did not conduct empirical research. Search the web for current best practices before forming a hypothesis."*
* *"You skipped Phase 3 (The Crucible). Instantiate the Actor-Critic loop and stress-test this architecture immediately."*

***

With the `.iderules` acting as the immutable law and the `cct-dispatch.md` providing the dynamic mission parameters, your IDE is now fully transformed into an autonomous architectural engine.
