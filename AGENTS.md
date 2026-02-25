# pytest-bdd-ng Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-20

## Active Technologies
- Python 3.10-3.14 (Python 3.14 provisioned from conda-forge when needed)
- pytest, tox>=4.2, pre-commit, mypy, ruff, packaging
- Project type: Python library and CLI tooling
- Python 3.10-3.14 + pytest>=6.2.5, tox>=4.2, pre-commit, packaging (001-add-py314-pytest39-support)
- N/A (repository configuration and documentation only) (001-add-py314-pytest39-support)
- Python 3.10-3.14 + pytest, pluggy hook system, cucumber-messages models, pytest-bdd runtime/plugin layers (003-unify-run-context)
- In-memory per-test-run context state bound to pytest runtime objects (no persistent storage) (003-unify-run-context)
- Python 3.10-3.14 + pytest, pluggy hooks, cucumber-messages models, pytest-bdd runtime/plugin modules (003-unify-run-context)
- In-memory runtime context state per active scenario execution (no persistent storage) (003-unify-run-context)
- Python 3.10-3.14 + pytest, pluggy, cucumber-messages, pytest-bdd plugin runtime and hook system (003-unify-run-context)
- In-memory runtime context graph (session-root + hierarchical child contexts), no persistent storage (003-unify-run-context)
- In-memory runtime context graph + canonical `pytest.config.stash` entry (no persistent storage) (003-unify-run-context)
- Python 3.10-3.14 + pytest, Jinja2, pypandoc, pathlib2, pytest-bdd plugin/runtime layers (004-migrate-jinja2-docs)
- Filesystem-only artifacts under `docs/features/` and generated temporary output directories (004-migrate-jinja2-docs)
- Python 3.10-3.14 + pytest, pluggy-based pytest-bdd plugins, Jinja2, packaging metadata (`setup.cfg`), pre-commi (004-migrate-jinja2-docs)
- N/A (file-based generation only) (004-migrate-jinja2-docs)
- Python 3.10-3.14 + pytest>=6.2.5, Jinja2, pluggy hooks, pre-commit, tox>=4.2, ruff, packaging (004-migrate-jinja2-docs)
- N/A (in-repo files only) (004-migrate-jinja2-docs)

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
- Documentation and planning artifacts MUST be written in English.
- For non-native platform test environments, run via the Docker skill; Windows
  targets are exempt from this Docker requirement.

## Recent Changes
- 004-migrate-jinja2-docs: Added Python 3.10-3.14 + pytest>=6.2.5, Jinja2, pluggy hooks, pre-commit, tox>=4.2, ruff, packaging
- 004-migrate-jinja2-docs: Added Python 3.10-3.14 + pytest, pluggy-based
  pytest-bdd plugins, Jinja2, packaging metadata (`setup.cfg`), pre-commit.
- 004-migrate-jinja2-docs: Added Python 3.10-3.14 + pytest, Jinja2, pypandoc,
  pathlib2, pytest-bdd plugin/runtime layers.
  cucumber-messages models, pytest-bdd runtime/plugin layers
  fixture/stash access model, and reporting hierarchy requirements.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
