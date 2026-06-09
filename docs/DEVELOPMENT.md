<!-- generated-by: gsd-doc-writer -->
# Development Guide

> For the full development guide, see [DEVELOPMENT.rst](../DEVELOPMENT.rst) in the project root.

## Local Setup

```bash
# Clone the repository
git clone https://github.com/elchupanebrej/pytest-bdd-ng.git
cd pytest-bdd-ng

# Install Python 3.14
uv python install 3.14

# Sync development environment
uv sync --extra test --extra testtypes --extra doc-gen --extra struct-bdd
```

## Build Commands

| Command | Description |
|---|---|
| `make test` | Run default test suite (no Docker/browser/slow) |
| `make test-unit` | Unit tests only |
| `make test-integration` | Integration tests only |
| `make test-contract` | Contract/schema tests only |
| `make test-e2e` | End-to-end tests (excluding browser) |
| `make test-all` | Full cross-platform tox matrix |
| `make pre-commit` | Run all pre-commit hooks |
| `make coverage` | Run tests with coverage report |
| `make build` | Build distribution packages |
| `make dist-check` | Validate built packages with twine |
| `make docs` | Build Sphinx documentation |
| `make clean` | Remove build artifacts and venv |

## Code Style

- **Linter/Formatter**: Ruff (line length 120, Python 3.10+ target)
- **Run linting**: `make pre-commit` or `uvx ruff check src/ tests/`
- **Format**: `uvx ruff format src/ tests/`
- **Type checking**: `uvx mypy src/pytest_bdd/`

## Branch Conventions

- `feat/<feature-name>` — New features
- `fix/<bug-description>` — Bug fixes
- `refactor/<description>` — Code refactoring
- Default branch: `default`

## PR Process

1. Create a feature branch from `default`
2. Make changes with tests
3. Run `make pre-commit` to verify linting
4. Run `make test` to verify tests pass
5. Open a PR against `default`
6. CI runs full matrix (Python 3.10-3.14, Ubuntu/Windows/macOS)

## Test Groups

Tests are organized by type and run via pytest markers:

```bash
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m contract      # Contract tests
pytest -m e2e           # End-to-end tests
pytest -m "not slow and not docker"  # Quick tests
```

## Architecture Overview

The project uses a layered plugin architecture with 18+ pytest plugins. See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design.
