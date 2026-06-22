# pytest-bdd-ng Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-11

# Meta AGENTS.md
- Development guideline is stored at `DEVELOPMENT.rst`
- NO DUPLICATED INFORMATION IS ALLOWED HERE. ON UPDATE ALL DUPLICATES MUST BE LEFT IN ONE COPY IN THIS DOCUMENT

## Active Technologies
- Project type: Python library and CLI tooling
- Python 3.10-3.14, with Python 3.14 provisioned via `uv python install` when needed
- Core tooling: `pytest>=7`, `pluggy`, `tox>=4.2`, `pre-commit`, `ruff`, `mypy`, `packaging`
- BDD/runtime stack: `cucumber-messages`, `gherkin`, `gherkin-official`, `jsonschema`, `PyYAML`, `aiofiles` (optional, async I/O), internal pytest-bdd parser/runtime/plugin layers, and canonical `pytest.config.stash`-backed runtime state
- Documentation/generation stack: `Jinja2`, `pypandoc`, `pathlib2`, markdown/RST feature docs, and generated docs under `docs/features/`
- Distributed/live-reporting stack: `pytest-xdist>=3.8.0`, `execnet`, `filelock`, Docker/Compose for non-native remote acceptance, Node.js on `PATH`, `@cucumber/cucumber`, and `@cucumber/pretty-formatter`
- Runtime/storage model: in-memory `Run`/`ScenarioRun`/execution-context state plus file artifacts such as NDJSON, JSON, YAML, Markdown, and temporary rendered script/output files under repository and temp paths. 022 feature adds in-memory dict `{Path: GherkinDocument}` in `pytest.config.stash` (no persistent storage).
- Python 3.10-3.14 (runtime), Go 1.21+ (build-time only, for cgo shared library compilation) + `gherkin-official>=33` (Python fallback, unchanged), `cucumber/gherkin/go/v28` (Go parser, vendored), `cucumber/messages/go/v28` (Go messages, vendored), `ctypes` (stdlib), `setuptools` (build) (023-go-gherkin-parser)

## Project Structure

```text
features/                 Executable BDD docs (Gherkin .feature.md files)
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
scripts/
  benchmark-before-after.ps1  Git checkout comparison script
pyproject.toml            Project config, deps, pytest settings, ruff rules
DEVELOPMENT.rst           Development guidelines
```

## Additional development guide

- If Microsoft Windows in use - use `wsl2` where possible.
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
- Use `attrs` library over builtin `dataclass`es
- Project practices ATDD/BDD: when a new feature is developed, acceptance tests must be created under `features/` with appropriate skill
- Debugging: All agents can launch with pytest pdb mcp step via `--mcp-pdb-on-fail` flag for interactive debugging (see `DEVELOPMENT.rst` § Debug MCP for details)
    - Run test with `--mcp-pdb-on-fail`, poll `.pytest_cache/mcp-pdb/session.json` for sidecar port, connect raw TCP to remote-pdb, send pdb commands, write investigation artifacts to `.pytest_cache/mcp-pdb/artifacts/<session_id>/`, send `continue` to unblock.
    - The `--mcp-pdb-on-fail` starts a `mcp-pdb` MCP server subprocess and blocks the test thread on `remote_pdb.set_trace()` until a client connects.
    - Registry step discovery: `Registry.registry` is a `cached_property` (not `lru_cache` — see fix 2026-06-08). Collection code uses `__pytest_bdd_step_registry__` attribute; `_build_collection_step_registry` uses `Registry(definitions=OrderedSet(...))`.

## Git and Pre-commit Workflow
- **No verification bypass**: Committing changes with pre-commit checks disabled (e.g. using `git commit --no-verify` or environment overrides) is strictly forbidden without explicit user permission.
- **Pre-commit failure resolution**: If the pre-commit hook fails on existing files:
  1. Verify the repository status before your changes.
  2. Create a separate, dedicated commit to fix the failing pre-commit checks first.
  3. Rebase/transplant your active feature work onto the clean, lint-passing commit.
  4. Ensure all pre-commit hooks and tests run cleanly before final commit.
- **Global Check/Tool Disabling Constraint**: Disabling pre-commit checks or linting tools globally in `pyproject.toml` is forbidden without explicit user permission. Requests for such permission must be accompanied by detailed arguments.
- **Local Ignore Rule**: Disabling or ignoring a specific check/rule must be done locally at the place of use (e.g., via inline comments like `# noqa` or `# pylint: disable`).
- **Directory Exclusions**: Disabling or excluding entire directories from checks is forbidden without explicit user permission, which must be requested with detailed arguments. Any excluded check/folder must have a descriptive comment explaining the reason nearby.
