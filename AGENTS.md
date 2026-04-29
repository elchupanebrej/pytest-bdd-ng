# pytest-bdd-ng Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-19

## Active Technologies
- Project type: Python library and CLI tooling
- Python 3.10-3.14, with Python 3.14 provisioned via `uv python install` when needed
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

- `uvx --with tox-uv tox -l`
- `uv run python -m pytest tests/compatibility -q`
- `uvx pre-commit run --all-files`

## Code Style

- Follow repository linting/formatting via `ruff` and pre-commit hooks.
- Keep compatibility behavior aligned with pytest Python-version support matrix.
- Documentation and planning artifacts MUST be written in English.
- Outside pytest hook implementations, returning `None` is an antipattern; use
  explicit values or deterministic exceptions instead.
- For non-native platform test environments, run via the Docker skill; Windows
  targets are exempt from this Docker requirement.

## Recent Changes
- 016-strict-non-null: Added Python 3.10-3.14 + `attrs`, `pytest>=7`, pluggy hook system, `cucumber-messages`, `gherkin`, internal `pickle_runner` and `gherkin_message_reporter` runtime layers
- 015-replace-step-context: Added Python 3.10-3.14 + `pytest>=7`, `pytest-bdd-ng` internal core

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
