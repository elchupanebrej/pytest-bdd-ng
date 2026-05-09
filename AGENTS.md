# pytest-bdd-ng Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-09

## Active Technologies
- Project type: Python library and CLI tooling
- Python 3.10-3.14, with Python 3.14 provisioned via `uv python install` when needed
- Core tooling: `pytest>=7`, `pluggy`, `tox>=4.2`, `pre-commit`, `ruff`, `mypy`, `packaging`
- BDD/runtime stack: `cucumber-messages`, `gherkin`, `jsonschema`, `PyYAML`, internal pytest-bdd parser/runtime/plugin layers, and canonical `pytest.config.stash`-backed runtime state
- Documentation/generation stack: `Jinja2`, `pypandoc`, `pathlib2`, markdown/RST feature docs, and generated docs under `docs/features/`
- Distributed/live-reporting stack: `pytest-xdist>=3.8.0`, `execnet`, `filelock`, Docker/Compose for non-native remote acceptance, Node.js on `PATH`, `@cucumber/cucumber`, and `@cucumber/pretty-formatter`
- Runtime/storage model: in-memory `Run`/`ScenarioRun`/execution-context state plus file artifacts such as NDJSON, JSON, YAML, Markdown, and temporary rendered script/output files under repository and temp paths
- Python 3.10–3.14 + `pytest >= 7`, `pytest-order` (new, to be added to test deps), `pytest-xdist >= 3.8.0` (existing) (020-test-group-ordering)
- Python 3.10–3.14 + `cucumber_messages`, `gherkin`, `attrs`, `pytest >= 7` (020-test-group-ordering)
- N/A (no new storage) (020-test-group-ordering)

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
- Documentation, specification and planning artifacts MUST be written in English.
- Outside pytest hook implementations, returning `None` is an antipattern; use
  explicit values or deterministic exceptions instead.
- For non-native platform test environments, run via the Docker skill; Windows
  targets are exempt from this Docker requirement.
- Test group ordering is configured through pytest ini-style options under
  `[tool.pytest.ini_options]`: `test_group_order`, `test_group_default`, and
  `test_group_paths`. Group names are generic configuration values, not fixed
  project constants.
- Shared test-group parsing, assignment, marker application, and xdist barrier
  logic lives in `src/pytest_bdd/util/test_group_ordering.py`; keep
  `tests/conftest.py` as a thin pytest adapter and do not add test-local
  grouping utility modules.
- Group filtering uses normal pytest marker expressions such as
  `pytest -m <configured-group>`. Non-group pytest markers must not be
  hardcoded into ignore lists; only configured group names participate in
  group resolution.

<!-- MANUAL ADDITIONS START -->
# Project structure
- Non-executable project documentation is stored at `specs` dir
- Executable project documentation is stored at `features` dir
# Conventions
- Use attrs lib over dataclasses
<!-- MANUAL ADDITIONS END -->
