# Data Flow Documentation

This document describes the actual data flow through the CCT MCP Server based on the codebase implementation, including request processing, cognitive workflows, and data persistence with real tool request/response examples.

## Table of Contents
1. [System Bootstrap Flow](#1-system-bootstrap-flow)
2. [MCP Tool Request/Response Flow](#2-mcp-tool-requestresponse-flow)
3. [Cognitive Workflow](#3-cognitive-workflow)
4. [Session Lifecycle Data Flow](#4-session-lifecycle-data-flow)
5. [Strategy Selection and Execution Flow](#5-strategy-selection-and-execution-flow)
6. [Data Persistence Flow](#6-data-persistence-flow)
7. [LLM Integration Flow](#7-llm-integration-flow)

---

## 1. System Bootstrap Flow

### Component Initialization Sequence (src/main.py)

```
┌─────────────────────────────────────────────────────────────┐
│              System Bootstrap Flow (main.py)                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Configuration Loading                                    │
│     ┌─────────────────────────────────────────────────┐      │
│     │ load_settings() from .env                     │      │
│     │ - Server configuration (host, port, transport) │      │
│     │ - LLM provider settings                        │      │
│     │ - Database and pricing paths                  │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  2. Core Engines Initialization                            │
│     ┌─────────────────────────────────────────────────┐      │
│     │ MemoryManager() - SQLite persistence          │      │
│     │ SequentialEngine(memory) - Sequence control     │      │
│     │ ScoringEngine() - Quality analysis              │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  3. Hybrid Services Initialization                           │
│     ┌─────────────────────────────────────────────────┐      │
│     │ ComplexityService() - Task complexity detection │      │
│     │ GuidanceService() - Cognitive guidance          │      │
│     │ AutonomousService(settings, memory) - Auto exec  │      │
│     │ ThoughtGenerationService(settings) - LLM client │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  4. Identity and Security Initialization                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ IdentityService() - provision_assets()          │      │
│     │ DigitalHippocampus(memory, identity) - Learning  │      │
│     │ IdentityService(hippocampus) - Dynamic identity  │      │
│     │ AdversarialReviewService(settings, identity)    │      │
│     │ InternalClearanceService(scoring) - Clearance   │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  5. Cognitive Engines Initialization                         │
│     ┌─────────────────────────────────────────────────┐      │
│     │ FusionOrchestrator(memory, scoring, sequential,  │      │
│     │                   autonomous, thought_service,  │      │
│     │                   guidance, identity)            │      │
│     │ IntelligenceRouter(scoring) - Mode selection    │      │
│     │ CognitiveEngineRegistry(...) - Strategy mapping │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  6. Master Orchestrator Initialization                       │
│     ┌─────────────────────────────────────────────────┐      │
│     │ CognitiveOrchestrator(memory, sequential,       │      │
│     │                   registry, fusion, router,      │      │
│     │                   identity, autonomous,          │      │
│     │                   internal_clearance)            │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  7. MCP Server Initialization                                 │
│     ┌─────────────────────────────────────────────────┐      │
│     │ FastMCP(settings.server_name, host, port)       │      │
│     │ register_simplified_tools(mcp, orchestrator,   │      │
│     │                         settings, complexity)   │      │
│     │ register_export_tools(mcp, orchestrator, settings)│      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  8. FastAPI Wrapper (for SSE/HTTP transport)                 │
│     ┌─────────────────────────────────────────────────┐      │
│     │ FastAPI(title="CCT Cognitive OS API")          │      │
│     │ /health endpoint (API key protected)             │      │
│     │ /status endpoint (API key protected)             │      │
│     │ Mount MCP app at /cognitive-api/v1/sync          │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  9. Transport Selection                                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ if transport in ("sse", "http"):               │      │
│     │   uvicorn.run(app, host, port)                  │      │
│     │ else:                                            │      │
│     │   mcp_instance.run(transport="stdio")           │      │
│     └─────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. MCP Tool Request/Response Flow

### Available MCP Tools

The CCT MCP Server exposes 6 main tools via FastMCP:

1. **thinking** - Create new session + execute first thinking step
2. **rethinking** - Continue thinking from existing session
3. **list_thinking** - List all cognitive thinking sessions
4. **branches** - Tree of Thoughts branch management
5. **export_thinking_session** - Export session history (with session_token)
6. **analyze_session** - Analyze session quality (with session_token)

### Tool 1: thinking - Session Creation + First Step

**Request Flow:**
```
Client MCP Call
    │
    ├─ thinking(
    │     problem_statement: str,
    │     llm_model_name: str,
    │     thought_content: str = "",
    │     profile: str = "balanced",
    │     model_id: str = "",
    │     estimated_thoughts: int = 0
    │   )
    │
    ├─ validate_problem_statement()
    │
    ├─ ComplexityService.detect_complexity(problem_statement)
    │  └─ Returns: TaskComplexity (SIMPLE, MODERATE, COMPLEX, SOVEREIGN)
    │
    ├─ PipelineSelector.detect_category(problem_statement)
    │  └─ Returns: Primary category (e.g., "ARCHITECTURE", "SECURITY")
    │
    ├─ PipelineSelector.detect_categories(problem_statement)
    │  └─ Returns: Dict of categories with scores
    │
    ├─ orchestrator.memory.create_session()
    │  ├─ Generate session_id (UUID)
    │  ├─ Store in SQLite (sessions table)
    │  ├─ Set profile, estimated_thoughts, model_id
    │  ├─ Store detected_categories, primary_category
       │  └─ Store suggested_pipeline
    │
    ├─ _get_strategy_pipeline(complexity, step=0, category)
    │  └─ Returns: ThinkingStrategy (e.g., LINEAR, EMPIRICAL_RESEARCH)
    │
    ├─ orchestrator.execute_strategy(session_id, strategy, payload)
    │  ├─ CognitiveEngineRegistry.get_engine(strategy)
    │  ├─ engine.execute(session_id, payload)
    │  │  ├─ SequentialEngine.process_sequence_step()
    │  │  ├─ Generate EnhancedThought
    │  │  ├─ ScoringEngine.analyze_thought()
    │  │  ├─ PatternArchiver.archive_thought() (if elite)
    │  │  └─ MemoryManager.add_thought()
    │  ├─ Update session usage statistics
    │  └─ Return thought result with usage metrics
    │
    └─ Return response to client
```

**Example Request:**
```python
thinking(
    problem_statement="Design a scalable microservices architecture",
    llm_model_name="gemini-1.5-flash",
    profile="balanced",
    estimated_thoughts=0
)
```

**Example Response:**
```python
{
    "status": "success",
    "session_id": "sess_abc123xyz",
    "detected_complexity": "moderate",
    "detected_category": "ARCHITECTURE",
    "steps": "1/5",
    "strategy_used": "empirical_research",
    "thought_result": {
        "generated_thought_id": "thought_xyz789",
        "content": "Microservices architecture provides scalability through...",
        "thought_type": "analysis",
        "metrics": {
            "logical_coherence": 0.92,
            "evidence_strength": 0.85,
            "clarity_score": 0.88,
            "input_tokens": 120,
            "output_tokens": 350,
            "input_cost_usd": 0.0001,
            "output_cost_usd": 0.0005
        }
    },
    "next_action": "Call rethinking with step=2",
    "processing_time": "2.345s"
}
```

### Tool 2: rethinking - Continue Thinking

**Request Flow:**
```
Client MCP Call
    │
    ├─ rethinking(
    │     session_id: str,
    │     llm_model_name: str,
    │     thought_content: str,
    │     thought_number: int = 2,
    │     estimated_total_thoughts: int = 5,
    │     next_thought_needed: bool = True,
    │     thought_type: str = "analysis",
    │     strategy: str = "auto",
    │     is_revision: bool = False,
    │     revises_thought_id: Optional[str] = None,
    │     branch_from_id: Optional[str] = None,
    │     branch_id: Optional[str] = None,
    │     critic_persona: str = "auto"
    │   )
    │
    ├─ validate_session_id(session_id)
    ├─ validate_thought_content(thought_content)
    │
    ├─ orchestrator.memory.get_session(session_id)
    │
    ├─ orchestrator.memory.get_session_history(session_id)
    │
    ├─ Update session.model_id if llm_model_name differs
    │
    ├─ Determine strategy:
    │  ├─ if strategy == "auto":
    │  │  └─ _get_strategy_pipeline(complexity, thought_number-1, category)
    │  └─ else: ThinkingStrategy(strategy)
    │
    ├─ Build payload with strategy-specific fields:
    │  ├─ ACTOR_CRITIC_LOOP: target_thought_id, critic_persona
    │  └─ MULTI_AGENT_FUSION: target_thought_id, personas
    │
    ├─ orchestrator.execute_strategy(session_id, strategy, payload)
    │  └─ Same flow as thinking tool
    │
    ├─ Determine is_complete:
    │  └─ not next_thought_needed or thought_number >= estimated_total_thoughts
    │
    └─ Return response to client
```

**Example Request:**
```python
rethinking(
    session_id="sess_abc123xyz",
    llm_model_name="gemini-1.5-flash",
    thought_content="Consider API gateway pattern for service communication",
    thought_number=2,
    estimated_total_thoughts=5,
    next_thought_needed=True,
    strategy="auto"
)
```

**Example Response:**
```python
{
    "status": "success",
    "session_id": "sess_abc123xyz",
    "thought_number": 2,
    "is_complete": False,
    "strategy": "first_principles",
    "thought_result": {
        "generated_thought_id": "thought_xyz790",
        "content": "API gateway pattern centralizes...",
        "metrics": {...},
        "usage": {
            "session_totals": {
                "tokens": {"input": 250, "output": 700, "total": 950},
                "cost_usd": 0.0012
            }
        }
    }
}
```

### Tool 3: list_thinking - List Sessions

**Request Flow:**
```
Client MCP Call
    │
    ├─ list_thinking(
    │     include_archived: bool = False,
    │     status_filter: str = "all"
    │   )
    │
    ├─ orchestrator.memory.list_sessions()
    │
    ├─ For each session_id:
    │  ├─ orchestrator.memory.get_session(session_id)
    │  ├─ orchestrator.memory.get_session_history(session_id)
    │  └─ Build result object:
    │     ├─ id
    │     ├─ status
    │     ├─ summary (problem_statement[:60] + "...")
    │     ├─ steps ("{len(history)}/{estimated_total_thoughts}")
    │     └─ complexity
    │
    └─ Return response to client
```

**Example Request:**
```python
list_thinking()
```

**Example Response:**
```python
{
    "sessions": [
        {
            "id": "sess_abc123xyz",
            "status": "active",
            "summary": "Design a scalable microservices architecture...",
            "steps": "3/5",
            "complexity": "moderate"
        },
        {
            "id": "sess_def456uvw",
            "status": "completed",
            "summary": "Implement authentication system...",
            "steps": "8/8",
            "complexity": "complex"
        }
    ],
    "total": 2
}
```

### Tool 4: branches - Tree of Thoughts Management

**Request Flow:**
```
Client MCP Call
    │
    ├─ branches(
    │     session_id: str,
    │     action: str = "get_tree",
    │     thought_id: str = "",
    │     branch_ids: List[str] = None,
    │     reason: str = ""
    │   )
    │
    ├─ validate_session_id(session_id)
    │
    ├─ Switch based on action:
    │  ├─ "get_tree":
    │  │  └─ orchestrator.memory.get_branch_tree(session_id, thought_id)
    │  ├─ "compare":
    │  │  └─ orchestrator.memory.compare_branches(session_id, branch_ids)
    │  ├─ "prune":
    │  │  └─ orchestrator.memory.prune_branch(session_id, thought_id, reason)
    │  └─ "promote":
    │     └─ orchestrator.memory.promote_branch(session_id, thought_id)
    │
    └─ Return response to client
```

**Example Request:**
```python
branches(
    session_id="sess_abc123xyz",
    action="get_tree"
)
```

**Example Response:**
```python
{
    "status": "success",
    "action": "get_tree",
    "tree": {
        "root": "thought_xyz789",
        "branches": [
            {
                "thought_id": "thought_xyz790",
                "parent_id": "thought_xyz789",
                "children": ["thought_xyz791"]
            }
        ]
    }
}
```

### Tool 5: export_thinking_session - Export Session

**Request Flow:**
```
Client MCP Call
    │
    ├─ export_thinking_session(
    │     session_id: str,
    │     session_token: str = ""
    │   )
    │
    ├─ orchestrator.memory.validate_session_token(session_id, session_token)
    │  └─ SECURITY: Returns 403 if invalid
    │
    ├─ orchestrator.memory.get_session_history(session_id)
    │
    ├─ Format thoughts as JSON
    │
    └─ Return response to client
```

**Example Request:**
```python
export_thinking_session(
    session_id="sess_abc123xyz",
    session_token="token_secure_xyz"
)
```

**Example Response:**
```python
{
    "steps": [
        {
            "id": "thought_xyz789",
            "content": "Microservices architecture provides...",
            "thought_type": "analysis",
            "strategy": "empirical_research",
            "metrics": {...}
        },
        {
            "id": "thought_xyz790",
            "content": "API gateway pattern centralizes...",
            "thought_type": "analysis",
            "strategy": "first_principles",
            "metrics": {...}
        }
    ]
}
```

### Tool 6: analyze_session - Analyze Session Quality

**Request Flow:**
```
Client MCP Call
    │
    ├─ analyze_session(
    │     session_id: str,
    │     session_token: str = ""
    │   )
    │
    ├─ orchestrator.memory.validate_session_token(session_id, session_token)
    │  └─ SECURITY: Returns 403 if invalid
    │
    ├─ orchestrator.memory.get_session(session_id)
    │
    ├─ orchestrator.memory.get_session_history(session_id)
    │
    ├─ IncrementalSessionAnalyzer:
    │  ├─ For each thought: analyzer.add_thought(thought.content)
    │  └─ Get final metrics
    │
    ├─ Build SessionMetrics:
    │  ├─ clarity_score
    │  ├─ bias_flags
    │  └─ consistency_score
    │
    └─ Return response to client
```

**Example Request:**
```python
analyze_session(
    session_id="sess_abc123xyz",
    session_token="token_secure_xyz"
)
```

**Example Response:**
```python
{
    "session_id": "sess_abc123xyz",
    "problem_statement": "Design a scalable microservices architecture",
    "metrics": {
        "clarity_score": 0.8750,
        "bias_flags": ["confirmation_bias"],
        "consistency_score": 0.9230
    }
}
```

### Orchestrator execute_strategy Flow

```
┌─────────────────────────────────────────────────────────────┐
│         CognitiveOrchestrator.execute_strategy() Flow         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. HITL Enforcement Check                                  │
│     ┌─────────────────────────────────────────────────┐      │
│     │ autonomous.check_execution_allowed(session_id)  │      │
│     │ - Block if awaiting human clearance              │      │
│     │ - Return error if HITL profile and blocked       │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  2. Token Economy - Context Compression                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ memory.get_session_history(session_id)          │      │
│     │ - Check if history > 5 thoughts                │      │
│     │ - compress_session_context() if needed          │      │
│     │ - Add historical_summary to payload              │      │
│     │ - Add preserved_context_ids to payload          │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  3. Hybrid Knowledge - Skills Injection                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ skills_loader.inject_skills_context(strategy,   │      │
│     │                                          payload)│      │
│     │ - Load action skills for strategy              │      │
│     │ - Inject into payload                          │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  4. Engine Selection via Registry                           │
│     ┌─────────────────────────────────────────────────┐      │
│     │ CognitiveEngineRegistry.get_engine(strategy)     │      │
│     │ - Primitive strategies → DynamicPrimitiveEngine│      │
│     │ - Hybrid strategies → Specific hybrid engine    │      │
│     │ - Multi-agent fusion → MultiAgentFusionEngine   │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  5. Engine Execution                                        │
│     ┌─────────────────────────────────────────────────┐      │
│     │ engine.execute(session_id, payload)             │      │
│     │ ├─ SequentialEngine.process_sequence_step()    │      │
│     │ ├─ Generate EnhancedThought                    │      │
│     │ ├─ ScoringEngine.analyze_thought()              │      │
│     │ ├─ PatternArchiver.archive_thought() (if elite)│      │
│     │ └─ MemoryManager.add_thought()                  │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  6. Automatic Pipeline - Adaptive Feedback                 │
│     ┌─────────────────────────────────────────────────┐      │
│     │ orchestrator.check_and_pivot(session_id)        │      │
│     │ - Evaluate if strategy needs change              │      │
│     │ - Pivot to different strategy if needed         │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  7. Usage Tracking - Transparency Layer                    │
│     ┌─────────────────────────────────────────────────┐      │
│     │ - Recalculate session totals from history        │      │
│     │ - Update session.total_prompt_tokens            │      │
│     │ - Update session.total_completion_tokens        │      │
│     │ - Update session.total_cost_usd/idr             │      │
│     │ - Archive elite thoughts (logical_coherence ≥ 0.9)│      │
│     │ - Attach usage block to result                  │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  8. HITL Trigger - Clearance Checkpoint                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ sequential.evaluate_convergence()               │      │
│     │ - Check if session converged                    │      │
│     │ - If HITL profile and converged:                │      │
│     │   - autonomous.trigger_human_stop()             │      │
│     │   - Merge HITL instructions into result         │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  9. Return Result to Tool Handler                           │
│     ┌─────────────────────────────────────────────────┐      │
│     │ - Return thought result with usage metrics      │      │
│     │ - Include HITL instructions if applicable       │      │
│     └─────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Primitive Engine Processing Flow (DynamicPrimitiveEngine)

```
┌─────────────────────────────────────────────────────────────┐
│         DynamicPrimitiveEngine 4-Stage Lifecycle              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Stage 1: Contextual Injection                               │
│     ├─ SequentialEngine.process_sequence_step()             │
│     ├─ Retrieve state for Tree of Thoughts position         │
│     └─ Ensure context of previous thoughts and branches      │
│                          │                                  │
│                          ▼                                  │
│  Stage 2: Hardened Validation                                │
│     ├─ ScoringEngine.analyze_thought()                       │
│     ├─ Token-optimized with 4000 token budget                │
│     ├─ Calculate: Clarity, Coherence, Novelty, Evidence     │
│     └─ Receive quantitative scores                          │
│                          │                                  │
│                          ▼                                  │
│  Stage 3: Cognitive Evolution (LTP)                           │
│     ├─ PatternArchiver.archive_thought()                     │
│     ├─ Promote elite thoughts (logical_coherence > 0.9)      │
│     ├─ Elite thoughts become Golden Thinking Patterns        │
│     └─ Patterns strengthen with use (Long-Term Potentiation)│
│                          │                                  │
│                          ▼                                  │
│  Stage 4: Early Convergence Detection                         │
│     ├─ Detect "Breakthrough" thoughts meeting victory cond. │
│     ├─ Trigger early stop to save tokens                     │
│     └─ Use dynamic threshold (DEFAULT_TP_THRESHOLD)          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Session Lifecycle Data Flow

### Session Creation Flow (in thinking tool)

```
┌─────────────────────────────────────────────────────────────┐
│            Session Creation Flow (thinking tool)               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Input Validation                                        │
│     ┌─────────────────────────────────────────────────┐      │
│     │ validate_problem_statement(problem_statement)    │      │
│     │ - Check non-empty string                         │      │
│     │ - Check minimum length                           │      │
│     │ - Return error if invalid                         │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  2. Complexity Detection                                   │
│     ┌─────────────────────────────────────────────────┐      │
│     │ ComplexityService.detect_complexity()            │      │
│     │ - Analyze problem statement                    │      │
│     │ - Return TaskComplexity (SIMPLE, MODERATE,       │      │
│     │                      COMPLEX, SOVEREIGN)         │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  3. Category Detection                                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ PipelineSelector.detect_category()              │      │
│     │ - Detect primary category (e.g., ARCHITECTURE)   │      │
│     │ PipelineSelector.detect_categories()           │      │
│     │ - Detect multiple categories with scores         │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  4. Profile Mapping                                        │
│     ┌─────────────────────────────────────────────────┐      │
│     │ Map string profile to CCTProfile enum           │      │
│     │ - creative → CCTProfile.CREATIVE_FIRST           │      │
│     │ - critical → CCTProfile.CRITICAL_FIRST           │      │
│     │ - balanced → CCTProfile.BALANCED                 │      │
│     │ - human_in_the_loop → CCTProfile.HUMAN_IN_THE_LOOP│      │
│     │ - deep_recursive → CCTProfile.DEEP_RECURSIVE      │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  5. Pipeline Selection                                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ PipelineSelector.select_pipeline()             │      │
│     │ - Select pipeline based on complexity           │      │
│     │ - Return list of ThinkingStrategy enum values   │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  6. Estimated Thoughts Calculation                          │
│     ┌─────────────────────────────────────────────────┐      │
│     │ - SOVEREIGN: 10 thoughts                         │      │
│     │ - COMPLEX: 8 thoughts                            │      │
│     │ - MODERATE: 5 thoughts                           │      │
│     │ - SIMPLE: 3 thoughts                             │      │
│     │ - Or use user-provided estimated_thoughts        │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  7. Session Creation                                        │
│     ┌─────────────────────────────────────────────────┐      │
│     │ orchestrator.memory.create_session()             │      │
│     │ - Generate session_id (UUID)                   │      │
│     │ - Store in SQLite (sessions table)              │      │
│     │ - Store as JSON blob with all metadata          │      │
│     │ - Initialize session state                      │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  8. Context Persistence                                    │
│     ┌─────────────────────────────────────────────────┐      │
│     │ orchestrator.memory.update_session()             │      │
│     │ - Store detected_categories                    │      │
│     │ - Store primary_category                        │      │
│     │ - Store suggested_pipeline                       │      │
│     │ - Store complexity value                         │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  9. First Strategy Selection                               │
│     ┌─────────────────────────────────────────────────┐      │
│     │ _get_strategy_pipeline(complexity, step=0,       │      │
│     │                      category)                  │      │
│     │ - Select first strategy from pipeline           │      │
│     │ - Return ThinkingStrategy enum                   │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  10. Execute First Step                                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ orchestrator.execute_strategy(session_id,        │      │
│     │                                 strategy,       │      │
│     │                                 payload)        │      │
│     │ - Execute cognitive processing                 │      │
│     │ - Generate first thought                       │      │
│     │ - Store in database                             │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  11. Response with Session Metadata                          │
│     ┌─────────────────────────────────────────────────┐      │
│     │ Return:                                          │      │
│     │ - session_id                                     │      │
│     │ - detected_complexity                           │      │
│     │ - detected_category                             │      │
│     │ - steps (e.g., "1/5")                           │      │
│     │ - strategy_used                                 │      │
│     │ - thought_result                                 │      │
│     │ - next_action                                   │      │
│     │ - processing_time                               │      │
│     └─────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Session Data Structure

**Database Schema (SQLite with JSON blobs)**:
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    data JSON NOT NULL
);

CREATE TABLE thoughts (
    thought_id TEXT PRIMARY KEY,
    session_id TEXT,
    data JSON NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);
```

**Session State Object (CCTSessionState)**:
```python
CCTSessionState(
    session_id="sess_abc123xyz",
    problem_statement="Design scalable system",
    profile=CCTProfile.BALANCED,
    status=SessionStatus.ACTIVE,
    created_at=datetime(2026, 4, 15, 7, 0, 0),
    updated_at=datetime(2026, 4, 15, 7, 0, 0),
    estimated_total_thoughts=5,
    current_thought_number=0,
    model_id="gemini-1.5-flash",
    complexity="moderate",
    primary_category="ARCHITECTURE",
    detected_categories={"ARCHITECTURE": 0.9, "SCALABILITY": 0.7},
    suggested_pipeline=["empirical_research", "first_principles", ...],
    history_ids=[],
    total_prompt_tokens=0,
    total_completion_tokens=0,
    total_cost_usd=0.0,
    total_cost_idr=0.0
)
```

### Session Termination Flow

```
Session Termination
│
├─ export_session()
│  ├─ Retrieve session data
│  ├─ Format for export (markdown/json)
│  ├─ Archive thinking patterns
│  └─ Mark session as completed
│
└─ Automatic cleanup
   ├─ Session expiration check
   ├─ Inactive session removal
   └─ Database cleanup
```

---

## 5. Strategy Selection and Execution Flow

### CognitiveEngineRegistry Strategy Mapping

```
┌─────────────────────────────────────────────────────────────┐
│      CognitiveEngineRegistry Strategy-to-Engine Mapping       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Registry Initialization                                   │
│     ┌─────────────────────────────────────────────────┐      │
│     │ _initialize_registry()                          │      │
│     │ - Iterate all ThinkingStrategy enum values     │      │
│     │ - Map each strategy to appropriate engine       │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  2. Special Case: Multi-Agent Fusion                        │
│     ┌─────────────────────────────────────────────────┐      │
│     │ If strategy == MULTI_AGENT_FUSION:              │      │
│     │ - Create MultiAgentFusionEngine                  │      │
│     │ - Inject: memory, sequential, fusion,           │      │
│     │           autonomous, thought_service,          │      │
│     │           guidance, identity, scoring            │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  3. Hybrid Strategy Mapping                                │
│     ┌─────────────────────────────────────────────────┐      │
│     │ ACTOR_CRITIC_LOOP → ActorCriticEngine           │      │
│     │ COUNCIL_OF_CRITICS → CouncilOfCriticsEngine     │      │
│     │ UNCONVENTIONAL_PIVOT → LateralEngine            │      │
│     │ LONG_TERM_HORIZON → LongTermHorizonEngine       │      │
│     │ - Inject appropriate services for each hybrid   │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  4. Primitive Strategy Mapping (Dynamic Factory)              │
│     ┌─────────────────────────────────────────────────┐      │
│     │ All other strategies → DynamicPrimitiveEngine   │      │
│     │ - Create single engine instance per strategy    │      │
│     │ - Inject: memory, sequential, identity, scoring │      │
│     │ - Pass strategy to constructor                 │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  5. Engine Retrieval                                       │
│     ┌─────────────────────────────────────────────────┐      │
│     │ get_engine(strategy: ThinkingStrategy)           │      │
│     │ - Look up strategy in _engines dict              │      │
│     │ - Return BaseCognitiveEngine instance             │      │
│     │ - Return None if not found                       │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  6. Engine Execution                                        │
│     ┌─────────────────────────────────────────────────┐      │
│     │ engine.execute(session_id, payload)             │      │
│     │ - Each engine implements BaseCognitiveEngine    │      │
│     │ - Returns Dict[str, Any] with result            │      │
│     └─────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Strategy Selection via _get_strategy_pipeline

```
┌─────────────────────────────────────────────────────────────┐
│        Strategy Selection (simplified_tools.py)               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Determine Pipeline Based on Complexity                  │
│     ┌─────────────────────────────────────────────────┐      │
│     │ if complexity in (COMPLEX, SOVEREIGN):         │      │
│     │   pipeline = PipelineSelector.SOVEREIGN_PIPELINE│      │
│     │ elif complexity == SIMPLE:                      │      │
│     │   - Step 0: LINEAR                             │      │
│     │   - Step 1: ANALYTICAL                         │      │
│     │   - Step 2+: INTEGRATIVE                       │      │
│     │ elif complexity == MODERATE:                   │      │
│     │   - Step 0: EMPIRICAL_RESEARCH                 │      │
│     │   - Step 1: FIRST_PRINCIPLES                   │      │
│     │   - Step 2: SYSTEMIC                           │      │
│     │   - Step 3+: INTEGRATIVE                       │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  2. Category-Based Template Override                        │
│     ┌─────────────────────────────────────────────────┐      │
│     │ if category != "GENERIC":                       │      │
│     │   template = PipelineSelector.PIPELINE_TEMPLATES│      │
│     │   if template and step < len(template):         │      │
│     │     return template[step]                       │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  3. Return Strategy                                         │
│     ┌─────────────────────────────────────────────────┐      │
│     │ return ThinkingStrategy(selected_strategy)      │      │
│     └─────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Strategy Selection Example

**Input**:
```python
{
    "complexity": TaskComplexity.MODERATE,
    "current_step": 0,
    "category": "ARCHITECTURE"
}
```

**Pipeline Selection**:
```python
{
    "pipeline": ["empirical_research", "first_principles", "systemic", "integrative"],
    "selected_strategy": "empirical_research"
}
```

**Engine Mapping**:
```python
{
    "strategy": ThinkingStrategy.EMPIRICAL_RESEARCH,
    "engine": DynamicPrimitiveEngine(strategy=EMPIRICAL_RESEARCH),
    "engine_type": "primitive"
}
```

---

## 6. Data Persistence Flow

### MemoryManager SQLite Operations Flow

```
┌─────────────────────────────────────────────────────────────┐
│          MemoryManager SQLite with JSON Blob Storage          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Database Initialization                                   │
│     ┌─────────────────────────────────────────────────┐      │
│     │ MemoryManager.__init__(db_path)                │      │
│     │ - Resolve absolute db_path                     │      │
│     │ - SECURITY: Check path traversal attack        │      │
│     │ - Initialize _write_lock (threading.Lock)      │      │
│     │ - _init_db() - Create tables if not exist       │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  2. Connection Management                                   │
│     ┌─────────────────────────────────────────────────┐      │
│     │ _get_connection()                               │      │
│     │ - Create new SQLite connection per operation    │      │
│     │ - Enable WAL mode (PRAGMA journal_mode=WAL)     │      │
│     │ - Allows concurrent reads without blocking      │      │
│     │ - Thread-safe with check_same_thread=False     │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  3. Session Operations (JSON Blob Storage)                  │
│     ┌─────────────────────────────────────────────────┐      │
│     │ CREATE: create_session()                       │      │
│     │ - Serialize CCTSessionState to JSON             │      │
│     │ - INSERT INTO sessions (session_id, data)       │      │
│     │ READ: get_session(session_id)                   │      │
│     │ - SELECT data FROM sessions WHERE session_id=?  │      │
│     │ - Deserialize JSON to CCTSessionState           │      │
│     │ UPDATE: update_session(session)                 │      │
│     │ - Serialize to JSON                             │      │
│     │ - UPDATE sessions SET data=? WHERE session_id=? │      │
│     │ LIST: list_sessions()                           │      │
│     │ - SELECT session_id FROM sessions               │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  4. Thought Operations (JSON Blob Storage)                   │
│     ┌─────────────────────────────────────────────────┐      │
│     │ CREATE: add_thought(thought)                    │      │
│     │ - Serialize EnhancedThought to JSON             │      │
│     │ - INSERT INTO thoughts (thought_id, session_id, │      │
│     │                      data)                      │      │
│     │ READ: get_thought(thought_id)                   │      │
│     │ - SELECT data FROM thoughts WHERE thought_id=?   │      │
│     │ - Deserialize JSON to EnhancedThought           │      │
│     │ LIST: get_session_history(session_id)            │      │
│     │ - SELECT data FROM thoughts WHERE session_id=?  │      │
│     │ - Deserialize all to list of EnhancedThought      │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  5. Thinking Pattern Operations                             │
│     ┌─────────────────────────────────────────────────┐      │
│     │ ARCHIVE: PatternArchiver.archive_thought()      │      │
│     │ - Serialize GoldenThinkingPattern to JSON        │      │
│     │ - INSERT INTO thinking_patterns                  │      │
│     │ RETRIEVE: get_thinking_pattern(pattern_id)      │      │
│     │ - SELECT data FROM thinking_patterns             │      │
│     │ INJECT: PatternInjector.inject_pattern()        │      │
│     │ - Retrieve pattern and add to context           │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  6. Anti-Pattern Operations                                  │
│     ┌─────────────────────────────────────────────────┐      │
│     │ RECORD: record_anti_pattern()                   │      │
│     │ - Serialize AntiPattern to JSON                 │      │
│     │ - INSERT INTO anti_patterns                     │      │
│     │ RETRIEVE: get_anti_patterns()                   │      │
│     │ - SELECT data FROM anti_patterns                │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  7. Branch Operations (Tree of Thoughts)                     │
│     ┌─────────────────────────────────────────────────┐      │
│     │ GET_TREE: get_branch_tree(session_id, thought_id)│      │
│     │ - Query thoughts with parent_id relationships    │      │
│     │ COMPARE: compare_branches(session_id, branch_ids)│      │
│     │ - Retrieve and compare branch thoughts           │      │
│     │ PRUNE: prune_branch(session_id, thought_id)      │      │
│     │ - Mark thought and descendants as pruned         │      │
│     │ PROMOTE: promote_branch(session_id, thought_id) │      │
│     │ - Move branch to mainline                       │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  8. Thread Safety and Audit Logging                         │
│     ┌─────────────────────────────────────────────────┐      │
│     │ Write Operations:                                │      │
│     │ - Acquire _write_lock before writes              │      │
│     │ - Serialize concurrent writes from async handlers│      │
│     │ Audit Logging:                                   │      │
│     │ - _audit_log(operation, entity_id, detail)      │      │
│     │ - Emit structured audit log for every write       │      │
│     └─────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema (SQLite with JSON Blobs)

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    data JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS thoughts (
    thought_id TEXT PRIMARY KEY,
    session_id TEXT,
    data JSON NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS thinking_patterns (
    tp_id TEXT PRIMARY KEY,
    thought_id TEXT,
    usage_count INTEGER DEFAULT 1,
    data JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS anti_patterns (
    failure_id TEXT PRIMARY KEY,
    thought_id TEXT,
    failed_strategy TEXT,
    category TEXT,
    data JSON NOT NULL
);
```

### Usage Tracking Data Flow

```
Token Usage Tracking
│
├─ LLM Call (ThoughtGenerationService)
│  ├─ Count input tokens
│  ├─ Count output tokens
│  └─ Calculate cost (pricing_manager)
│
├─ Session Update (CognitiveOrchestrator)
│  ├─ Recalculate totals from history
│  ├─ Update session.total_prompt_tokens
│  ├─ Update session.total_completion_tokens
│  ├─ Update session.total_cost_usd
│  ├─ Update session.total_cost_idr
│  └─ Update session.total_tokens
│
├─ Usage Block in Response
│  ├─ model_used
│  ├─ session_totals (tokens, costs)
│  ├─ token_economy (compression status)
│  └─ currency_meta (forex rate, source)
│
└─ Pricing Data (pricing_manager)
   ├─ Store per-model pricing
   ├─ Update forex rates (ForexService)
   └─ Calculate multi-currency costs (USD, IDR)
```

---

## 7. LLM Integration Flow

### ThoughtGenerationService Flow

```
┌─────────────────────────────────────────────────────────────┐
│         ThoughtGenerationService LLM Integration Flow         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Intelligent Model Selection                               │
│     ┌─────────────────────────────────────────────────┐      │
│     │ ModelSelectionStrategy.select_model()            │      │
│     │ - Build CognitiveTaskContext                    │      │
│     │ - Analyze: complexity, requires_reasoning,      │      │
│     │            requires_code, token_estimate         │      │
│     │ - Select provider/model based on cost-performance│      │
│     │ - Return: provider, model, depth, estimated_cost  │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  2. Provider Routing                                       │
│     ┌─────────────────────────────────────────────────┐      │
│     │ if provider == "gemini":                        │      │
│     │   - Call _call_gemini(prompt, system_prompt)   │      │
│     │ elif provider == "openai":                      │      │
│     │   - Call _call_openai(prompt, system_prompt)    │      │
│     │ elif provider == "anthropic":                    │      │
│     │   - Call _call_anthropic(prompt, system_prompt)│      │
│     │ elif provider == "ollama":                      │      │
│     │   - Call _call_ollama(prompt, system_prompt)    │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  3. API Call (Example: Gemini)                            │
│     ┌─────────────────────────────────────────────────┐      │
│     │ _call_gemini(prompt, system_prompt)             │      │
│     │ - Use default_model or gemini-flash-latest     │      │
│     │ - Strip 'models/' path if present               │      │
│     │ - Construct URL:                                 │      │
│     │   https://generativelanguage.googleapis.com/v1beta│      │
│     │   /models/{model_id}:generateContent?key={key}  │      │
│     │ - Build payload with contents and generationConfig│      │
│     │ - Add system_instruction if provided             │      │
│     │ - Send POST request with httpx.AsyncClient      │      │
│     │ - Handle timeout (60.0s connect, 10.0s)        │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  4. Response Processing                                   │
│     ┌─────────────────────────────────────────────────┐      │
│     │ - Parse JSON response                           │      │
│     │ - Extract generated text from response           │      │
│     │ - Handle errors gracefully                      │      │
│     │ - Return fallback error message on failure       │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  5. Restore Original Model                                  │
│     ┌─────────────────────────────────────────────────┐      │
│     │ - Restore settings.default_model                │      │
│     │ - Ensure state consistency for next call         │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  6. Return Generated Thought                               │
│     ┌─────────────────────────────────────────────────┐      │
│     │ Return: generated thought text string            │      │
│     └─────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Model Selection Strategy

**Supported Providers:**
- Gemini (Google AI Studio)
- OpenAI
- Anthropic
- Ollama (local)

**Selection Criteria:**
```python
CognitiveTaskContext(
    complexity="moderate",
    requires_reasoning=True,
    requires_code=False,
    token_estimate=700,
    latency_preference="balanced"
)

ModelSelection returns:
- provider: "gemini"
- model: "gemini-1.5-flash"
- depth: ModelDepth.EFFICIENCY
- estimated_cost_per_1k: $0.0001
```

### API Call Example (Gemini)

**Request Payload:**
```python
{
    "contents": [{
        "parts": [{"text": "Analyze microservices architecture..."}]
    }],
    "generationConfig": {
        "temperature": 0.3,
        "topP": 0.8,
        "topK": 40
    },
    "system_instruction": {
        "parts": [{"text": "You are a cognitive architect..."}]
    }
}
```

**Response Processing:**
```python
# Extract from response
candidates[0]["content"]["parts"][0]["text"]

# Token counting and cost calculation
- Input tokens: counted from request
- Output tokens: counted from response
- Cost: calculated via pricing_manager
- Currency: USD and IDR (via ForexService)
```

---

## Error Handling Flow

### Error Propagation

```
Error Handling Flow
│
├─ Input Validation Errors
│  ├─ Return error response to client
│  ├─ Include error message
│  └─ Suggest corrective action
│
├─ LLM API Errors
│  ├─ Retry with exponential backoff
│  ├─ Fallback to guided mode
│  └─ Log error for monitoring
│
├─ Database Errors
│  ├─ Retry operation
│  ├─ Use in-memory fallback
│  └─ Alert administrator
│
├─ Mode Execution Errors
│  ├─ Fallback to default mode
│  ├─ Log error details
│  └─ Continue with degraded functionality
│
└─ System Errors
   ├─ Graceful degradation
   ├─ Return safe default response
   └─ Trigger alert for investigation
```

---

## Summary

**Key Data Flow Patterns**:
1. **Request Processing**: Client → Transport → Server → Orchestrator → Response
2. **Cognitive Workflow**: Input → Mode Selection → Context → Processing → Analysis → Storage
3. **Session Lifecycle**: Creation → Processing → Termination → Export
4. **Persistence**: Database Operations → Transaction Management → Usage Tracking
5. **LLM Integration**: Prompt → API Call → Response → Post-Processing

**Data Transformations**:
- Raw input → Validated parameters
- Problem statement → Cognitive context
- LLM response → Enhanced thought
- Thought → Scored metrics
- Session data → Export format

**Error Handling**:
- Validation errors at input layer
- Retry logic for transient failures
- Graceful degradation for system errors
- Comprehensive logging for monitoring
