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
- Python 3.10-3.14 + pytest>=6.2.5, pytest-bdd parser/runtime layers,
  gherkin markdown token matcher, pre-commit, tox>=4.2
  (005-no-empty-bdd-headings)
- N/A (in-repo text files and validation diagnostics only) (005-no-empty-bdd-headings)
- Python 3.10-3.14 + pytest>=6.2.5, pluggy hook system, cucumber-messages models/converter, pytest-bdd reporter/runtime plugins, mypy, tox>=4.2, pre-commi (006-unify-event-messages)
- In-memory runtime state + NDJSON report artifacts + repository `specs/` directory metadata (006-unify-event-messages)
- Python 3.10-3.14 + pytest>=6.2.5, pluggy hook system, cucumber-messages (upstream baseline pinned per release cycle), pytest-bdd runtime/reporter plugins, mypy, tox>=4.2, pre-commi (007-maximize-messages-coverage)
- In-memory runtime reporting state + NDJSON artifacts + feature planning artifacts under `specs/007-maximize-messages-coverage/` (007-maximize-messages-coverage)
- In-memory runtime reporting state + NDJSON artifacts + feature governance artifacts under `specs/007-maximize-messages-coverage/` (007-maximize-messages-coverage)
- Python 3.10-3.14 + `pytest`, `cucumber-messages`, `pluggy`, `jsonschema` (007-maximize-messages-coverage)
- N/A (in-repo json artifacts only) (007-maximize-messages-coverage)
- Python 3.10-3.14 + `pytest`, `pluggy`, `cucumber-messages`, `jsonschema` (008-maximize-messages-coverage)
- In-repo NDJSON + JSON artifacts (no persistent database) (008-maximize-messages-coverage)
- Python 3.10-3.14 + `pytest>=6.2.5`, `cucumber-messages`, `pluggy`, `jsonschema`, `tox>=4.2`, `pre-commit` (008-maximize-messages-coverage)
- In-memory runtime state + NDJSON artifacts + repository governance artifacts under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/` (008-maximize-messages-coverage)
- Python 3.10-3.14 + `pytest`, `pluggy`, `cucumber-messages`, `jsonschema`, internal `pytest_bdd` governance/reporting modules (008-maximize-messages-coverage)
- File-based artifacts only (NDJSON message streams, JSON governance reports, Markdown checklist/docs) (008-maximize-messages-coverage)
- Python 3.10-3.14 + `pytest>=6.2.5`, `pluggy`, `cucumber-messages`, `jsonschema`, `PyYAML` (008-maximize-messages-coverage)
- N/A (in-memory runtime state + file artifacts: NDJSON/JSON/YAML under repository and temporary paths) (008-maximize-messages-coverage)
- Python 3.10-3.14 + `pytest`, `pluggy`, `cucumber-messages`, `jsonschema`, pytest-bdd runtime/reporter plugin layers (009-execution-context-reporting)
- In-memory execution context state + NDJSON artifacts under `artifacts/` and governance files under `specs/008-maximize-messages-coverage/` (009-execution-context-reporting)
- Python 3.10-3.14 + `pytest>=6.2.5`, `pluggy`, `cucumber-messages`, `jsonschema`, existing `message_converter` (009-execution-context-reporting)
- In-memory runtime context state (`ExecutionContext`, `SessionExecutionContext`) + file artifacts (NDJSON, JSON governance reports under `artifacts/` and `specs/`) (009-execution-context-reporting)
- In-memory runtime context (`Run`/`ScenarioRun`) + file artifacts (`.ndjson`, governance JSON) (009-execution-context-reporting)
- Python 3.10-3.14 + `pytest`, `pluggy`, `cucumber-messages`, `gherkin`, `jsonschema` (009-execution-context-reporting)
- In-memory runtime state in `Run` / `ScenarioRun` plus `pytest.config.stash`; NDJSON and governance artifacts on disk (009-execution-context-reporting)

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
- 009-execution-context-reporting: Added Python 3.10-3.14 + `pytest`, `pluggy`, `cucumber-messages`, `gherkin`, `jsonschema`
- 009-execution-context-reporting: Added Python 3.10-3.14 + `pytest`, `pluggy`, `cucumber-messages`, `jsonschema`
- 009-execution-context-reporting: Added Python 3.10-3.14 + `pytest>=6.2.5`, `pluggy`, `cucumber-messages`, `jsonschema`, existing `message_converter`
  pytest-bdd parser/runtime layers, gherkin markdown token matcher,
  pre-commit, tox>=4.2
  pytest-bdd plugins, Jinja2, packaging metadata (`setup.cfg`), pre-commit.
  pathlib2, pytest-bdd plugin/runtime layers.
  cucumber-messages models, pytest-bdd runtime/plugin layers
  fixture/stash access model, and reporting hierarchy requirements.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
