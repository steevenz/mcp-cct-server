# 📖 Operational Guide: Executing CCT Dispatch in Chat

The `cct-dispatch.md` file acts as the ultimate context bridge between your Streamlit Mission Control and your AI coding assistant. Once the dashboard generates this file, the IDE takes over.

## ⚙️ The Standard Workflow

### Step 1: Context Attachment
In your IDE chat (Cursor or Trae), you must first attach the dispatch file to the context window.
* **Type:** `@cct-dispatch.md` and select the file from the dropdown menu.

### Step 2: The Trigger Prompt
You do not need to re-explain the problem. The system prompt (`.cursorrules` / `.traerules`) combined with the dispatch file contains all the necessary constraints, modes, and memory injections. 

Use one of the following trigger prompts based on your desired execution style:

**Option A: The "Vibe Coding" Trigger (Recommended)**
> *"Initialize Phase 0. Read the attached dispatch, acknowledge the execution mode and injected memory, and execute the CCT pipeline autonomously."*

**Option B: The Strict Step-by-Step Trigger**
> *"Read the dispatch. Initialize Phase 0 and Phase 1.5 (Empirical Grounding), then pause and report your findings before proceeding to the deconstruction phase."*

---

## 👁️ What to Expect (The Observation Phase)

Once triggered, you should sit back and watch the AI's cognitive engine spin up. You will see the agent utilizing the MCP tools automatically:

1. **The Acknowledgment:** The AI will explicitly state which Thinking Patterns it is adopting and which Anti-Patterns it is avoiding based on the dispatch.
2. **Tool Execution:** You will see the AI calling `start_cct_session`, followed by `cct_think_step`. 
3. **Dashboard Sync:** If you have your Streamlit dashboard open on a secondary screen (or your DeX setup), you will see the "Tree of Thought" graph updating in real-time as the chat session progresses.

---

## 🛑 Handling the Clearance Checkpoint (Phase 6)

How the session concludes depends entirely on the `EXECUTION_MODE` variable set in your dispatch file.

### Scenario A: `AUTONOMOUS` Mode
The AI will debate internally, hit the > 0.95 Logic Score threshold, grant itself clearance, and immediately start writing the final files or architecture document in your workspace.

### Scenario B: `HUMAN-IN-THE-LOOP` Mode
The AI will abruptly stop generating code. It will output an **Executive Summary** in the chat, detailing the stress-test results from the Actor-Critic loop.
* **Your Action Required:** Review the summary.
* **Approval Prompt:** > *"Clearance granted. Proceed to Phase 7 and write the implementation."*
* **Rejection Prompt:** > *"Clearance denied. Your Temporal Horizon projection failed to account for [X]. Pivot laterally and re-evaluate Phase 3."*

---

## 💡 Pro-Tips for Session Recovery

If the AI gets distracted or hits a token limit mid-session, you can force it back on track using the SQLite memory state.

**Context Recovery Prompt:**
> *"You drifted. Re-read `@cct-dispatch.md`, fetch your last optimized history from the Memory Manager, and resume the pipeline from Phase 4."*

---

Here is an example of what you will see in your IDE chat when the AI reaches **Phase 6: The Clearance Checkpoint** under `HUMAN-IN-THE-LOOP` mode. 

This summary proves that the AI hasn't just "guessed" the code; it has brutally audited its own ideas before asking for your permission to touch the codebase.

***

### 🖥️ Example IDE Chat Output (AI Generating the Summary)

```markdown
# 🛑 PHASE 6: EXECUTIVE SUMMARY & CLEARANCE REQUEST

**Mission ID:** `session_8f92a1b`
**Status:** SUSPENDED (AWAITING HUMAN AUTHORIZATION)
**Domain:** SEC / ARCH (Loop EDR Authentication Module)

As per the `cct-dispatch.md` directive, I have completed the cognitive pipeline through Phase 5. I have withheld implementation code pending your review of the architectural synthesis below.

### 🧠 1. Memory & Pattern Alignment
* **Injected Thinking Pattern (`TP_91ddde72`):** Successfully applied the *Weighted Persona Consensus* model to ensure security didn't override system performance.
* **Avoided Anti-Pattern (`AP_Auth_04`):** Prevented the use of stateless JWTs without a revocation mechanism, utilizing the corrective action: *Stateful Redis-backed blacklist for compromised tokens.*

### 🔍 2. Empirical Grounding (Phase 1.5)
* Validated against the latest OAuth 2.1 best practices.
* Checked recent CVEs regarding token hijacking in Kotlin Multiplatform environments. No critical blockers found for the proposed stack.

### ⚔️ 3. The Crucible: Actor-Critic Synthesis (Phase 3)
* **The Proposal:** A decentralized JWT-based auth service to reduce database latency.
* **The Critic (Security Hardener):** Attacked the proposal. In an EDR context, if an endpoint is compromised, we cannot wait for a 15-minute JWT expiration to revoke access.
* **The Synthesis (Final Architecture):** We will implement ultra-short-lived JWTs (3 minutes) coupled with an asynchronous background Refresh Token Rotation strategy. A Redis tier will handle immediate, hard-revocation signals pushed via Server-Sent Events (SSE) to the gateways.

### 🔭 4. Temporal Horizon Projection (Phase 4)
* **NOW:** Secure, scalable auth that immediately mitigates endpoint compromise.
* **NEXT (6 Months):** Redis cluster will require sharding as the endpoint agent count scales past 50,000.
* **LATER (Technical Debt):** The SSE gateway logic will eventually need to be migrated to a dedicated gRPC microservice to handle the persistent connection load.

---
### ⚠️ AUTHORIZATION REQUIRED
The architecture is secure, scores a Logic metric of 0.96, and aligns with your O2System standards. 

**Do I have clearance to proceed to Phase 7 and implement the `AuthManager.kt` and `RedisRevocation.kt` modules?** *(Reply "Clearance Granted" to proceed, or "Clearance Denied" with pivot instructions).*
```

***

### 💡 Why this format is powerful for you:
1. **Zero Hallucination:** You can clearly see *how* it arrived at the Redis + Short JWT conclusion. It didn't just pull it from GitHub; it fought itself to get there.
2. **Total Control:** If you disagree with the "NEXT" projection (e.g., you prefer Hazelcast over Redis), you just reply: *"Clearance denied. Swap Redis for Hazelcast and regenerate the Crucible phase."*
3. **Cognitive Relief:** You don't have to read 500 lines of code to spot an architectural flaw. You audit the *logic* first, and let the AI write the code only when the blueprint is perfect.