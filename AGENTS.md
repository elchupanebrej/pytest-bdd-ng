# pytest-bdd-ng Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-11

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
- Python 3.10–3.14 + `aiofiles` (new optional), `gherkin-official` (existing), `pytest >= 7` (existing), `attrs` (existing), `multiprocessing` (stdlib), `asyncio` (stdlib) (022-async-feature-collection)
- In-memory dict `{Path: GherkinDocument}` in `pytest.config.stash`; no persistent storage (022-async-feature-collection)

## Project Structure

```text
eatures/                 Executable BDD docs (Gherkin .feature.md files)
  NN Topic/               Numbered feature areas (01 Tutorial, 02 Feature, ...)
docs/
  features/               Generated .rst docs from features/ (auto-generated, don't edit)
specs/                    Non-executable specs (NNN-feature-name/ per speckit)
  NNN-feature-name/
    spec.md               Feature specification
    plan.md               Implementation plan
    tasks.md              Task breakdown
    research.md           Technical decisions
    data-model.md         Entities and relationships
    contracts/            Interface contracts
    checklists/           Quality checklists
    quickstart.md         Quickstart guide
src/pytest_bdd/           Library source
  collector_batch.py      FeatureBatchParser + parse worker
  collector.py            FeatureFileModule (feature file collection)
  scenario.py             Public API: scenario(), scenarios()
  scenario_locator.py     FileScenarioLocator, UrlScenarioLocator
  parser.py               GherkinParser, MarkdownGherkinParser
  steps.py                Step definition manager, matchers
  model/
    scenario_run.py       Run, ScenarioRun, FeatureRuntimeBinding (core runtime)
    stash_access.py       StashBound base class
    message_converter.py  Dict <-> cucumber_messages conversion
  plugin/
    scenario_test_collector/  Feature autoload + batch collection
    pickle_runner/            Scenario execution runtime
    gherkin_message_reporter/ Live formatter bridge
    struct_bdd/               YAML/JSON/HOCON/TOML BDD support
    cucumber_json/            Cucumber JSON reporter
    cucumber_pretty/          Cucumber pretty formatter
    ...                       (other formatter plugins)
tests/
  unit/                   Unit tests
  feature/                Integration tests (testdir-based)
  hook/                   Hook lifecycle tests
  e2e/                    End-to-end tests (run features/ directory)
    conftest.py           Step definitions for Gherkin .feature.md files
    test_e2e.py           Entry point: scenarios(".", ...)
  model/                  Model-level tests
  messages/               Cucumber Messages protocol tests
  messages_coverage/      Message coverage probes
pyproject.toml            Project config, deps, pytest settings, ruff rules
DEVELOPMENT.rst          Development guidelines
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
