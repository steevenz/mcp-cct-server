# Component Architecture

This document provides detailed documentation of each component in the CCT MCP Server architecture, including responsibilities, interfaces, and interactions.

## Table of Contents
1. [Entry Point](#1-entry-point)
2. [Core Components](#2-core-components)
3. [Cognitive Engines](#3-cognitive-engines)
4. [Cognitive Modes](#4-cognitive-modes)
5. [Services](#5-services)
6. [Tools](#6-tools)
7. [Analysis Components](#7-analysis-components)
8. [Utilities](#8-utilities)

---

## 1. Entry Point

### main.py

**Location**: `src/main.py`

**Purpose**: System bootstrap and server initialization

**Responsibilities**:
- Bootstraps all system components
- Initializes FastAPI/FastMCP server
- Registers MCP tools
- Handles transport mode selection (stdio/SSE)
- Provides health and status endpoints

**Key Functions**:
```python
def bootstrap() -> dict[str, object]:
    """Bootstraps the dependencies and initializes the central orchestrator."""
    
def main():
    """Main entry point - starts server based on transport mode."""
```

**Component Initialization Order**:
1. Load settings from environment
2. Initialize MemoryManager
3. Initialize SequentialEngine
4. Initialize ScoringEngine
5. Initialize services (Complexity, Guidance, Autonomous, ThoughtGeneration, Identity)
6. Initialize DigitalHippocampus
7. Initialize FusionOrchestrator
8. Initialize IntelligenceRouter
9. Initialize CognitiveEngineRegistry
10. Initialize CognitiveOrchestrator (master controller)

**Dependencies**:
- `src.core.config`: Settings configuration
- `src.engines.memory.manager`: Memory management
- `src.engines.sequential.engine`: Sequential processing
- `src.analysis.scoring_engine`: Scoring and metrics
- `src.engines.fusion.orchestrator`: Multi-mode coordination
- `src.core.services.routing`: Intelligence routing
- `src.modes.registry`: Cognitive mode registry
- `src.engines.orchestrator`: Master orchestrator
- `src.tools.simplified_tools`: MCP tools
- `src.tools.export_tools`: Export tools

---

## 2. Core Components

### Configuration (config.py)

**Location**: `src/core/config.py`

**Purpose**: Centralized configuration management

**Key Class**:
```python
@dataclass(frozen=True, slots=True)
class Settings:
    server_name: str
    transport: str
    host: str
    port: int
    max_sessions: int
    log_level: str
    db_path: str
    pricing_path: str
    default_model: str
    dashboard_api_key: str
    mcp_secret: str | None
    max_thoughts: int
    max_content_length: int
    max_context_tokens: int
    context_strategy: str
    tp_threshold: float
    forex_cache_ttl: int
    forex_default_rate: float
    forex_api_url: str
    enabled_tool_groups: set[str]
    llm_provider: str | None
    openai_api_key: str | None
    anthropic_api_key: str | None
    gemini_api_key: str | None
    ollama_base_url: str | None
    critic_llm_api_url: str | None
    critic_model: str | None
    critic_api_key: str | None
    critic_provider: str | None
```

**Key Function**:
```python
def load_settings() -> Settings:
    """Load settings from environment variables with validation."""
```

**Environment Variables**:
- Server configuration: `CCT_SERVER_NAME`, `CCT_TRANSPORT`, `CCT_HOST`, `CCT_PORT`
- Session limits: `CCT_MAX_SESSIONS`, `CCT_MAX_THOUGHTS`
- Database: `CCT_DB_PATH`, `CCT_PRICING_PATH`
- LLM providers: `CCT_LLM_PROVIDER`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
- User preferences: `CCT_DEFAULT_MODEL`, `CCT_LOG_LEVEL`, `CCT_MAX_CONTENT_LENGTH`

### Domain Models (core/models/)

**Location**: `src/core/models/`

**Purpose**: Core business entities and data structures

#### domain.py
**Key Classes**:
```python
class EnhancedThought(BaseModel):
    """Enhanced thought with metrics and context."""
    id: str
    session_id: str
    content: str
    thought_type: ThoughtType
    strategy: ThinkingStrategy
    sequential_context: SequentialContext
    summary: str
    metrics: ThoughtMetrics
    tags: list[str]
    timestamp: datetime

class CCTSessionState(BaseModel):
    """Cognitive session state."""
    session_id: str
    problem_statement: str
    profile: CCTProfile
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    estimated_total_thoughts: int
    current_thought_number: int
    model_id: str
    complexity: str
    primary_category: str
    detected_categories: dict[str, float]
    suggested_pipeline: list[str]
    history_ids: list[str]
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float
    total_cost_idr: float

class ThoughtMetrics(BaseModel):
    """Thought quality metrics."""
    logical_coherence: float
    evidence_strength: float
    clarity_score: float
    novelty_score: float
    depth_score: float
```

#### enums.py
**Key Enums**:
```python
class ThinkingStrategy(str, Enum):
    LINEAR = "linear"
    ANALYTICAL = "analytical"
    EMPIRICAL_RESEARCH = "empirical_research"
    FIRST_PRINCIPLES = "first_principles"
    SYSTEMIC = "systemic"
    INTEGRATIVE = "integrative"
    ACTOR_CRITIC_LOOP = "actor_critic_loop"
    COUNCIL_OF_CRITICS = "council_of_critics"
    UNCONVENTIONAL_PIVOT = "unconventional_pivot"
    LONG_TERM_HORIZON = "long_term_horizon"
    MULTI_AGENT_FUSION = "multi_agent_fusion"

class ThoughtType(str, Enum):
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"
    REFLECTION = "reflection"

class CCTProfile(str, Enum):
    CREATIVE_FIRST = "creative"
    CRITICAL_FIRST = "critical"
    BALANCED = "balanced"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    DEEP_RECURSIVE = "deep_recursive"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    STOPPED = "stopped"
```

#### contexts.py
**Key Classes**:
```python
class SequentialContext(BaseModel):
    """Context for sequential thought processing."""
    thought_number: int
    estimated_total_thoughts: int
    previous_thoughts: list[str]
    current_focus: str

class CognitiveTaskContext(BaseModel):
    """Context for cognitive task execution."""
    problem_statement: str
    profile: CCTProfile
    constraints: dict[str, Any]
```

### Security (security.py)

**Location**: `src/core/security.py`

**Purpose**: Security utilities for token generation and validation

**Key Functions**:
```python
def generate_token() -> str:
    """Generate a secure random token."""
    
def hash_token(token: str) -> str:
    """Hash a token using SHA-256."""
    
def verify_token(token: str, hashed: str) -> bool:
    """Verify a token against its hash."""
    
def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent injection attacks."""
```

### Validators (validators.py)

**Location**: `src/core/validators.py`

**Purpose**: Input validation and sanitization

**Key Functions**:
```python
def validate_session_id(session_id: str) -> str | None:
    """Validate session ID format."""
    
def validate_problem_statement(problem_statement: str) -> str | None:
    """Validate problem statement content."""
    
def validate_transport_mode(transport: str) -> str | None:
    """Validate transport mode (stdio/sse)."""
```

### Rate Limiter (rate_limiter.py)

**Location**: `src/core/rate_limiter.py`

**Purpose**: Rate limiting for API calls and resource management

**Key Classes**:
```python
@dataclass
class RateLimiterConfig:
    window_seconds: int
    max_requests: int

class RateLimiter:
    """Token bucket rate limiter."""
    
    def is_allowed(self) -> bool:
        """Check if request is allowed."""
    
    def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics."""
```

---

## 3. Cognitive Engines

### Memory Manager (engines/memory/manager.py)

**Location**: `src/engines/memory/manager.py`

**Purpose**: Session and thought persistence with SQLite backend

**Key Class**:
```python
class MemoryManager:
    """Manages cognitive sessions and thought persistence."""
    
    def create_session(
        self,
        problem_statement: str,
        profile: CCTProfile,
        estimated_thoughts: int,
        model_id: str = ""
    ) -> CCTSessionState:
        """Create a new cognitive session."""
    
    def get_session(self, session_id: str) -> CCTSessionState | None:
        """Retrieve session by ID."""
    
    def add_thought(self, thought: EnhancedThought) -> None:
        """Store a thought in the database."""
    
    def get_thought(self, thought_id: str) -> EnhancedThought | None:
        """Retrieve thought by ID."""
    
    def list_sessions(self) -> list[str]:
        """List all active session IDs."""
    
    def get_session_history(self, session_id: str) -> list[EnhancedThought]:
        """Get complete thought history for a session."""
    
    def validate_session_token(self, session_id: str, token: str) -> bool:
        """Validate session ownership via token."""
    
    def get_aggregate_usage(self) -> dict[str, Any]:
        """Get aggregate usage statistics (tokens, costs, sessions)."""
```

**Database Schema (SQLite with JSON blobs)**:
- `sessions` table: session_id (PK), data (JSON blob with CCTSessionState)
- `thoughts` table: thought_id (PK), session_id (FK), data (JSON blob with EnhancedThought)
- `thinking_patterns` table: tp_id (PK), thought_id, usage_count, data (JSON blob)
- `anti_patterns` table: failure_id (PK), thought_id, failed_strategy, category, data (JSON blob)

**Thread Safety**: WAL mode enabled with write lock for concurrent operations

### Sequential Engine (engines/sequential/engine.py)

**Location**: `src/engines/sequential/engine.py`

**Purpose**: Sequential thought processing and context management

**Key Class**:
```python
class SequentialEngine:
    """Processes thoughts sequentially with context management."""
    
    def process_sequence_step(
        self,
        session_id: str,
        llm_thought_number: int,
        llm_estimated_total: int,
        next_thought_needed: bool,
        is_revision: bool = False,
        revises_id: Optional[str] = None,
        branch_from_id: Optional[str] = None,
        branch_id: Optional[str] = None
    ) -> SequentialContext:
        """Process a single sequence step with context."""
    
    def evaluate_convergence(
        self,
        session_id: str
    ) -> bool:
        """Evaluate if session has converged."""
```

### Fusion Orchestrator (engines/fusion/orchestrator.py)

**Location**: `src/engines/fusion/orchestrator.py`

**Purpose**: Multi-mode cognitive processing and consensus building

**Key Class**:
```python
class FusionOrchestrator:
    """Orchestrates multiple cognitive modes for fusion processing."""
    
    def __init__(
        self,
        memory: MemoryManager,
        scoring: ScoringEngine,
        sequential: SequentialEngine,
        orchestration: AutonomousService,
        thought_service: ThoughtGenerationService,
        guidance: GuidanceService,
        identity: IdentityService
    ):
        """Initialize with required services."""
    
    async def fuse_thoughts(
        self,
        session_id: str,
        thought_ids: List[str],
        synthesis_goal: str,
        model_id: str,
        model_tier: str = "efficiency"
    ) -> EnhancedThought:
        """Synthesize multiple thoughts into unified conclusion."""
    
    def _determine_mode(
        self,
        session_id: str
    ) -> str:
        """Determine synthesis mode based on context."""
```

### Cognitive Orchestrator (engines/orchestrator.py)

**Location**: `src/engines/orchestrator.py`

**Purpose**: Master controller for cognitive workflows

**Key Class**:
```python
class CognitiveOrchestrator:
    """Master controller for cognitive workflows."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        sequential_engine: SequentialEngine,
        registry: CognitiveEngineRegistry,
        fusion_engine: FusionOrchestrator,
        router: IntelligenceRouter,
        identity: IdentityService,
        autonomous: AutonomousService,
        internal_clearance: Optional[InternalClearanceService] = None
    ):
        """Initialize with all required components."""
    
    async def execute_strategy(
        self,
        session_id: str,
        strategy: ThinkingStrategy,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a cognitive strategy for a session."""
    
    def check_and_pivot(
        self,
        session_id: str
    ) -> bool:
        """Check if strategy needs to pivot based on feedback."""
    
    @property
    def memory(self) -> MemoryManager:
        """Get memory manager instance."""
```

---

## 4. Cognitive Modes

### Base Mode (modes/base.py)

**Location**: `src/modes/base.py`

**Purpose**: Base interface for all cognitive modes

**Key Class**:
```python
class CognitiveEngine(ABC):
    """Base class for all cognitive engines."""
    
    @abstractmethod
    def process(
        self,
        problem: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a problem using this cognitive strategy."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this cognitive mode."""
    
    @abstractmethod
    def get_description(self) -> str:
        """Get a description of this cognitive mode."""
```

### Primitives (modes/primitives/)

**Location**: `src/modes/primitives/`

**Purpose**: Fundamental cognitive strategies

#### orchestrator.py
**Key Class**:
```python
class DynamicPrimitiveEngine(CognitiveEngine):
    """Dynamic primitive strategy engine."""
    
    def process(
        self,
        problem: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process using dynamic primitive selection."""
```

**Available Primitives**:
- Systematic analysis
- Creative brainstorming
- Critical evaluation
- Divergent thinking
- Convergent thinking

### Hybrids (modes/hybrids/)

**Location**: `src/modes/hybrids/`

**Purpose**: Advanced multi-strategy cognitive modes

#### actor_critic/
**Key Class**:
```python
class ActorCriticEngine(CognitiveEngine):
    """Actor-Critic cognitive mode for iterative refinement."""
    
    def process(
        self,
        problem: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process using actor-critic loop."""
```

#### council_of_critics/
**Key Class**:
```python
class CouncilOfCriticsEngine(CognitiveEngine):
    """Council of Critics mode for multi-perspective analysis."""
    
    def process(
        self,
        problem: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process using council of critics approach."""
```

#### lateral/
**Key Class**:
```python
class LateralPivotEngine(CognitiveEngine):
    """Lateral pivot mode for unconventional thinking."""
    
    def process(
        self,
        problem: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process using lateral thinking and paradigm shifts."""
```

#### multi_agent/
**Key Class**:
```python
class MultiAgentFusionEngine(CognitiveEngine):
    """Multi-agent fusion mode for collaborative processing."""
    
    def process(
        self,
        problem: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process using multi-agent fusion."""
```

#### temporal/
**Key Class**:
```python
class LongTermHorizonEngine(CognitiveEngine):
    """Long-term horizon mode for temporal planning."""
    
    def process(
        self,
        problem: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process using long-term horizon planning."""
```

### CognitiveEngineRegistry (modes/registry.py)

**Location**: `src/modes/registry.py`

**Purpose**: Strategy-to-engine mapping for cognitive processing

**Key Class**:
```python
class CognitiveEngineRegistry:
    """Registry mapping ThinkingStrategy to cognitive engines."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        sequential_engine: SequentialEngine,
        fusion_orchestrator: FusionOrchestrator,
        autonomous: AutonomousService,
        thought_service: ThoughtGenerationService,
        guidance: GuidanceService,
        identity: IdentityService,
        scoring_engine: ScoringEngine,
        review_service: AdversarialReviewService = None
    ):
        """Initialize with required services."""
    
    def _initialize_registry(self) -> None:
        """Initialize registry with hybrid engines and dynamic primitives."""
    
    def get_engine(self, strategy: ThinkingStrategy) -> BaseCognitiveEngine | None:
        """Get engine instance for a strategy."""
    
    @property
    def strategy_type(self) -> ThinkingStrategy:
        """Get strategy type."""
```

**Strategy Mapping**:
- Primitive strategies → DynamicPrimitiveEngine (dynamic factory)
- MULTI_AGENT_FUSION → MultiAgentFusionEngine
- ACTOR_CRITIC_LOOP → ActorCriticEngine
- COUNCIL_OF_CRITICS → CouncilOfCriticsEngine
- UNCONVENTIONAL_PIVOT → LateralEngine
- LONG_TERM_HORIZON → LongTermHorizonEngine

---

## 5. Services

### Identity Service (core/services/identity.py)

**Location**: `src/core/services/identity.py`

**Purpose**: Identity and persona management

**Key Class**:
```python
class IdentityService:
    """Manages cognitive identity and persona."""
    
    def __init__(self, digital_hippocampus: Optional[DigitalHippocampus] = None):
        """Initialize with optional digital hippocampus."""
    
    def provision_assets(self) -> None:
        """Provision identity assets from defaults."""
    
    def get_identity(self) -> dict[str, Any]:
        """Get current identity configuration."""
    
    def apply_persona(self, persona: str) -> None:
        """Apply a specific persona to the identity."""
```

### Guidance Service (core/services/guidance.py)

**Location**: `src/core/services/guidance.py`

**Purpose**: Cognitive guidance and direction

**Key Class**:
```python
class GuidanceService:
    """Provides cognitive guidance and direction."""
    
    def get_guidance(
        self,
        problem: str,
        profile: CCTProfile
    ) -> dict[str, Any]:
        """Get guidance for a specific problem."""
    
    def suggest_strategy(
        self,
        problem: str
    ) -> str:
        """Suggest an appropriate cognitive strategy."""
```

### Autonomous Service (core/services/autonomous.py)

**Location**: `src/core/services/autonomous.py`

**Purpose**: Autonomous decision-making and orchestration

**Key Class**:
```python
class AutonomousService:
    """Autonomous decision-making service."""
    
    def __init__(self, settings: Settings, memory_manager: MemoryManager):
        """Initialize with settings and memory manager."""
    
    def orchestrate_task(
        self,
        task: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Orchestrate an autonomous task."""
    
    def get_hitl_status(self, session_id: str) -> dict[str, Any]:
        """Get Human-in-the-Loop status."""
    
    def grant_clearance(
        self,
        session_id: str,
        authorized_by: str,
        note: str
    ) -> dict[str, Any]:
        """Grant human clearance for blocked session."""
```

### Thought Generation Service (core/services/llm/client.py)

**Location**: `src/core/services/llm/client.py`

**Purpose**: LLM integration with intelligent model selection

**Key Class**:
```python
class ThoughtGenerationService:
    """LLM client for thought generation with intelligent model selection."""
    
    def __init__(self, settings: Settings):
        """Initialize with settings."""
    
    async def generate_thought(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        complexity: str = "moderate",
        requires_reasoning: bool = False
    ) -> str:
        """Generate a thought using LLM with intelligent model selection."""
    
    def _call_gemini(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Call Gemini API."""
    
    def _call_openai(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Call OpenAI API."""
    
    def _call_anthropic(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Call Anthropic API."""
    
    def _call_ollama(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Call Ollama API."""
```

**Model Selection Strategy**:
- Intelligent model selection based on CognitiveTaskContext
- Supports: Gemini, OpenAI, Anthropic, Ollama
- Cost-performance optimization via ModelSelectionStrategy

### Adversarial Review Service (core/services/llm/critic.py)

**Location**: `src/core/services/llm/critic.py`

**Purpose**: Adversarial review and quality assurance

**Key Class**:
```python
class AdversarialReviewService:
    """Adversarial review service for thought quality."""
    
    def __init__(self, settings: Settings, identity_service: IdentityService):
        """Initialize with settings and identity service."""
    
    def review_thought(
        self,
        thought: EnhancedThought
    ) -> dict[str, Any]:
        """Review a thought for quality and bias."""
    
    def get_feedback(
        self,
        thought: EnhancedThought
    ) -> str:
        """Get constructive feedback on a thought."""
```

### Digital Hippocampus (core/services/digital_hippocampus.py)

**Location**: `src/core/services/digital_hippocampus.py`

**Purpose**: Learning and adaptation from user patterns

**Key Class**:
```python
class DigitalHippocampus:
    """Digital hippocampus for learning user patterns."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        identity_service: IdentityService
    ):
        """Initialize with memory manager and identity service."""
    
    def learn_pattern(
        self,
        pattern: dict[str, Any]
    ) -> None:
        """Learn a pattern from user behavior."""
    
    def adapt_identity(self) -> None:
        """Adapt identity based on learned patterns."""
    
    def get_learned_patterns(self) -> list[dict[str, Any]]:
        """Get all learned patterns."""
```

### Internal Clearance Service (core/services/internal_clearance.py)

**Location**: `src/core/services/internal_clearance.py`

**Purpose**: Internal security clearance for sensitive operations

**Key Class**:
```python
class InternalClearanceService:
    """Internal clearance service for security checks."""
    
    def __init__(self, scoring_engine: ScoringEngine):
        """Initialize with scoring engine."""
    
    def check_clearance(
        self,
        operation: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Check clearance for an operation."""
    
    def grant_clearance(
        self,
        operation: str,
        level: str
    ) -> None:
        """Grant clearance for an operation."""
```

### Intelligence Router (core/services/routing.py)

**Location**: `src/core/services/routing.py`

**Purpose**: Dynamic mode selection and routing

**Key Class**:
```python
class IntelligenceRouter:
    """Router for dynamic mode selection."""
    
    def __init__(self, scoring_engine: ScoringEngine):
        """Initialize with scoring engine."""
    
    def select_mode(
        self,
        problem: str,
        profile: CCTProfile,
        context: dict[str, Any]
    ) -> str:
        """Select appropriate cognitive mode."""
    
    def get_routing_score(
        self,
        mode: str,
        problem: str
    ) -> float:
        """Get routing score for a mode."""
```

### Complexity Service (core/services/complexity.py)

**Location**: `src/core/services/complexity.py`

**Purpose**: Complexity analysis and assessment

**Key Class**:
```python
class ComplexityService:
    """Service for complexity analysis."""
    
    def detect_complexity(
        self,
        problem: str
    ) -> TaskComplexity:
        """Detect complexity level (SIMPLE, MODERATE, COMPLEX, SOVEREIGN)."""
    
    def get_complexity_level(self) -> str:
        """Get current complexity level."""
```

### Pipeline Selector (core/services/pipeline_policy.py)

**Location**: `src/core/services/pipeline_policy.py`

**Purpose**: Pipeline selection based on complexity and category

**Key Class**:
```python
class PipelineSelector:
    """Pipeline selector for cognitive strategies."""
    
    SOVEREIGN_PIPELINE: list[str] = [...]
    PIPELINE_TEMPLATES: dict[str, list[str]] = {...}
    
    @staticmethod
    def select_pipeline(
        complexity: TaskComplexity
    ) -> list[str]:
        """Select pipeline based on complexity."""
    
    @staticmethod
    def detect_category(
        problem: str
    ) -> str:
        """Detect primary category (e.g., ARCHITECTURE, SECURITY)."""
    
    @staticmethod
    def detect_categories(
        problem: str
    ) -> dict[str, float]:
        """Detect multiple categories with scores."""
```

### Model Selection Strategy (core/services/llm/router.py)

**Location**: `src/core/services/llm/router.py`

**Purpose**: Intelligent LLM model selection

**Key Class**:
```python
class ModelSelectionStrategy:
    """Intelligent model selection strategy."""
    
    @staticmethod
    def select_model(
        complexity: str,
        requires_reasoning: bool,
        requires_code: bool,
        token_estimate: int,
        latency_preference: str = "balanced"
    ) -> tuple[str, str, ModelDepth, float]:
        """Select optimal model based on task requirements."""
```

---

## 6. Tools

### Simplified Tools (tools/simplified_tools.py)

**Location**: `src/tools/simplified_tools.py`

**Purpose**: Main MCP tools for cognitive operations

**Key Functions**:
```python
@mcp.tool()
@rate_limited(max_requests=10, window_seconds=60)
async def thinking(
    problem_statement: str,
    llm_model_name: str,
    thought_content: str = "",
    profile: str = "balanced",
    model_id: str = "",
    estimated_thoughts: int = 0
) -> dict[str, Any]:
    """Create new session + execute first thinking step."""

@mcp.tool()
@rate_limited(max_requests=10, window_seconds=60)
async def rethinking(
    session_id: str,
    llm_model_name: str,
    thought_content: str,
    thought_number: int = 2,
    estimated_total_thoughts: int = 5,
    next_thought_needed: bool = True,
    thought_type: str = "analysis",
    strategy: str = "auto",
    is_revision: bool = False,
    revises_thought_id: Optional[str] = None,
    branch_from_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    critic_persona: str = "auto"
) -> dict[str, Any]:
    """Continue thinking from existing session."""

@mcp.tool()
def list_thinking(
    include_archived: bool = False,
    status_filter: str = "all"
) -> dict[str, Any]:
    """List all cognitive thinking sessions."""

@mcp.tool()
def branches(
    session_id: str,
    action: str = "get_tree",
    thought_id: str = "",
    branch_ids: List[str] = None,
    reason: str = ""
) -> dict[str, Any]:
    """Tree of Thoughts branch management."""
```

### Export Tools (tools/export_tools.py)

**Location**: `src/tools/export_tools.py`

**Purpose**: Export and analysis MCP tools

**Key Functions**:
```python
@mcp.tool()
def export_thinking_session(
    session_id: str,
    session_token: str = ""
) -> dict[str, object]:
    """Export session history with session token validation."""

@mcp.tool()
def analyze_session(
    session_id: str,
    session_token: str = ""
) -> dict[str, object]:
    """Analyze session quality with session token validation."""
```


---

## 7. Analysis Components

### Scoring Engine (analysis/scoring_engine.py)

**Location**: `src/analysis/scoring_engine.py`

**Purpose**: Thought quality scoring and metrics calculation

**Key Class**:
```python
class ScoringEngine:
    """Engine for scoring and metrics calculation."""
    
    def score_thought(
        self,
        thought: EnhancedThought
    ) -> ThoughtMetrics:
        """Score a thought and return metrics."""
    
    def analyze_pattern(
        self,
        thoughts: list[EnhancedThought]
    ) -> dict[str, Any]:
        """Analyze patterns in a sequence of thoughts."""
    
    def get_analysis_report(
        self,
        session_id: str
    ) -> dict[str, Any]:
        """Get comprehensive analysis report."""
```

### Bias Detection (analysis/bias.py)

**Location**: `src/analysis/bias.py`

**Purpose**: Bias detection and analysis

**Key Functions**:
```python
def detect_bias(text: str) -> dict[str, Any]:
    """Detect bias in text."""

def analyze_bias_patterns(
    thoughts: list[EnhancedThought]
) -> dict[str, Any]:
    """Analyze bias patterns across thoughts."""
```

### Quality Assessment (analysis/quality.py)

**Location**: `src/analysis/quality.py`

**Purpose**: Quality assessment and evaluation

**Key Functions**:
```python
def assess_quality(
    thought: EnhancedThought
) -> dict[str, Any]:
    """Assess the quality of a thought."""

def get_quality_score(
    text: str
) -> float:
    """Get quality score for text."""
```

### Summarization (analysis/summarization.py)

**Location**: `src/analysis/summarization.py`

**Purpose**: Text summarization and compression

**Key Functions**:
```python
def compress_session_context(
    session_id: str,
    max_tokens: int
) -> str:
    """Compress session context to fit within token limits."""

def summarize_thoughts(
    thoughts: list[EnhancedThought]
) -> str:
    """Summarize a sequence of thoughts."""
```

---

## 8. Utilities

### Pricing Manager (utils/pricing.py)

**Location**: `src/utils/pricing.py`

**Purpose**: Cost tracking and pricing calculation

**Key Class**:
```python
class PricingManager:
    """Manager for pricing and cost calculation."""
    
    def calculate_cost(
        self,
        tokens: int,
        model: str
    ) -> dict[str, float]:
        """Calculate cost for token usage."""
    
    def get_total_cost(
        self,
        session_id: str
    ) -> dict[str, float]:
        """Get total cost for a session."""
```

### Forex Service (utils/forex.py)

**Location**: `src/utils/forex.py`

**Purpose**: Foreign exchange rate conversion

**Key Class**:
```python
class ForexService:
    """Service for forex rate conversion."""
    
    def get_rate(
        from_currency: str,
        to_currency: str
    ) -> float:
        """Get exchange rate."""
    
    def convert(
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """Convert amount between currencies."""
```

---

## Component Interdependencies

### Dependency Graph

```
main.py
├── config.py
├── CognitiveOrchestrator
│   ├── MemoryManager
│   ├── SequentialEngine
│   ├── CognitiveEngineRegistry
│   │   ├── all modes (primitives, hybrids)
│   │   └── all services
│   ├── FusionOrchestrator
│   │   ├── MemoryManager
│   │   ├── ScoringEngine
│   │   ├── SequentialEngine
│   │   ├── AutonomousService
│   │   ├── ThoughtGenerationService
│   │   ├── GuidanceService
│   │   └── IdentityService
│   ├── IntelligenceRouter
│   │   └── ScoringEngine
│   ├── IdentityService
│   │   └── DigitalHippocampus
│   ├── AutonomousService
│   │   └── MemoryManager
│   └── InternalClearanceService
│       └── ScoringEngine
├── ScoringEngine
├── Tools (session_tools, cognitive_tools, export_tools)
│   └── CognitiveOrchestrator
└── Analysis components
    ├── ScoringEngine
    ├── bias.py
    ├── quality.py
    └── summarization.py
```

### Initialization Order

1. **Configuration**: Load settings from environment
2. **Infrastructure**: Initialize MemoryManager, SequentialEngine
3. **Services**: Initialize all services (Identity, Guidance, Autonomous, etc.)
4. **Engines**: Initialize FusionOrchestrator, IntelligenceRouter
5. **Registry**: Initialize CognitiveEngineRegistry with all modes
6. **Orchestrator**: Initialize master CognitiveOrchestrator
7. **Tools**: Register MCP tools with FastMCP
8. **Server**: Start FastAPI/FastMCP server

---

## Summary

The CCT MCP Server architecture consists of:

- **Entry Point**: System bootstrap and server initialization
- **Core Components**: Configuration, models, security, validators, rate limiting
- **Cognitive Engines**: Memory, sequential, fusion, and master orchestrator
- **Cognitive Modes**: Primitives and hybrids with registry
- **Services**: Identity, guidance, autonomous, LLM integration, digital hippocampus
- **Tools**: MCP tools for session, cognitive, and export operations
- **Analysis**: Scoring, bias detection, quality assessment, summarization
- **Utilities**: Pricing and forex services

All components follow DDD principles with clear separation of concerns and well-defined interfaces.
