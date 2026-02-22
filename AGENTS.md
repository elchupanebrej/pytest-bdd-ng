# pytest-bdd-ng Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-20

## Active Technologies
- Python 3.10-3.14 (Python 3.14 provisioned from conda-forge when needed)
- pytest, tox>=4.2, pre-commit, mypy, ruff, packaging
- Project type: Python library and CLI tooling
- Python 3.10-3.14 + pytest>=6.2.5, tox>=4.2, pre-commit, packaging (001-add-py314-pytest39-support)
- N/A (repository configuration and documentation only) (001-add-py314-pytest39-support)

## Project Structure

```text
src/
tests/
```

## Commands

- `conda run -n pytest-bdd-ng-py314 tox -l`
- `conda run -n pytest-bdd-ng-py314 python -m pytest tests/compatibility -q`
- `conda run -n pytest-bdd-ng-py314 pre-commit run --all-files`

## Code Style

- Follow repository linting/formatting via `ruff` and pre-commit hooks.
- Keep compatibility behavior aligned with pytest Python-version support matrix.
- For non-native platform test environments, run via the Docker skill; Windows
  targets are exempt from this Docker requirement.

## Recent Changes
- 001-add-py314-pytest39-support: Added Python 3.10-3.14 + pytest>=6.2.5, tox>=4.2, pre-commit, packaging
- 001-add-py314-pytest39-support: Added Python 3.14 support path via conda-forge.
- 001-add-py314-pytest39-support: Added matrix compatibility validation flow.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
