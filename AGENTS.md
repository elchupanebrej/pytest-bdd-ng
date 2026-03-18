# pytest-bdd-ng Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-18

## Active Technologies
- Project type: Python library and CLI tooling
- Python 3.10-3.14, with Python 3.14 provisioned from conda-forge when needed
- Core tooling: `pytest>=7`, `pluggy`, `tox>=4.2`, `pre-commit`, `ruff`, `mypy`, `packaging`
- BDD/runtime stack: `cucumber-messages`, `gherkin`, `jsonschema`, `PyYAML`, internal pytest-bdd parser/runtime/plugin layers, and canonical `pytest.config.stash`-backed runtime state
- Documentation/generation stack: `Jinja2`, `pypandoc`, `pathlib2`, markdown/RST feature docs, and generated docs under `docs/features/`
- Distributed/live-reporting stack: `pytest-xdist>=3.8.0`, `execnet`, `filelock`, Docker/Compose for non-native remote acceptance, Node.js on `PATH`, `@cucumber/cucumber`, and `@cucumber/pretty-formatter`
- Runtime/storage model: in-memory `Run`/`ScenarioRun`/execution-context state plus file artifacts such as NDJSON, JSON, YAML, Markdown, and temporary rendered script/output files under repository and temp paths

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
- Outside pytest hook implementations, returning `None` is an antipattern; use
  explicit values or deterministic exceptions instead.
- For non-native platform test environments, run via the Docker skill; Windows
  targets are exempt from this Docker requirement.

## Recent Changes
- 015-replace-step-context: Added Python 3.10-3.14 + `pytest>=7`, `pytest-bdd-ng` internal core
- 013-live-formatter-rendering: Added Python 3.10-3.14 with Node.js runtime available on `PATH` + `pytest>=7`, `pluggy`, `pytest-xdist>=3.8.0`, `execnet`, `filelock`, `cucumber-messages`, `@cucumber/cucumber`, `@cucumber/pretty-formatter`
- 012-cucumber-formatters-support: Added Python 3.10-3.14 with Node.js runtime available on `PATH` + `pytest>=7`, `pluggy`, `cucumber-messages`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
