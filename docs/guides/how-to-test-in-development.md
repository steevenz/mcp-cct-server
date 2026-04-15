# Guide: Testing in Development

This guide provides comprehensive information for testing the CCT MCP Server during development, including test structure, running tests, debugging, and adding new tests.

## Overview

The CCT MCP Server uses a **DDD-aligned test structure** organized by architectural layers. The test suite includes unit tests, integration tests, verification tests, and benchmarks to ensure code quality and functionality.

## Test Structure (DDD-Aligned)

```
tests/
├── domain/                    # Domain Layer Tests
│   └── models/               # Domain models, value objects, enums
│       └── test_models.py    # Model validation and behavior
│
├── application/              # Application Layer Tests
│   ├── services/            # Application services
│   │   └── test_config.py   # Configuration service tests
│   ├── modes/               # Cognitive modes (primitives & hybrids)
│   └── orchestrators/       # Application orchestrators
│
├── infrastructure/          # Infrastructure Layer Tests
│   ├── tools/              # MCP tools
│   ├── utils/              # Utility services
│   ├── analysis/           # Analysis engines
│   └── memory/             # Memory infrastructure
│
├── integration/             # Integration Tests
│   ├── test_cognitive_workflow.py  # End-to-end cognitive pipeline
│   ├── test_mcp_workflow.py         # MCP protocol workflow
│   ├── test_hybrid_flows.py         # Hybrid cognitive flows
│   └── test_hitl_hardening.py      # Human-in-the-loop hardening
│
├── verifications/           # Whitepaper Verification Tests
│   └── README.md           # Verification test documentation
│
├── benchmarks/             # Benchmark Tests
│   └── performance_benchmarks.py  # Performance and load testing
│
├── test_cct.py             # CCT server integration test
├── test_mcp_server.py      # MCP server protocol test
├── test_mcp_sse.py         # SSE transport test
├── test_persistence.py     # Database persistence test
├── conftest.py             # Pytest fixtures and configuration
└── README.md               # Test documentation
```

## DDD Layer Mapping

### Domain Layer (src/core/models/)

**Source Files:**
- `src/core/models/enums.py` - ThinkingStrategy, ThoughtType, CCTProfile, SessionStatus
- `src/core/models/domain.py` - EnhancedThought, CCTSessionState, ThoughtMetrics
- `src/core/models/contexts.py` - SequentialContext, CognitiveTaskContext
- `src/core/models/schemas.py` - Various Pydantic schemas
- `src/core/models/identity_defaults.py` - SOVEREIGN_MINDSET, SOVEREIGN_SOUL

**Test Location:**
- `tests/domain/models/` - Test domain models, value objects, and enums

**Testing Focus:**
- Model validation and Pydantic schema validation
- Enum value correctness and completeness
- Domain logic invariants
- Value object behavior
- Identity default constants

### Application Layer (src/core/services/, src/modes/, src/engines/orchestrator.py, src/engines/fusion/)

**Source Files:**
- `src/core/services/` - IdentityService, InternalClearanceService, DigitalHippocampus, etc.
- `src/modes/` - DynamicPrimitiveEngine, ActorCriticEngine, CouncilOfCriticsEngine, etc.
- `src/engines/orchestrator.py` - CognitiveOrchestrator
- `src/engines/fusion/orchestrator.py` - FusionOrchestrator

**Test Location:**
- `tests/application/services/` - Test application services
- `tests/application/modes/` - Test cognitive modes (primitives & hybrids)
- `tests/application/orchestrators/` - Test application orchestrators

**Testing Focus:**
- Service orchestration and coordination
- Mode selection and execution
- Business logic and workflows
- Service interactions
- Strategy pattern implementation

### Infrastructure Layer (src/tools/, src/utils/, src/analysis/, src/engines/memory/, src/engines/sequential/)

**Source Files:**
- `src/tools/` - MCP tool implementations
- `src/utils/` - PricingManager, ForexService, etc.
- `src/analysis/` - ScoringEngine, bias detection, summarization
- `src/engines/memory/` - MemoryManager
- `src/engines/sequential/` - SequentialEngine

**Test Location:**
- `tests/infrastructure/tools/` - Test MCP tools
- `tests/infrastructure/utils/` - Test utility services
- `tests/infrastructure/analysis/` - Test analysis engines
- `tests/infrastructure/memory/` - Test memory infrastructure

**Testing Focus:**
- External integrations (API calls, databases)
- Utility functions and helpers
- Analysis algorithms
- Data persistence and retrieval
- Performance and resource management

## Development Testing Workflows

### Quick Development Test Cycle

```bash
# 1. Run tests for the layer you're working on
pytest tests/domain/ -v

# 2. Run with coverage to see what you've covered
pytest tests/domain/ --cov=src/domain --cov-report=term-missing

# 3. Run specific test function during development
pytest tests/domain/models/test_models.py::test_enhanced Thought_validation -v
```

### Before Committing

```bash
# 1. Run full test suite
pytest tests/ -v

# 2. Run with coverage report
pytest tests/ --cov=src --cov-report=html

# 3. Check coverage report
# Open htmlcov/index.html in browser
```

### Testing Specific Components

#### Domain Layer Tests
```bash
# Test domain models and value objects
pytest tests/domain/models/ -v

# Run with marker (if configured)
pytest tests/domain/ -m domain -v
```

#### Application Layer Tests
```bash
# Test application services
pytest tests/application/services/ -v

# Test cognitive modes
pytest tests/application/modes/ -v

# Test orchestrators
pytest tests/application/orchestrators/ -v
```

#### Infrastructure Layer Tests
```bash
# Test MCP tools
pytest tests/infrastructure/tools/ -v

# Test analysis engines
pytest tests/infrastructure/analysis/ -v

# Test memory infrastructure
pytest tests/infrastructure/memory/ -v
```

#### Integration Tests
```bash
# Test cognitive workflow
pytest tests/integration/test_cognitive_workflow.py -v

# Test MCP protocol workflow
pytest tests/integration/test_mcp_workflow.py -v

# Test hybrid flows
pytest tests/integration/test_hybrid_flows.py -v
```

#### Server Integration Tests
```bash
# Test CCT server (requires server running)
pytest tests/test_cct.py -v

# Test MCP server protocol
pytest tests/test_mcp_server.py -v

# Test SSE transport
pytest tests/test_mcp_sse.py -v

# Test database persistence
pytest tests/test_persistence.py -v
```

### Running Tests by Pattern

```bash
# Run tests matching name pattern
pytest tests/ -k "test_memory" -v

# Run tests matching multiple patterns
pytest tests/ -k "memory or session" -v

# Exclude tests matching pattern
pytest tests/ -k "not integration" -v
```

## Test Fixtures

### Available Fixtures (from `conftest.py`)

The test suite provides several fixtures to simplify test setup:

| Fixture | Description | Scope |
|---------|-------------|-------|
| `memory_manager` | In-memory SQLite MemoryManager for isolated tests | Function |
| `sequential_engine` | SequentialEngine with test memory manager | Function |
| `scoring_engine` | ScoringEngine for analysis and metrics | Function |
| `fusion_orchestrator_base` | Properly initialized FusionOrchestrator with all services | Function |
| `automatic_router` | IntelligenceRouter for dynamic pipeline selection | Function |
| `full_registry` | CognitiveEngineRegistry with all required services | Function |
| `orchestrator` | CognitiveOrchestrator with all components injected | Function |
| `sample_session` | Sample CCT session for testing | Function |
| `sample_thought` | Sample enhanced thought for testing | Function |

### Using Fixtures in Tests

```python
import pytest
from src.engines.memory.manager import MemoryManager

def test_session_creation(memory_manager):
    """Test session creation using memory_manager fixture."""
    session = memory_manager.create_session(
        problem_statement="Test problem",
        profile="balanced",
        estimated_thoughts=10
    )
    assert session.session_id is not None
    assert session.problem_statement == "Test problem"

def test_thought_storage(memory_manager, sample_session):
    """Test thought storage using sample_session fixture."""
    from src.core.models.domain import EnhancedThought
    from src.core.models.enums import ThoughtType
    
    thought = EnhancedThought(
        id="thought_1",
        session_id=sample_session.session_id,
        content="Test content",
        thought_type=ThoughtType.ANALYSIS
    )
    
    memory_manager.add_thought(thought)
    retrieved = memory_manager.get_thought("thought_1")
    assert retrieved.content == "Test content"
```

### Custom Fixtures

You can define custom fixtures in your test files:

```python
@pytest.fixture
def custom_test_data():
    """Create custom test data for your tests."""
    return {
        "test_input": "value",
        "expected_output": "result"
    }

def test_custom_logic(custom_test_data):
    """Test using custom fixture."""
    result = process_data(custom_test_data["test_input"])
    assert result == custom_test_data["expected_output"]
```

## Debugging Tests

### Common Debugging Commands

```bash
# Stop on first failure
pytest tests/ -x

# Enter debugger on failure
pytest tests/ --pdb

# Show local variables on failure
pytest tests/ -l

# Show verbose output
pytest tests/ -vv

# Run specific test with debugging
pytest tests/domain/models/test_models.py::test_enhanced_Thought_validation -vv --pdb
```

### Debugging Failed Tests

When a test fails, use these strategies:

1. **Print Statements**: Add print statements to see intermediate values
```python
def test_complex_logic():
    input_data = {"key": "value"}
    print(f"Input: {input_data}")  # Debug output
    result = process(input_data)
    print(f"Result: {result}")  # Debug output
    assert result == expected
```

2. **Use pytest -s**: Show print output
```bash
pytest tests/ -s -v
```

3. **Use pytest --pdb-mtrace**: Debug with Python debugger
```bash
pytest tests/ --pdb-mtrace
```

4. **Isolate the failing test**: Run only the failing test
```bash
pytest tests/domain/models/test_models.py::test_failing_function -v
```

### Common Test Failures and Solutions

**Import Error: Module not found**
- Ensure you're running tests from project root
- Activate virtual environment: `source .venv/bin/activate` or `.venv\Scripts\activate`
- Check that src is in Python path

**Fixture not found**
- Ensure fixture is defined in conftest.py or test file
- Check fixture name spelling
- Verify fixture scope (function vs session)

**Database lock errors**
- Tests use in-memory SQLite via TestMemoryManager
- Each test gets isolated database
- If you see lock errors, ensure you're using the memory_manager fixture

**Async test errors**
- Use `@pytest.mark.asyncio` decorator for async tests
- Ensure pytest-asyncio is installed
- Use `pytest --asyncio-mode=auto` flag

## Writing New Tests

### Test Naming Convention

- **Test files**: `test_<module_name>.py` (e.g., `test_config.py`, `test_models.py`)
- **Test functions**: `test_<functionality_being_tested>` (e.g., `test_session_creation`)
- **Test classes**: `Test<ClassName>` (e.g., `TestMemoryManager`)

### Test Structure Template

```python
import pytest
from src.module import ClassOrFunction

def test_basic_functionality():
    """Test basic functionality with clear structure."""
    # Arrange - Set up test data
    input_data = "test_input"
    expected = "expected_output"
    
    # Act - Execute the function being tested
    result = function_to_test(input_data)
    
    # Assert - Verify the result
    assert result == expected

def test_edge_case():
    """Test edge case or error condition."""
    invalid_input = None
    
    # Act & Assert - Should raise an exception
    with pytest.raises(ValueError):
        function_to_test(invalid_input)
```

### Testing Domain Models

```python
import pytest
from src.core.models.domain import EnhancedThought
from src.core.models.enums import ThoughtType, ThinkingStrategy
from src.core.models.contexts import SequentialContext

def test_enhanced_Thought_creation(memory_manager, sample_session):
    """Test creating an enhanced thought."""
    thought = EnhancedThought(
        id="thought_1",
        session_id=sample_session.session_id,
        content="Test content",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.SYSTEMATIC,
        sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=10)
    )
    
    assert thought.id == "thought_1"
    assert thought.session_id == sample_session.session_id
    assert thought.content == "Test content"
```

### Testing Application Services

```python
import pytest
from src.core.config import load_settings

def test_config_loading():
    """Test configuration loading from environment."""
    # Arrange - Set environment variable
    import os
    os.environ["CCT_PORT"] = "8001"
    
    # Act - Load settings
    settings = load_settings()
    
    # Assert - Verify settings
    assert settings.port == 8001
    
    # Cleanup
    del os.environ["CCT_PORT"]
```

### Testing with Fixtures

```python
def test_session_with_fixture(memory_manager):
    """Test using memory_manager fixture."""
    # Arrange - Create session using fixture
    session = memory_manager.create_session(
        problem_statement="Test problem",
        profile="balanced"
    )
    
    # Act - Add thought to session
    from src.core.models.domain import EnhancedThought
    thought = EnhancedThought(
        id="thought_1",
        session_id=session.session_id,
        content="Test thought"
    )
    memory_manager.add_thought(thought)
    
    # Assert - Verify thought was added
    retrieved = memory_manager.get_thought("thought_1")
    assert retrieved is not None
    assert retrieved.content == "Test thought"
```

### Testing Best Practices

1. **Arrange-Act-Assert Pattern**: Structure tests clearly with these three phases
2. **Isolation**: Each test should be independent and not depend on other tests
3. **Descriptive Names**: Test names should describe what's being tested
4. **Use Fixtures**: Leverage fixtures for common setup to reduce duplication
5. **Mock External Dependencies**: Mock external services (API calls, databases) when needed
6. **Test Edge Cases**: Test boundary conditions, empty inputs, and error paths
7. **Keep Tests Fast**: Unit tests should run quickly (avoid slow operations)
8. **Test One Thing**: Each test should verify one specific behavior

## Test Coverage

### Running Coverage Analysis

```bash
# Generate coverage report for all tests
pytest tests/ --cov=src --cov-report=html

# Generate coverage for specific module
pytest tests/domain/ --cov=src/domain --cov-report=html

# Show coverage in terminal
pytest tests/ --cov=src --cov-report=term-missing
```

### Coverage Goals by Layer

| Layer | Target Coverage | Priority |
|-------|----------------|----------|
| Domain | 90%+ | High |
| Application | 85%+ | High |
| Infrastructure | 80%+ | Medium |
| Integration | 70%+ | Medium |

### Improving Coverage

```bash
# Find uncovered lines
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML report to see detailed coverage
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Focus on low-coverage modules
pytest tests/domain/models/ --cov=src/domain/models --cov-report=term-missing
```

## Development-Specific Tips

### Fast Feedback Loop

```bash
# Watch mode - re-run tests on file changes
pytest-watch tests/  # Requires pytest-watch package

# Or use pytest-xdist for parallel testing
pytest tests/ -n auto  # Run tests in parallel
```

### Testing Without API Keys

```bash
# Set empty API key to use guided mode
export CCT_LLM_PROVIDER=""
export CCT_LLM_PROVIDER=""

# Run tests - they should work without API keys
pytest tests/ -v
```

### Testing Database Changes

```bash
# After database schema changes, clear test database
# Tests use in-memory SQLite, so no manual cleanup needed

# Test persistence separately
pytest tests/test_persistence.py -v
```

### Temporary Files

- Use `tests/verifications/temp` for temporary test files
- Use `output/` folder in project root for test outputs
- All test fixtures are configured to use designated temp folders

## Continuous Integration

### Running Tests in CI

```bash
# Run tests with coverage and JUnit XML for CI
pytest tests/ --cov=src --cov-report=xml --cov-report=term --junitxml=test-results.xml
```

### Pre-commit Hook (Optional)

Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Common Issues

**Import Error: Module not found**
```bash
# Solution: Ensure you're in project root and venv is activated
cd /path/to/mcp-cct-server
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows
```

**Database Lock Errors**
- Tests use in-memory SQLite via `TestMemoryManager` in `conftest.py`
- Each test gets isolated database
- If you see lock errors, ensure you're using the memory_manager fixture

**Fixture Not Found**
```bash
# Solution: Ensure fixture is defined in conftest.py
# Check fixture name spelling
# Verify fixture scope (function vs session)
```

**Tests Timeout**
```bash
# Solution: Increase timeout for slow tests
pytest tests/ --timeout=300  # Requires pytest-timeout package
```

**Port Already in Use**
```bash
# Solution: Change CCT_PORT in .env or environment variable
export CCT_PORT=8002
pytest tests/test_cct.py
```

### Test Dependencies

Required test dependencies (install with pip):
```bash
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
pytest-xdist>=3.0.0  # For parallel testing
pytest-watch>=4.0.0  # For watch mode
pytest-timeout>=2.0.0  # For timeout handling
```

Install all test dependencies:
```bash
pip install pytest pytest-cov pytest-asyncio pytest-xdist pytest-watch pytest-timeout
```

## Quick Reference

### Essential Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific layer
pytest tests/domain/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/domain/models/test_models.py::test_enhanced_Thought_validation -v

# Run tests matching pattern
pytest tests/ -k "memory" -v

# Stop on first failure
pytest tests/ -x

# Debug on failure
pytest tests/ --pdb

# Parallel execution
pytest tests/ -n auto
```

### Test Markers

If markers are configured in pytest.ini:
```bash
# Run tests by marker
pytest tests/ -m domain -v
pytest tests/ -m application -v
pytest tests/ -m integration -v
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Test Coverage](https://coverage.readthedocs.io/)
- [Project Test README](tests/README.md)

## Summary

**Key Points for Development Testing:**
- Use DDD-aligned test structure (domain, application, infrastructure, integration)
- Leverage fixtures from conftest.py for common setup
- Run tests frequently during development for fast feedback
- Use coverage reports to identify untested code
- Test at the layer you're working on (don't always run full suite)
- Debug failed tests with pytest --pdb or -x flags
- Keep tests isolated and fast
- Use descriptive test names and Arrange-Act-Assert pattern

**Development Workflow:**
1. Write code
2. Write/Update tests for that code
3. Run tests for the specific layer
4. Fix any failures
5. Run full test suite before committing
6. Check coverage report
