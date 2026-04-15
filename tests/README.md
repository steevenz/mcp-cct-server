# CCT MCP Server Tests

## Test Structure (DDD-Aligned)

```
tests/
├── domain/                    # Domain Layer Tests
│   └── models/               # Domain models, value objects, enums
│
├── application/              # Application Layer Tests
│   ├── services/            # Application services
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
│
├── verifications/           # Whitepaper Verification Tests
│
├── benchmarks/             # Benchmark Tests
│
└── conftest.py             # Pytest fixtures and configuration
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific layer
```bash
# Domain layer only
pytest tests/domain/ -m domain

# Application layer only
pytest tests/application/ -m application

# Infrastructure layer only
pytest tests/infrastructure/ -m infrastructure
```

### Run specific test file
```bash
pytest tests/domain/models/test_enums.py
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Temporary Files

- Use `tests/verifications/temp` folder for temporary files
- Use `output/` folder in project root for test outputs
- All test fixtures are configured to use the designated temp folder to prevent temp file sprawl

## Pytest Configuration

See `pytest.ini` for configuration options.
