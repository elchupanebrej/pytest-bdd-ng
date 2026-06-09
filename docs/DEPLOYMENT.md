<!-- generated-by: gsd-doc-writer -->
# Deployment

## Package Distribution

pytest-bdd-ng is distributed as a Python package on PyPI.

### Building

```bash
make build
# Runs: uvx --with build python -m build
```

This creates distribution packages in `dist/`:

- `pytest_bdd_ng-{version}.tar.gz` (source distribution)
- `pytest_bdd_ng-{version}-py3-none-any.whl` (wheel)

### Validation

```bash
make dist-check
# Runs: uvx --with twine twine check dist/*
```

### Publishing

<!-- VERIFY: PyPI upload credentials and process -->
Packages are published to PyPI via CI when a GitHub release is created. The release workflow:

1. Tags the commit
2. Builds the distribution
3. Publishes to PyPI using stored credentials

### Version Management

Version is defined in `pyproject.toml` under `[project] version`. Update this field before releasing.

## CI/CD Pipeline

### Main Workflow (`.github/workflows/main.yml`)

- **Triggers**: Push to `default`, pull requests, manual dispatch
- **Matrix**: Python 3.10-3.14 + PyPy 3.11 on Ubuntu/Windows/macOS
- **Steps**:
  1. Checkout (recursive submodules)
  2. Setup Python, Node.js, uv
  3. Install npm dependencies
  4. Run `make tox` (full test matrix)
  5. Message schema validation (Python 3.14/Ubuntu only)
  6. Coverage upload to Codecov
  7. Distribution check with twine

### Messages Baseline Drift (`.github/workflows/messages-baseline-drift.yml`)

- **Schedule**: Weekly (Monday 04:00 UTC)
- **Purpose**: Detects drift in Cucumber messages capability baseline
- **Action**: Fails if capabilities change from baseline

## Docker

<!-- VERIFY: Docker image availability and registry -->
Docker images are used for cross-platform testing, not for distribution. The project uses Docker for:

- Linux backend testing on Windows/macOS
- Windows container testing
- Allure report generation

### Building Docker Images

```bash
make env-install-docker
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md (if maintained)
3. Create a pull request with the version bump
4. Merge to `default`
5. Create a GitHub release with the version tag
6. CI automatically publishes to PyPI
