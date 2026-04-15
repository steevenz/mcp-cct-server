# System Architecture Overview

This document provides a high-level architectural overview of the CCT MCP Server, including system components, data flow, and key design patterns.

## Table of Contents
1. [Architecture Philosophy](#architecture-philosophy)
2. [System Components](#system-components)
3. [Layered Architecture](#layered-architecture)
4. [Component Interactions](#component-interactions)
5. [Transport Modes](#transport-modes)
6. [Design Patterns](#design-patterns)

---

## Architecture Philosophy

The CCT MCP Server follows **Domain-Driven Design (DDD)** principles with a focus on:
- **Separation of Concerns**: Clear boundaries between domain, application, and infrastructure layers
- **Cognitive Pipeline Architecture**: Sequential thought processing with strategic mode selection
- **Fusion-Based Orchestration**: Multiple cognitive strategies working in concert
- **Multi-Agent Support**: Shared server architecture for concurrent AI agent interactions
- **Transport Flexibility**: Support for both stdio and SSE (Server-Sent Events) transport modes

---

## System Components

### Core Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                    CCT MCP Server                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Entry Point (main.py)                      │ │
│  │  - Bootstrap system components                          │ │
│  │  - Initialize FastAPI/FastMCP server                    │ │
│  │  - Register MCP tools                                   │ │
│  │  - Handle transport mode (stdio/SSE)                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │         Cognitive Orchestrator (Master Controller)      │ │
│  │  - Session lifecycle management                         │ │
│  │  - Mode selection and routing                           │ │
│  │  - Thought processing coordination                      │ │
│  │  - Integration with all engines                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                                │
│  ┌──────────────┬──────────────┬──────────────┬─────────────┐ │
│  │ Memory       │ Sequential    │ Fusion        │ Analysis    │ │
│  │ Engine       │ Engine       │ Orchestrator  │ Engine     │ │
│  │              │              │              │             │ │
│  │ - Sessions   │ - Thoughts   │ - Multi-mode  │ - Scoring  │ │
│  │ - Thoughts   │ - Context    │ - Consensus   │ - Bias     │ │
│  │ - Patterns   │ - History    │ - Synthesis   │ - Quality  │ │
│  └──────────────┴──────────────┴──────────────┴─────────────┘ │
│                              │                                │
│  ┌──────────────┬──────────────┬──────────────┬─────────────┐ │
│  │ Modes        │ Services     │ Tools        │ Utils       │ │
│  │              │              │              │             │ │
│  │ - Primitives │ - Identity   │ - Cognitive  │ - Pricing   │ │
│  │ - Hybrids    │ - Guidance   │ - Export     │ - Forex     │ │
│  │ - Registry   │ - Autonomous │ - Session    │             │ │
│  │              │ - LLM Client │              │             │ │
│  └──────────────┴──────────────┴──────────────┴─────────────┘ │
│                              │                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Core Configuration & Models                │ │
│  │  - Settings (config.py)                                 │ │
│  │  - Domain models (models/)                              │ │
│  │  - Enums (enums.py)                                     │ │
│  │  - Security (security.py)                                │ │
│  │  - Rate limiter (rate_limiter.py)                        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Data Persistence                           │ │
│  │  - SQLite database (aiosqlite)                          │ │
│  │  - Thinking patterns archive                            │ │
│  │  - Session history                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

**Entry Point (`main.py`)**
- System bootstrap and component initialization
- FastAPI/FastMCP server configuration
- Transport mode handling (stdio/SSE)
- MCP tool registration
- Health and status endpoints

**Cognitive Orchestrator (`engines/orchestrator.py`)**
- Master controller for cognitive workflows
- Session lifecycle management
- Mode selection and routing via IntelligenceRouter
- Coordination of all cognitive engines
- Integration with Memory, Sequential, Fusion, and Analysis engines

**Memory Engine (`engines/memory/`)**
- `manager.py`: SQLite persistence with JSON blob storage (sessions, thoughts, patterns, anti_patterns)
- `thinking_patterns.py`: Pattern archiving and retrieval (GoldenThinkingPattern)
- `pattern_injector.py`: Pattern injection for learning
- Thread-safe with WAL mode and write lock for concurrent operations

**Sequential Engine (`engines/sequential/`)**
- Thought-by-thought processing
- Context management and history tracking
- Sequential context building

**Fusion Orchestrator (`engines/fusion/`)**
- Multi-mode cognitive processing
- Consensus building across modes
- Synthesis generation from multiple perspectives

**Analysis Engine (`analysis/`)**
- `scoring_engine.py`: Thought quality scoring (ScoringEngine, IncrementalSessionAnalyzer)
- `bias.py`: Bias detection and analysis
- `quality.py`: Quality assessment
- `summarization.py`: Text summarization and compression (compress_session_context)

**Cognitive Modes (`modes/`)**
- `base.py`: Base cognitive engine interface
- `primitives/`: Fundamental cognitive strategies
- `hybrids/`: Advanced multi-strategy modes
- `registry.py`: Mode registration and management

**Services (`core/services/`)**
- `identity.py`: Identity and persona management (IdentityService)
- `guidance.py`: Cognitive guidance and direction (GuidanceService)
- `autonomous.py`: Autonomous decision-making (AutonomousService)
- `llm/client.py`: LLM integration with intelligent model selection (ThoughtGenerationService)
- `llm/critic.py`: Adversarial review service (AdversarialReviewService)
- `llm/router.py`: Model selection strategy (ModelSelectionStrategy)
- `digital_hippocampus.py`: Learning and adaptation (DigitalHippocampus)
- `internal_clearance.py`: Internal security clearance (InternalClearanceService)
- `routing.py`: Intelligence routing (IntelligenceRouter)
- `pipeline_policy.py`: Pipeline selection (PipelineSelector)
- `complexity.py`: Task complexity detection (ComplexityService)

**MCP Tools (`tools/`)**
- `simplified_tools.py`: Main MCP tools (thinking, rethinking, list_thinking, branches)
- `export_tools.py`: Export and analysis tools (export_thinking_session, analyze_session)
- `session_tools.py`: Session management tools (health_check)

---

## Layered Architecture

### Domain Layer (`src/core/models/`)

**Purpose**: Core business entities and rules

**Components**:
- `domain.py`: Domain models (EnhancedThought, CCTSessionState, ThoughtMetrics)
- `enums.py`: Enums (ThinkingStrategy, ThoughtType, CCTProfile, SessionStatus)
- `contexts.py`: Context models (SequentialContext, CognitiveTaskContext)
- `schemas.py`: Pydantic schemas for validation
- `identity_defaults.py`: Identity constants and defaults

**Responsibilities**:
- Define core business entities
- Enforce business rules
- Provide type safety
- No external dependencies

### Application Layer (`src/core/services/`, `src/modes/`, `src/engines/orchestrator.py`)

**Purpose**: Application logic and orchestration

**Components**:
- `services/`: Application services (Identity, Guidance, Autonomous, etc.)
- `modes/`: Cognitive modes (Primitives, Hybrids, Registry)
- `engines/orchestrator.py`: Main application orchestrator

**Responsibilities**:
- Coordinate domain objects
- Implement business workflows
- Handle use cases
- Orchestrate cognitive processes

### Infrastructure Layer (`src/tools/`, `src/utils/`, `src/analysis/`, `src/engines/memory/`, `src/engines/sequential/`)

**Purpose**: External integrations and technical concerns

**Components**:
- `tools/`: MCP tool implementations
- `utils/`: Utility services (Pricing, Forex)
- `analysis/`: Analysis engines (Scoring, Bias, Quality)
- `engines/memory/`: Memory infrastructure
- `engines/sequential/`: Sequential processing infrastructure

**Responsibilities**:
- External API integrations
- Data persistence
- Utility functions
- Technical implementations

---

## Component Interactions

### Request Flow (MCP Tool Call)

```
┌─────────────┐
│   Client    │
│  (IDE/Agent)│
└──────┬──────┘
       │
       │ 1. MCP Tool Call (thinking/rethinking/etc.)
       ▼
┌─────────────────────────────────────────┐
│         FastAPI/FastMCP Server          │
│  - Receives MCP request                 │
│  - Routes to appropriate tool          │
└──────┬──────────────────────────────────┘
       │
       │ 2. Tool Execution (simplified_tools.py)
       ▼
┌─────────────────────────────────────────┐
│         Cognitive Orchestrator          │
│  - Validates session                    │
│  - execute_strategy(session, strategy,  │
│                     payload)            │
│  - HITL enforcement check               │
│  - Context compression (token economy)  │
└──────┬──────────────────────────────────┘
       │
       │ 3. Engine Selection (Registry)
       ▼
┌─────────────────────────────────────────┐
│      CognitiveEngineRegistry            │
│  - get_engine(strategy)               │
│  - Maps strategy to engine:            │
│    • Primitives → DynamicPrimitiveEngine│
│    • Hybrids → Specific hybrid engine   │
│    • Multi-agent → MultiAgentFusionEngine│
└──────┬──────────────────────────────────┘
       │
       │ 4. Engine Execution
       ▼
┌─────────────────────────────────────────┐
│      Selected Cognitive Engine          │
│  - execute(session_id, payload)        │
│  - SequentialEngine.process_sequence() │
│  - ScoringEngine.analyze_thought()     │
│  - PatternArchiver.archive_thought()    │
│  - MemoryManager.add_thought()         │
└──────┬──────────────────────────────────┘
       │
       │ 5. Usage Tracking & HITL
       ▼
┌─────────────────────────────────────────┐
│      CognitiveOrchestrator             │
│  - Update session totals               │
│  - Archive elite thoughts              │
│  - HITL trigger if converged           │
└──────┬──────────────────────────────────┘
       │
       │ 6. Response
       ▼
┌─────────────────────────────────────────┐
│         MCP Response                   │
│  - Returns thought result              │
│  - Includes usage metrics              │
│  - Includes HITL instructions (if applicable)│
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Client    │
└─────────────┘
```

### Session Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Session Lifecycle                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Session Creation (thinking tool)                        │
│     ┌─────────────────────────────────────────────────┐      │
│     │ thinking(problem_statement, llm_model_name,     │      │
│     │          profile, estimated_thoughts)          │      │
│     │ - Validates problem statement                   │      │
│     │ - Detects complexity and category               │      │
│     │ - Creates session in memory (SQLite)            │      │
│     │ - Selects initial strategy from pipeline        │      │
│     │ - Executes first thinking step                  │      │
│     │ - Returns session_id, strategy_used, result    │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  2. Cognitive Processing (rethinking tool)                   │
│     ┌─────────────────────────────────────────────────┐      │
│     │ rethinking(session_id, thought_content,         │      │
│     │            thought_number, strategy)           │      │
│     │ - Validates session_id and content              │      │
│     │ - Selects strategy (auto or specified)          │      │
│     │ - Orchestrator.execute_strategy()               │      │
│     │ - CognitiveEngineRegistry.get_engine()         │      │
│     │ - Engine.execute()                             │      │
│     │ - Stores thought in memory                      │      │
│     │ - Returns thought result with usage metrics     │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  3. Sequential Processing                                   │
│     ┌─────────────────────────────────────────────────┐      │
│     │ Multiple rethinking() calls                     │      │
│     │ - SequentialEngine.process_sequence_step()      │      │
│     │ - Builds sequential context                      │      │
│     │ - Maintains thought history                      │      │
│     │ - Updates session state                          │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  4. Session Export (export_thinking_session tool)            │
│     ┌─────────────────────────────────────────────────┐      │
│     │ export_thinking_session(session_id,             │      │
│     │                       session_token)             │      │
│     │ - Validates session ownership via token         │      │
│     │ - Retrieves session history                     │      │
│     │ - Returns all thoughts in JSON format           │      │
│     └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  5. Session Analysis (analyze_session tool)                 │
│     ┌─────────────────────────────────────────────────┐      │
│     │ analyze_session(session_id, session_token)       │      │
│     │ - Validates session ownership via token         │      │
│     │ - IncrementalSessionAnalyzer processes thoughts  │      │
│     │ - Returns quality metrics (clarity, bias, etc.)  │      │
│     └─────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Transport Modes

### stdio Mode

**Use Case**: Direct IDE integration, single-agent usage

**Flow**:
```
IDE ←→ stdio ←→ FastMCP ←→ Cognitive Orchestrator ←→ Cognitive Engines
```

**Characteristics**:
- Standard input/output communication
- Single client connection
- Lower latency
- Simple setup

### SSE Mode (Server-Sent Events)

**Use Case**: Multi-agent, multi-IDE, HTTP-based communication

**Flow**:
```
IDE/Agent ←→ HTTP/SSE ←→ FastAPI ←→ FastMCP ←→ Cognitive Orchestrator ←→ Cognitive Engines
```

**Characteristics**:
- HTTP-based communication
- Multiple concurrent connections
- Network-based
- Requires host/port configuration
- Suitable for multi-agent scenarios

---

## Design Patterns

### 1. Strategy Pattern

**Location**: `src/modes/`

**Purpose**: Encapsulate cognitive strategies as interchangeable algorithms

**Implementation**:
- `base.py`: Base cognitive engine interface
- `primitives/`: Concrete strategy implementations
- `registry.py`: Strategy selection and management

**Example**:
```python
# Different cognitive strategies can be swapped
mode = registry.get_mode("actor_critic")
result = mode.process(problem_statement)
```

### 2. Orchestrator Pattern

**Location**: `src/engines/orchestrator.py`, `src/engines/fusion/orchestrator.py`

**Purpose**: Coordinate multiple components to achieve complex workflows

**Implementation**:
- `CognitiveOrchestrator`: Master controller
- `FusionOrchestrator`: Multi-mode coordination

**Example**:
```python
orchestrator = CognitiveOrchestrator(
    memory_manager=memory,
    sequential_engine=sequential,
    registry=registry,
    fusion_engine=fusion,
    router=router
)
```

### 3. Repository Pattern

**Location**: `src/engines/memory/manager.py`

**Purpose**: Abstract data access logic

**Implementation**:
- `MemoryManager`: Session and thought persistence
- SQLite as backing store
- CRUD operations for domain objects

### 4. Factory Pattern

**Location**: `src/modes/registry.py`

**Purpose**: Create cognitive mode instances

**Implementation**:
- `CognitiveEngineRegistry`: Mode factory
- Dynamic mode instantiation based on configuration

### 5. Service Layer Pattern

**Location**: `src/core/services/`

**Purpose**: Encapsulate application logic

**Implementation**:
- `IdentityService`: Identity management
- `GuidanceService`: Cognitive guidance
- `AutonomousService`: Autonomous decision-making
- `ThoughtGenerationService`: LLM integration

### 6. Dependency Injection

**Location**: `src/main.py` (bootstrap function)

**Purpose**: Inject dependencies into components

**Implementation**:
- All components initialized in bootstrap
- Dependencies passed via constructor
- Loose coupling between components

---

## Key Architectural Decisions

### 1. DDD-Aligned Structure

**Rationale**: Clear separation of concerns, maintainability

**Impact**:
- Domain models isolated from infrastructure
- Application logic separated from technical concerns
- Easier testing and evolution

### 2. Multi-Mode Cognitive Processing

**Rationale**: Different problems require different cognitive approaches

**Impact**:
- Flexible cognitive strategy selection
- Fusion of multiple perspectives
- Improved problem-solving capabilities

### 3. SQLite for Persistence

**Rationale**: Simple, reliable, no external dependencies

**Impact**:
- Easy deployment
- Zero configuration
- Sufficient for current scale

### 4. FastMCP as Protocol Layer

**Rationale**: Standard MCP protocol implementation

**Impact**:
- IDE compatibility
- Multi-agent support
- Standardized tool interface

### 5. Transport Flexibility

**Rationale**: Support different deployment scenarios

**Impact**:
- stdio for direct IDE integration
- SSE for multi-agent/multi-IDE scenarios
- Future-proofing for additional transports

---

## Technology Stack

### Core Framework
- **FastMCP**: MCP protocol implementation
- **FastAPI**: HTTP server (SSE mode)
- **Uvicorn**: ASGI server

### Data Persistence
- **SQLite**: Primary database (aiosqlite for async)
- **Pydantic**: Data validation and serialization

### Analysis & NLP
- **scikit-learn**: Machine learning utilities
- **sentence-transformers**: Text embeddings
- **textstat**: Text statistics
- **numpy**: Numerical computing

### LLM Integration
- **OpenAI**: GPT models
- **Anthropic**: Claude models
- **Google**: Gemini models
- **Ollama**: Local models

### Utilities
- **python-dotenv**: Environment configuration
- **httpx/aiohttp**: HTTP clients
- **colorama**: Terminal colors

---

## Performance Considerations

### Scalability
- Multi-agent support via SSE transport
- Rate limiting for resource management
- Session limits to prevent memory exhaustion

### Optimization
- In-memory caching for frequent operations
- Async I/O for database operations
- Efficient thought pattern archiving

### Resource Management
- Session cleanup and expiration
- Database connection pooling
- Memory usage monitoring

---

## Security Considerations

### Authentication
- API key protection for dashboard endpoints
- Session tokens for session ownership
- Internal clearance for sensitive operations

### Authorization
- Session ownership validation
- HITL (Human-in-the-Loop) authorization
- Role-based access control

### Data Protection
- Secure token generation
- Input validation and sanitization
- SQL injection prevention (parameterized queries)

---

## Future Architectural Considerations

### Potential Enhancements
- **PostgreSQL**: For larger scale deployments
- **Redis**: For caching and session management
- **Message Queue**: For async task processing
- **Microservices**: For component isolation and scaling

### Extension Points
- Custom cognitive modes via registry
- Additional LLM providers via service interface
- Custom analysis engines via plugin system
- Alternative storage backends via repository pattern

---

## Summary

The CCT MCP Server architecture is designed with:
- **Clear separation of concerns** through DDD-aligned layers
- **Flexible cognitive processing** via multi-mode architecture
- **Scalable deployment** via transport mode flexibility
- **Maintainable codebase** through proven design patterns
- **Extensible system** through registry and service patterns

The architecture supports both simple single-agent use cases and complex multi-agent scenarios while maintaining code quality and system reliability.
