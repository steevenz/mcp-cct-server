# Guide: Contributing to CCT MCP Server

This guide provides comprehensive instructions for contributing to the CCT MCP Server project, including development workflow, versioning, pull requests, and best practices.

## Table of Contents
1. [Getting Started](#1-getting-started)
2. [Development Workflow](#2-development-workflow)
3. [Branching Strategy](#3-branching-strategy)
4. [Commit Guidelines](#4-commit-guidelines)
5. [Pull Request Process](#5-pull-request-process)
6. [Versioning and Tags](#6-versioning-and-tags)
7. [Coding Standards](#7-coding-standards)
8. [Testing Requirements](#8-testing-requirements)
9. [Documentation](#9-documentation)

---

## 1. Getting Started

### Prerequisites

- **Python 3.8+** installed
- **Git** installed and configured
- **GitHub account** with access to the repository
- **Code editor** (VS Code, PyCharm, or similar)
- **Docker** (optional, for containerized development)

### Initial Setup

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mcp-cct-server.git
cd mcp-cct-server

# Add upstream remote
git remote add upstream https://github.com/steevenz/mcp-cct-server.git

# Set up development environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run setup
python scripts/server/setup.py

# Copy environment configuration
cp .env.example .env
```

### Development Environment

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows

# Install development dependencies
pip install pytest pytest-cov pytest-asyncio black flake8 mypy

# Run tests to verify setup
pytest tests/ -v
```

---

## 2. Development Workflow

### Feature Development Cycle

1. **Create feature branch** from `dev`
2. **Make changes** with commits
3. **Write/update tests**
4. **Run tests** to verify
5. **Update documentation**
6. **Submit pull request** to `dev`
7. **Address review feedback**
8. **Merge** when approved

### Daily Workflow

```bash
# Sync with upstream
git fetch upstream
git checkout dev
git merge upstream/dev

# Create/update feature branch
git checkout -b dev-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to your fork
git push origin dev-feature-name
```

### Before Submitting PR

```bash
# Run full test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check (optional)
mypy src/
```

---

## 3. Branching Strategy

### Branch Types

| Branch Type | Naming Convention | Purpose |
|-------------|------------------|---------|
| `main` | N/A | Production-ready code |
| `dev` | N/A | Development integration branch |
| `dev-*` | `dev-feature-name` | Feature development |
| `dev-fix-*` | `dev-fix-issue` | Bug fixes |
| `dev-doc-*` | `dev-doc-update` | Documentation updates |
| `dev-refactor-*` | `dev-refactor-module` | Code refactoring |

### Branch Lifecycle

```
main (production)
    ↑
    merge
    ↑
dev (development)
    ↑
    merge
    ↑
dev-feature-name (feature branch)
```

### Creating a Feature Branch

```bash
# Ensure dev is up to date
git checkout dev
git pull upstream dev

# Create feature branch
git checkout -b dev-add-ollama-support

# Make changes
# ... development work ...

# Commit changes
git add .
git commit -m "feat: add Ollama model support"

# Push to your fork
git push origin dev-add-ollama-support
```

### Deleting Branches

```bash
# After merge, delete local branch
git branch -d dev-add-ollama-support

# Delete remote branch
git push origin --delete dev-add-ollama-support
```

---

## 4. Commit Guidelines

### Commit Message Format

Follow conventional commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

| Type | Description | Examples |
|------|-------------|----------|
| `feat` | New feature | `feat(modes): add actor-critic mode` |
| `fix` | Bug fix | `fix(memory): resolve database lock issue` |
| `docs` | Documentation changes | `docs(readme): update installation instructions` |
| `style` | Code style changes | `style(src): format code with black` |
| `refactor` | Code refactoring | `refactor(orchestrator): simplify fusion logic` |
| `test` | Test additions/changes | `test(core): add config validation tests` |
| `chore` | Maintenance tasks | `chore(deps): update fastmcp to 3.2.3` |
| `perf` | Performance improvements | `perf(memory): optimize database queries` |

### Commit Examples

**Good commits:**
```
feat(modes): add multi-agent fusion mode

Implements multi-agent fusion mode for collaborative
cognitive processing across multiple AI agents.

- Add fusion orchestrator
- Implement consensus building
- Add multi-agent session management
```

```
fix(database): resolve connection timeout

Fix SQLite connection timeout issue when multiple
sessions access database concurrently.

Closes #123
```

**Bad commits:**
```
update stuff
fixed bug
wip
```

### Commit Frequency

- **Small, frequent commits** are preferred
- One logical change per commit
- Commit when a unit of work is complete
- Avoid "WIP" commits in shared branches

---

## 5. Pull Request Process

### Creating a Pull Request

1. **Push your branch** to your fork
2. **Go to GitHub** and click "New Pull Request"
3. **Select branches**: `dev-feature-name` → `dev`
4. **Fill PR template** with required information
5. **Link related issues** (e.g., "Closes #123")
6. **Request review** from maintainers

### PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Closes #123
Related to #456

## Changes Made
- List key changes
- Include screenshots for UI changes
- Link to relevant documentation

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Documentation updated

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed the code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings generated
- [ ] Added tests for new features
- [ ] All tests passing
```

### PR Review Process

1. **Automated checks** run (CI/CD)
2. **Code review** by maintainers
3. **Address feedback** in commits
4. **Re-request review** when changes are ready
5. **Approval** and merge by maintainer

### Addressing Review Feedback

```bash
# Make requested changes
# ... code changes ...

# Commit with fixup
git add .
git commit -m "fix: address review feedback"

# Push changes
git push origin dev-feature-name
```

### Squashing Commits

If requested to squash commits:

```bash
# Interactive rebase to squash
git rebase -i HEAD~3

# Force push after squashing
git push origin dev-feature-name --force
```

---

## 6. Versioning and Tags

### Semantic Versioning

Project follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH

MAJOR: Incompatible API changes
MINOR: Backwards-compatible functionality additions
PATCH: Backwards-compatible bug fixes
```

### Version Examples

- `1.0.0` - Initial release
- `1.1.0` - Added new cognitive mode (MINOR)
- `1.1.1` - Fixed database bug (PATCH)
- `2.0.0` - Breaking API changes (MAJOR)

### Tagging Releases

```bash
# Ensure main is up to date
git checkout main
git pull upstream main

# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0: Initial stable release"

# Push tag to GitHub
git push origin v1.0.0
git push upstream v1.0.0
```

### Release Notes

Create release notes in GitHub:

```markdown
## v1.0.0 (2026-04-15)

### Added
- Multi-agent fusion mode
- SSE transport support
- Docker deployment support

### Fixed
- Database connection timeout
- Memory leak in session management

### Changed
- Updated to FastMCP 3.2.3
- Improved error handling

### Migration
- Update .env: Add CCT_TRANSPORT variable
- Run setup.py with --multi-agent flag
```

### Pre-release Versions

```bash
# Alpha version
git tag -a v1.0.0-alpha.1 -m "Alpha release"

# Beta version
git tag -a v1.0.0-beta.1 -m "Beta release"

# RC version
git tag -a v1.0.0-rc.1 -m "Release candidate"
```

---

## 7. Coding Standards

### Python Style

Follow [PEP 8](https://pep8.org/) style guidelines:

```bash
# Format code with Black
black src/ tests/

# Check style with Flake8
flake8 src/ tests/
```

### Type Hints

Use type hints for function signatures:

```python
from typing import Dict, List, Optional

def process_session(
    session_id: str,
    options: Optional[Dict[str, str]] = None
) -> Dict[str, object]:
    """Process a cognitive session."""
    if options is None:
        options = {}
    # ... implementation ...
```

### Docstrings

Use Google-style docstrings:

```python
def create_session(
    problem_statement: str,
    profile: str = "balanced"
) -> CCTSessionState:
    """Create a new cognitive session.

    Args:
        problem_statement: The problem to solve
        profile: Cognitive profile (balanced, creative, analytical)

    Returns:
        CCTSessionState: The created session state

    Raises:
        ValueError: If problem_statement is empty
    """
    # ... implementation ...
```

### Error Handling

```python
# Use specific exceptions
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# Provide helpful error messages
if not problem_statement:
    raise ValueError(
        "problem_statement cannot be empty. "
        "Please provide a valid problem description."
    )
```

### Code Organization

Follow DDD structure:
- `src/core/models/` - Domain models
- `src/core/services/` - Application services
- `src/modes/` - Cognitive modes
- `src/tools/` - MCP tools
- `src/analysis/` - Analysis engines
- `src/engines/` - Core engines

---

## 8. Testing Requirements

### Unit Tests

Write unit tests for all new functionality:

```python
import pytest
from src.core.models.domain import EnhancedThought

def test_enhanced_thought_creation():
    """Test creating an enhanced thought."""
    thought = EnhancedThought(
        id="test_1",
        session_id="session_1",
        content="Test content"
    )
    assert thought.id == "test_1"
    assert thought.content == "Test content"
```

### Test Coverage

Maintain high test coverage:
- **Domain layer**: 90%+ coverage
- **Application layer**: 85%+ coverage
- **Infrastructure layer**: 80%+ coverage

```bash
# Check coverage
pytest tests/ --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Integration Tests

Add integration tests for complex workflows:

```python
def test_cognitive_workflow(memory_manager, orchestrator):
    """Test end-to-end cognitive workflow."""
    session = orchestrator.start_session("Test problem")
    result = orchestrator.process_thought(session.session_id, "Test thought")
    assert result["status"] == "success"
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/domain/models/test_models.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/domain/models/test_models.py::test_enhanced_thought_creation -v
```

---

## 9. Documentation

### Code Documentation

- Document all public functions and classes
- Use docstrings for complex logic
- Add inline comments for non-obvious code

### README Updates

Update README.md for:
- New features
- Configuration changes
- API changes
- Breaking changes

### Guide Updates

Update relevant guides in `docs/guides/`:
- `how-to-setup.md` - Setup changes
- `how-to-configure.md` - Configuration changes
- `how-to-manage-server.md` - Server management changes
- `how-to-test-in-development.md` - Testing changes

### Changelog

Maintain CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- Multi-agent fusion mode

### Fixed
- Database connection timeout

### Changed
- Updated FastMCP to 3.2.3
```

---

## Best Practices

### Before Submitting

- [ ] Run full test suite
- [ ] Check code formatting
- [ ] Update documentation
- [ ] Add tests for new features
- [ ] Ensure no breaking changes without version bump
- [ ] Link to related issues
- [ ] Self-review your changes

### During Development

- **Small commits** - Commit frequently with meaningful messages
- **Branch often** - Create separate branches for features
- **Test locally** - Run tests before pushing
- **Document as you go** - Update docs alongside code
- **Ask for help** - Use issues for questions

### After Merge

- **Delete feature branches** - Keep repository clean
- **Update local main** - Sync with upstream regularly
- **Review feedback** - Learn from code reviews
- **Celebrate** - Acknowledge contributions

---

## Getting Help

### Issues

- Use GitHub issues for bugs and feature requests
- Search existing issues before creating new ones
- Provide detailed information and reproduction steps

### Discussions

- Use GitHub Discussions for questions and ideas
- Tag maintainers for specific topics
- Be respectful and constructive

### Communication

- Be patient with review process
- Respond to feedback promptly
- Ask clarifying questions when needed
- Help others with their contributions

---

## Summary

**Key Points:**
- Use `dev-*` branch naming for features
- Follow conventional commit format
- Write tests for all changes
- Update documentation
- Submit PRs to `dev` branch
- Follow semantic versioning for releases
- Maintain code quality standards

**Quick Commands:**
```bash
# Create feature branch
git checkout -b dev-feature-name

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push to fork
git push origin dev-feature-name

# Sync with upstream
git fetch upstream
git checkout dev
git merge upstream/dev
```

**Resources:**
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [PEP 8 Style Guide](https://pep8.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
