# Testing Guide

## Overview

This document provides comprehensive information about the CCT MCP Server test suite, including test coverage, running tests, and adding new tests.

## Test Structure

```
tests/
├── conftest.py                          # Pytest fixtures and configuration
├── unit/                                # Unit tests
│   ├── core/                            # Core module tests
│   │   ├── test_config.py              # Configuration loading and validation
│   │   ├── test_models.py              # Domain models and enums
│   │   ├── test_security.py            # Security utilities (tokens, hashing)
│   │   └── test_validators.py          # Input validation
│   ├── engines/                         # Engine module tests
│   │   ├── memory/
│   │   │   ├── test_memory_manager.py  # SQLite memory management
│   │   │   └── test_thinking_patterns.py # Pattern archiving
│   │   ├── test_orchestrator.py        # Cognitive orchestrator
│   │   └── test_sequential_engine.py   # Sequential thought processing
│   ├── modes/                           # Cognitive mode tests
│   │   ├── test_base.py                # Base cognitive engine contract
│   │   ├── test_actor_critic.py        # Actor-Critic hybrid mode
│   │   ├── test_long_term_horizon.py   # Long-term horizon mode
│   │   ├── test_multi_agent.py         # Multi-agent fusion mode
│   │   ├── test_primitives.py          # Primitive strategies
│   │   └── test_unconventional_pivot.py # Unconventional pivot mode
│   └── tools/                           # Tool tests
│       ├── test_cognitive_tools.py      # Cognitive analysis tools
│       ├── test_export_tools.py         # Session export tools
│       └── test_session_tools.py       # Session management tools
├── analysis/                            # Analysis module tests
│   └── test_scoring_engine.py          # Scoring and metrics calculation
├── integration/                         # Integration tests
│   └── test_cognitive_workflow.py     # End-to-end cognitive workflow
├── test_pricing.py                     # Pricing and cost calculation
└── test_requirements.py                # Dependency verification
```

## Test Coverage

### Core Modules (High Priority)

| Module | Test File | Coverage Status | Key Tests |
|--------|-----------|----------------|-----------|
| `config.py` | `test_config.py` | ✅ Complete | Environment variable parsing, validation, defaults |
| `security.py` | `test_security.py` | ✅ Complete | Token generation, hashing, verification, sanitization |
| `validators.py` | `test_validators.py` | ✅ Complete | ID validation, content validation, transport modes |
| `models.py` | `test_models.py` | ✅ Existing | Thought metrics, enhanced thought, enums |

### Analysis Modules (High Priority)

| Module | Test File | Coverage Status | Key Tests |
|--------|-----------|----------------|-----------|
| `scoring_engine.py` | `test_scoring_engine.py` | ✅ Complete | Pattern detection, analysis, caching, incremental analysis |

### Engine Modules (Medium Priority)

| Module | Test File | Coverage Status | Key Tests |
|--------|-----------|----------------|-----------|
| `memory_manager.py` | `test_memory_manager.py` | ✅ Existing | Session CRUD, thought storage, history retrieval |
| `thinking_patterns.py` | `test_thinking_patterns.py` | ✅ Complete | Pattern archiving, markdown export, threshold logic |
| `orchestrator.py` | `test_orchestrator.py` | ✅ Existing | Strategy execution, session management |
| `sequential_engine.py` | `test_sequential_engine.py` | ✅ Existing | Thought processing, context management |

### Mode Modules (Medium Priority)

| Module | Test File | Coverage Status | Key Tests |
|--------|-----------|----------------|-----------|
| `base.py` | `test_base.py` | ✅ Complete | Engine contract, validation, thought linking |
| `actor_critic.py` | `test_actor_critic.py` | ✅ Existing | Actor-Critic loop, synthesis generation |
| `long_term_horizon.py` | `test_long_term_horizon.py` | ✅ Existing | Temporal projection, horizon planning |
| `multi_agent.py` | `test_multi_agent.py` | ✅ Existing | Multi-agent fusion, consensus building |
| `primitives.py` | `test_primitives.py` | ✅ Existing | Primitive strategy execution |
| `unconventional_pivot.py` | `test_unconventional_pivot.py` | ✅ Existing | Lateral thinking, paradigm shifts |

### Tool Modules (Medium Priority)

| Module | Test File | Coverage Status | Key Tests |
|--------|-----------|----------------|-----------|
| `cognitive_tools.py` | `test_cognitive_tools.py` | ✅ Existing | Analysis tools, scoring integration |
| `export_tools.py` | `test_export_tools.py` | ✅ Existing | Session export, markdown generation |
| `session_tools.py` | `test_session_tools.py` | ✅ Existing | Session CRUD, state management |

### Integration Tests

| Test File | Coverage Status | Key Tests |
|-----------|----------------|-----------|
| `test_cognitive_workflow.py` | ✅ Existing | End-to-end cognitive pipeline, strategy execution |

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v
```

### Run Specific Test Files

```bash
# Run core module tests
pytest tests/unit/core/

# Run engine tests
pytest tests/unit/engines/

# Run analysis tests
pytest tests/unit/analysis/

# Run integration tests
pytest tests/integration/
```

### Run Specific Test Functions

```bash
# Run specific test
pytest tests/unit/core/test_config.py::test_load_settings_defaults

# Run tests matching pattern
pytest -k "test_load_settings"
```

## Test Fixtures

### Available Fixtures (from `conftest.py`)

| Fixture | Description |
|---------|-------------|
| `memory_manager` | In-memory SQLite MemoryManager for isolated tests |
| `sequential_engine` | SequentialEngine with test memory manager |
| `orchestrator` | CognitiveOrchestrator with test components |

### Custom Fixtures

Tests can define custom fixtures for specific needs:

```python
@pytest.fixture
def sample_session():
    """Create sample session state."""
    return CCTSessionState(
        session_id="test_session",
        problem_statement="Test problem",
        profile="balanced",
        status="active"
    )
```

## Adding New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test functions: `test_<functionality_being_tested>`
- Test classes: `Test<ClassName>`

### Test Structure Template

```python
import pytest
from src.module import ClassOrFunction

def test_functionality_basic():
    """Test basic functionality."""
    # Arrange
    input_data = "test"
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_result

def test_functionality_edge_case():
    """Test edge case or error condition."""
    with pytest.raises(ValueError):
        function_to_test(invalid_input)
```

### Testing Best Practices

1. **Arrange-Act-Assert Pattern**: Structure tests clearly
2. **Isolation**: Each test should be independent
3. **Descriptive Names**: Test names should describe what's being tested
4. **Fixtures**: Use fixtures for common setup
5. **Mocking**: Mock external dependencies when needed
6. **Edge Cases**: Test boundary conditions and error paths

## Coverage Goals

### Current Coverage Status

| Module | Target | Current | Status |
|--------|--------|---------|--------|
| Core | 90% | ~85% | 🟡 Good |
| Analysis | 85% | ~80% | 🟡 Good |
| Engines | 85% | ~80% | 🟡 Good |
| Modes | 80% | ~75% | 🟡 Good |
| Tools | 80% | ~75% | 🟡 Good |

### Coverage Goals

- **Core Modules**: 90%+ coverage
- **Analysis Modules**: 85%+ coverage
- **Engine Modules**: 85%+ coverage
- **Mode Modules**: 80%+ coverage
- **Tool Modules**: 80%+ coverage

## Continuous Integration

Tests should be run as part of CI/CD pipeline:

```bash
# Run tests in CI
pytest --cov=src --cov-report=xml --junitxml=test-results.xml
```

## Troubleshooting

### Common Issues

**Import Errors**: Ensure project root is in Python path
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
```

**Database Locks**: Use in-memory SQLite for tests (handled by `TestMemoryManager` in `conftest.py`)

**Fixture Not Found**: Ensure fixtures are defined in `conftest.py` or test file

### Debugging Failed Tests

```bash
# Run with pdb on failure
pytest --pdb

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

## Test Dependencies

Required test dependencies (in `requirements.txt`):
- `pytest>=8.0.0`
- `pytest-cov>=4.0.0`
- `pytest-asyncio>=0.21.0`

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Test Coverage](https://coverage.readthedocs.io/)
