<!-- generated-by: gsd-doc-writer -->
# Testing

## Test Framework

The project uses **pytest** as its test framework, with the following key plugins:

- `pytest-xdist` — Parallel test execution
- `pytest-httpserver` — HTTP server for testing
- `pytest-order` — Test ordering
- `pytest-timeout` — Test timeouts
- `hypothesis` — Property-based testing
- `factory-boy` — Test fixtures

## Running Tests

### Quick Test Suite

```bash
# Run default tests (excludes slow/docker/windows/browser/external)
make test

# Or directly:
uv run python -m pytest tests/cases -m "not slow and not docker and not windows and not browser and not external"
```

### Test Groups

```bash
make test-unit          # Unit tests
make test-integration   # Integration tests
make test-contract      # Contract tests
make test-e2e           # End-to-end tests
make test-compat        # Compatibility tests
make test-perf          # Performance tests
```

### Specific Markers

```bash
pytest -m unit                    # Unit tests
pytest -m "e2e and not browser"   # E2E without browser tests
pytest -m docker                  # Docker-dependent tests
pytest -m slow                    # Slow tests
pytest -k "test_name"             # Run specific test by name
```

### Cross-Platform

```bash
make test-all                     # Full tox matrix
make test-platform-native         # Current OS only
make test-platform-linux          # Linux tests
make test-platform-windows        # Windows tests
make test-platform-macos          # macOS tests
```

## Writing New Tests

### Test File Location

Tests are organized under `tests/cases/` by type:

```
tests/cases/
├── unit/              # Unit tests (marker: unit)
├── integration/       # Integration tests (marker: integration)
├── contract/          # Contract/schema tests (marker: contract)
├── e2e/               # End-to-end tests (marker: e2e)
├── compat/            # Compatibility tests (marker: compat)
├── perf/              # Performance tests (marker: perf)
└── external/          # External dependency tests (marker: external)
```

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Adding a New Test

1. Place the test file in the appropriate group directory
2. Add the appropriate marker decorator
3. Follow existing patterns in that directory

Example:

```python
import pytest

pytestmark = [pytest.mark.contract]

class TestMyFeature:
    def test_basic_behavior(self):
        assert True

    @pytest.mark.slow
    def test_expensive_operation(self):
        # Long-running test
        pass
```

### E2E Tests with Feature Files

E2E tests use Gherkin feature files. Step definitions go in `tests/cases/e2e/steps_*.py`:

```python
from pytest_bdd import given, when, then, parsers

@given("a setup condition")
def setup_condition():
    return "value"

@when(parsers.parse("an action with {param}"))
def perform_action(param):
    pass

@then("expected outcome")
def verify_outcome():
    pass
```

## Coverage

```bash
make coverage
# Runs: uv run coverage run --source=pytest_bdd -m pytest tests/cases
# Then: uv run coverage report -m
```

No minimum coverage threshold is configured, but coverage reports are generated for review.

## CI Integration

Tests run in GitHub Actions (`.github/workflows/main.yml`):

- **Matrix**: Python 3.10-3.14 + PyPy 3.11 across Ubuntu, Windows, macOS
- **Trigger**: Push to `default` branch, pull requests
- **Steps**: Install deps → `make tox` → Coverage upload → Dist check

## Docker Tests

Some tests require Docker (marked `@pytest.mark.docker`):

```bash
# Run Docker tests
pytest -m docker

# Skip Docker tests (default)
pytest -m "not docker"
```

## Browser Tests

Browser tests use Playwright (marked `@pytest.mark.browser`):

```bash
# Install Playwright
pip install playwright
playwright install

# Run browser tests
pytest -m browser
```
