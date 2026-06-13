<!-- generated-by: gsd-doc-writer -->
# Configuration

## pytest Configuration

pytest-bdd-ng is configured through `pyproject.toml` under `[tool.pytest.ini_options]`.

### Core Settings

```toml
[tool.pytest.ini_options]
bdd_allow_empty_scenarios = false
bdd_features_base_dir = "features/"
```

| Setting | Default | Description |
|---|---|---|
| `bdd_allow_empty_scenarios` | `false` | Allow scenarios with no steps |
| `bdd_features_base_dir` | `"features/"` | Base directory for feature file discovery |

### Test Group Configuration

The project uses a custom test grouping system for organizing tests by type:

```toml
test_group_default = "integration"
test_group_order = ["unit", "integration", "contract", "e2e", "compat", "perf", "external"]
test_group_paths = [
    "tests/cases/unit/** = unit",
    "tests/cases/integration/** = integration",
    "tests/cases/contract/** = contract",
    "tests/cases/e2e/** = e2e",
    "tests/cases/compat/** = compat",
    "tests/cases/perf/** = perf",
    "tests/cases/external/** = external"
]
```

Run specific groups with: `pytest -m <group-name>`

### Markers

Available pytest markers:

| Marker | Purpose |
|---|---|
| `unit` | Unit tests |
| `integration` | Integration tests |
| `contract` | Contract/schema tests |
| `e2e` | End-to-end tests |
| `compat` | Compatibility tests |
| `perf` | Performance tests |
| `external` | External dependency tests |
| `slow` | Slow-running tests |
| `docker` | Tests requiring Docker |
| `browser` | Tests requiring Playwright |
| `windows` | Windows-specific tests |
| `posix` | POSIX-specific tests |

## Linting Configuration

The project uses Ruff for linting and formatting:

```toml
[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.format]
indent-style = "space"
quote-style = "double"
```

### Running Linting

```bash
# Run all pre-commit hooks
make pre-commit

# Or directly with ruff
uvx ruff check src/ tests/
uvx ruff format src/ tests/
```

## CLI Tools

Three CLI entry points are provided:

```bash
# Allure Formatter
allure-formatter <ndjson-file> <output-dir>

# Compatibility matrix checker
compatibility_matrix --list --compatible-only
compatibility_matrix --python 314 --pytest 90

# Cucumber formatter renderer
render_cucumber_formatters
```

## Optional Dependencies

Install extras for additional functionality:

```bash
# Async support
pip install pytest-bdd-ng[async]

# StructBDD (YAML/JSON/HOCON/TOML BDD)
pip install pytest-bdd-ng[struct-bdd]

# Documentation generation
pip install pytest-bdd-ng[doc-gen]

# Playwright browser tests
pip install pytest-bdd-ng[test-playwright]

# Full install (all extras)
pip install pytest-bdd-ng[full]
```

## CI Configuration

The project tests against Python 3.10-3.14 and PyPy 3.11 across Ubuntu, Windows, and macOS. The main CI workflow is defined in `.github/workflows/main.yml`.

Key CI targets:
- `make test` — Run local tests (excludes slow/docker/windows/browser/external)
- `make tox` — Full tox matrix
- `make local-pr-gate` — Pre-merge validation (lint + e2e + matrix checks)
