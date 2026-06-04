---
last_mapped_commit: c59470a9bc50f5ae0f628a572832a5b614d862a7
mapped_at: 2026-05-12
focus: arch
---

# Codebase Structure

**Analysis Date:** 2026-05-12

## Directory Layout

```
pytest-bdd/
├── src/pytest_bdd/              # Library source (Python package)
│   ├── __init__.py              # Public API: lazy imports of given/when/then/scenario
│   ├── collector.py             # FeatureFileModule pytest collector
│   ├── collector_batch.py       # FeatureBatchParser: lazy-batched async parsing
│   ├── scenario.py              # scenario(), scenarios() decorators
│   ├── scenario_locator.py      # FileScenarioLocator, UrlScenarioLocator
│   ├── feature_locator.py       # ScenarioLocatorBuilder (marks -> locators)
│   ├── steps.py                 # StepDefinitionManager, Registry, Matcher
│   ├── parsers.py               # StepParser hierarchy (re, parse, cfparse, etc.)
│   ├── parser.py                # GherkinParser, MarkdownGherkinParser
│   ├── hook.py                  # before/after/around hooks (mark/tag)
│   ├── runner.py                # Compatibility runner helpers
│   ├── const.py                 # TAG_PREFIX, PytestConfigParam
│   ├── mimetype.py              # Mimetype enum, gherkin_suffixes
│   ├── utils.py                 # General utility module
│   ├── tag_expression.py        # Tag expression evaluation
│   ├── model/                   # Core domain model
│   │   ├── __init__.py          # Public re-exports of model classes
│   │   ├── scenario_run.py      # Run, ScenarioRun, FeatureRuntimeBinding (1422 lines)
│   │   ├── stash_access.py      # StashBound, StashAccess pattern
│   │   ├── message_converter.py # Dict <-> cucumber_messages conversion
│   │   ├── message_registry.py  # EnvelopeRegistry, IdentifiableObjectRegistry
│   │   ├── message_serialization.py
│   │   ├── message_validation.py
│   │   ├── message_transport.py
│   │   ├── message_capability.py
│   │   ├── message_capability_inventory.py
│   │   ├── message_status_governance.py
│   │   ├── message_governance_checklist.py
│   │   ├── message_baseline_diff.py
│   │   ├── message_outcome_mapping.py
│   │   ├── message_extension.py
│   │   ├── message_consolidation.py
│   │   ├── heading_validation.py
│   │   ├── execution_message_adapter.py
│   │   ├── cucumber_formatter_adapter.py
│   │   ├── context/
│   │   ├── coverage/
│   │   ├── in_run_converter/
│   │   ├── step/
│   │   └── message_jsonschema/    # JSON Schema for Cucumber Messages
│   ├── plugin/                  # Pytest hook implementations
│   │   ├── scenario_test_collector/  # Feature autoload + batch collection
│   │   │   ├── entrypoint.py        # pytest_addoption, pytest_configure
│   │   │   ├── plugin.py            # ScenarioTestCollector (pytest hooks)
│   │   │   ├── hook.py              # Hook specs
│   │   │   └── const.py
│   │   ├── pickle_runner/           # Scenario execution runtime
│   │   │   ├── entrypoint.py        # pytest_configure, fixtures
│   │   │   ├── plugin.py            # PickleRunner (pytest_runtest_* hooks)
│   │   │   ├── run_transitions.py   # State machine transitions
│   │   │   ├── run_access.py        # Runtime object accessors
│   │   │   ├── hook.py              # PickleRunnerHookSpec
│   │   │   ├── const.py
│   │   │   └── api_compatibility.py
│   │   ├── gherkin_message_reporter/ # Live Cucumber Messages reporter
│   │   │   ├── entrypoint.py        # pytest_configure, xdist remote
│   │   │   ├── plugin.py            # GherkinMessageReporter
│   │   │   ├── session.py
│   │   │   ├── message_stream.py
│   │   │   ├── lifecycle_runtime.py
│   │   │   ├── scenario_runtime.py
│   │   │   ├── step_catalog_runtime.py
│   │   │   ├── hook_catalog_runtime.py
│   │   │   ├── live_formatter_runtime.py
│   │   │   ├── transport_runtime.py
│   │   │   ├── attachment_runtime.py
│   │   │   ├── standalone_renderer.py
│   │   │   ├── html_report.py
│   │   │   ├── stream_relay.py
│   │   │   ├── runtime_assembly.py
│   │   │   ├── runtime_contract.py
│   │   │   ├── runtime_support.py
│   │   │   ├── service_base.py
│   │   │   ├── hook.py
│   │   │   └── resources/          # Jinja2 & Node.js formatter templates
│   │   ├── cucumber_json/          # Cucumber JSON reporter
│   │   ├── struct_bdd/             # YAML/JSON/HOCON/TOML BDD
│   │   ├── code_generator/         # Step code generator
│   │   ├── allure_logger/          # Allure integration
│   │   ├── scenario_reporter/      # Scenario reporting hooks
│   │   ├── scenario_runner/        # Alternative scenario runner
│   │   ├── gherkin_terminal_reporter/ # Terminal output
│   │   ├── cucumber_formatter_support/
│   │   ├── cucumber_json_formatter.py
│   │   ├── cucumber_junit.py
│   │   ├── cucumber_pretty.py
│   │   ├── cucumber_progress.py
│   │   ├── cucumber_progress_bar.py
│   │   ├── cucumber_snippets.py
│   │   ├── cucumber_summary.py
│   │   ├── cucumber_usage.py
│   │   └── cucumber_usage_json.py
│   ├── _gherkin_go/              # Optional Go Gherkin parser backend
│   │   ├── __init__.py           # Public parse() API
│   │   ├── _bridge.py            # ctypes bridge to Go shared library
│   │   ├── _build.py             # setuptools BuildGoCommand
│   │   └── _types.py             # GherkinGoNotAvailable, GherkinParseError
│   ├── compatibility/            # Cross-version pytest/Python shims
│   │   ├── pytest/               # Re-exports of pytest types, outcomes
│   │   ├── importlib/            # resources.py, metadata.py
│   │   ├── parser.py             # ParserProtocol, ParsedFeature
│   │   ├── struct_bdd.py         # STRUCT_BDD_INSTALLED guard
│   │   ├── pathlib.py, path.py
│   │   ├── enum.py, typing.py
│   │   ├── tomllib.py, git.py
│   │   ├── jsonschema.py, allure.py
│   │   └── matrix.py
│   ├── types/                    # Type definitions and exceptions
│   │   ├── exception.py          # FeatureParseError, StepDefinitionNotFoundError
│   │   ├── warning.py            # PytestBDDStepDefinitionWarning
│   │   ├── protocol.py           # Identifiable, MultiLinkedAST, HasPytestStash
│   │   └── json.py               # JSON type aliases
│   ├── util/                     # Utility helpers
│   │   ├── toolz_extra.py        # Functional utilities
│   │   ├── other.py              # IdGenerator, identifier formatting
│   │   ├── data_table.py
│   │   ├── tests_group_ordering.py
│   │   ├── cucumber_formatters.py
│   │   ├── npm_resource.py
│   │   ├── live_reporting.py
│   │   ├── pytest_extra.py       # inject_fixture helper
│   │   ├── inspect_extra.py      # Caller module locals
│   │   ├── packaging.py          # Distribution version
│   │   ├── url.py, webloc.py
│   │   └── toolz_test.py
│   ├── script/                   # CLI entry point scripts
│   │   ├── _feature_tree.py      # Shared feature docs ordering-prefix validation
│   │   ├── compatibility_matrix.py
│   │   ├── render_cucumber_formatters.py
│   │   ├── validate_feature_headings.py
│   │   ├── sync_messages_contract_schemas.py
│   │   └── message_capability_governance.py
│   └── template/                 # Jinja2 templates for code generation
│       └── test.py.jinja2
├── tests/                        # Test suite
│   ├── unit/                     # Fast in-memory unit tests
│   ├── feature/                  # Integration tests (testdir-based)
│   ├── model/                    # Model-level tests
│   ├── message/                  # Message protocol tests
│   ├── messages/                 # Extended message tests
│   ├── messages_coverage/        # Message coverage probes
│   ├── hook/                     # Hook lifecycle tests
│   ├── steps/                    # Step definition tests
│   ├── args/                     # Argument parsing tests
│   ├── library/                  # Library-level integration tests
│   ├── gherkin_integration/      # Gherkin parsing integration tests
│   ├── e2e/                      # End-to-end tests (run features/ directory)
│   │   ├── conftest.py           # Step definitions for Gherkin .feature.md files
│   │   ├── test_e2e.py           # Entry: scenarios(".", ...)
│   │   ├── test_cucumber_formatters.py
│   │   ├── test_xdist_html_reporting.py
│   │   └── fixtures/
│   ├── struct_bdd/               # Struct-BDD tests
│   ├── contract/                 # Contract tests
│   ├── allure_/                  # Allure integration tests
│   ├── compatibility/            # Compatibility matrix tests
│   ├── doc/                      # Documentation tests
│   ├── generation/               # Code generation tests
│   ├── scripts/                  # Script tests
│   ├── build/                    # Build process tests
│   ├── support/                  # Test support utilities
│   └── conftest.py               # Global test conftest (group ordering)
├── features/                     # Executable BDD docs (Gherkin .feature.md files)
│   └── NN Topic/                 # Numbered feature areas
├── specs/                        # Non-executable specs (SpecKit)
│   └── NNN-feature-name/
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       └── ...
├── docs/                         # Sphinx documentation
│   └── ext/                      # Local Sphinx extensions
│       ├── __init__.py
│       └── feature_tree.py       # Feature Markdown validation/copy extension
├── gherkin_go/                   # Go source for gherkin parser shared library
├── scripts/                      # Dev/CI helper scripts
├── pyproject.toml                # Project config, deps, pytest/ruff settings
├── tox.ini                       # Tox configuration for multi-version testing
├── Makefile                      # Build automation
├── uv.lock                       # Lockfile (uv package manager)
├── DEVELOPMENT.rst               # Development guidelines
├── AGENTS.md                     # Agent development guide
├── README.rst                    # Project readme
├── CHANGES.rst                   # Changelog
├── LICENSE.rst                   # MIT License
└── .pre-commit-config.yaml       # Pre-commit hooks
```

## Directory Purposes

**src/pytest_bdd/**: Root of the Python library package. Contains public API, domain model, plugin system, parsers, and utilities. Everything under `src/` layout for clean packaging.

**src/pytest_bdd/model/**: Core domain model. The heart of the runtime. Contains `Run` (session-scoped BDD state), `ScenarioRun` (per-scenario execution state), `FeatureRuntimeBinding` (per-feature parsed data), stash access pattern, and Cucumber Messages protocol handling (conversion, validation, serialization, transport, capability governance).
- Key files: `scenario_run.py` (1422 lines, largest module), `stash_access.py` (188 lines), `message_converter.py`

**src/pytest_bdd/plugin/**: Pytest hook implementations. Each subdirectory is a plugin registered via `pytest11` entry point. Key plugins:
- `scenario_test_collector/` -- Discovers `.feature` files, registers `pytest_collect_file` and `pytest_generate_tests` hooks
- `pickle_runner/` -- Implements `pytest_runtest_*` hooks for scenario and step execution
- `gherkin_message_reporter/` -- Live Cucumber Messages reporting (NDJSON, HTML, formatter bridge to Node.js)
- `struct_bdd/` -- Alternative BDD formats (YAML, JSON, HOCON, TOML)
- Formatter plugins (`cucumber_*.py`) -- Cucumber-compatible output formats

**src/pytest_bdd/compatibility/**: Cross-version abstraction layer that isolates the codebase from pytest and Python version differences. Re-exports pytest types, provides `pathlib` shims, `tomllib` fallbacks, importlib compatibility. All other modules import from here rather than directly from `_pytest` or version-specific stdlib.

**src/pytest_bdd/util/**: Shared utility functions. No business logic, just helper functions used across layers. Includes `toolz_extra.py` (functional composition), `other.py` (IdGenerator, Python identifier formatting), `tests_group_ordering.py` (CI test grouping).

**src/pytest_bdd/types/**: Pure type definitions, exceptions, and protocols. Includes:
- `exception.py` -- `FeatureParseError`, `FeatureConcreteParseError`, `StepDefinitionNotFoundError`, stash errors
- `protocol.py` -- `Identifiable`, `MultiLinkedAST`, `HasPytestStash`
- `warning.py` -- `PytestBDDStepDefinitionWarning`

**src/pytest_bdd/_gherkin_go/**: Optional Go Gherkin parser backend. Private sub-package (underscore prefix). Uses ctypes to call a Go shared library compiled from `gherkin_go/` CGo source. The Python fallback (`gherkin.parser.Parser` in `parser.py`) is always available.

**src/pytest_bdd/script/**: CLI entry points installed as console scripts via `[project.scripts]`. Standalone tools for documentation generation, compatibility matrix, and formatter template rendering. Shared script-adjacent helpers such as `_feature_tree.py` keep feature documentation ordering validation importable without depending on conversion scripts.

**src/pytest_bdd/template/**: Jinja2 templates used for code generation (step definition stubs) and documentation generation (RST feature docs).

**tests/**: Test suite organized by test type and speed tier (configured via `test_group_paths` in `pyproject.toml`):
- `unit/` -- Fastest, in-memory unit tests (instant tier)
- `feature/` -- Integration tests using pytest's `testdir` fixture (medium tier)
- `model/` -- Model-level tests (instant tier)
- `e2e/` -- End-to-end tests that run actual `.feature.md` files from the `features/` directory (external tier)
- `hook/`, `steps/`, `args/` -- Fast tests for hook lifecycle, step definitions, argument parsing

**features/**: Executable BDD documentation. Contains `.feature.md` files (Gherkin scenarios in Markdown) organized into numbered topic areas (01 Tutorial, 02 Feature, etc.). These serve as both documentation and acceptance tests.

**specs/**: Non-executable specification artifacts managed by SpecKit (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`). Each feature has its own numbered directory with spec.md, plan.md, tasks.md, research.md, data-model.md.

**docs/**: Sphinx documentation served via ReadTheDocs. Local extensions live under `docs/ext/`; `feature_tree.py` validates ordered `features/` sources, copies Markdown feature files into the Sphinx source tree during build, and generates MyST toctree content.

**gherkin_go/**: Go source code for the Gherkin parser shared library. Compiled via `go build -buildmode=c-shared` during `python setup.py build_go`. Uses `cucumber/gherkin/go` and `cucumber/messages/go` Go modules.

## Key File Locations

**Entry Points:**
- `src/pytest_bdd/__init__.py`: Public API (lazy imports for `scenario`, `given`, `when`, `then`, `step`)
- `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py`: Collection plugin entry
- `src/pytest_bdd/plugin/pickle_runner/entrypoint.py`: Execution plugin entry
- `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`: Live reporting plugin entry
- `tests/e2e/test_e2e.py`: E2E test runner entry point (`scenarios(".", ...)`)

**Configuration:**
- `pyproject.toml`: Project metadata, dependencies, pytest settings (`[tool.pytest.ini_options]`), ruff settings (`[tool.ruff]`), mypy settings (`[tool.mypy]`), setuptools packaging
- `tox.ini`: Multi-Python-version test matrix
- `.pre-commit-config.yaml`: Pre-commit hooks (ruff, mypy, etc.)
- `uv.lock`: Dependency lockfile for `uv` package manager

**Core Logic:**
- `src/pytest_bdd/model/scenario_run.py`: The central runtime container (Run, ScenarioRun, FeatureRuntimeBinding)
- `src/pytest_bdd/steps.py`: Step definition registration and matching (StepDefinitionManager, 755 lines)
- `src/pytest_bdd/parsers.py`: Step pattern parsing (StepParser hierarchy, 762 lines)
- `src/pytest_bdd/parser.py`: Gherkin file parsing (GherkinParser, MarkdownGherkinParser, 252 lines)
- `src/pytest_bdd/plugin/scenario_test_collector/plugin.py`: ScenarioTestCollector (314 lines, orchestration)
- `src/pytest_bdd/plugin/pickle_runner/plugin.py`: PickleRunner (545 lines, step execution engine)

**Testing:**
- `tests/conftest.py`: Global test configuration (group ordering, parametrization)
- `tests/e2e/conftest.py`: Step definitions for acceptance tests
- `tests/feature/test_steps.py`: Step definition integration tests
- `tests/feature/test_outline.py`: Scenario outline tests
- `tests/unit/`: Unit tests for batch parsing, Go parser, group ordering

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `scenario_locator.py`, `collector_batch.py`)
- Plugin sub-packages: `snake_case/` with `entrypoint.py` (e.g., `scenario_test_collector/entrypoint.py`)
- Test files: `test_*.py` prefix (e.g., `test_steps.py`, `test_outline.py`)
- Jinja2 templates: `*.jinja2` extension
- Private/internal modules: underscore prefix (e.g., `_gherkin_go/_bridge.py`)

**Directories:**
- Plugin directories: `snake_case/` (e.g., `pickle_runner/`, `scenario_test_collector/`)
- Test directories: organized by test type (e.g., `unit/`, `feature/`, `e2e/`)
- Feature file directories: `NN Topic/` (numbered, e.g., `01 Tutorial/`)

**Classes:**
- Pytest plugin classes: `PascalCase` with descriptive names (e.g., `ScenarioTestCollector`, `PickleRunner`, `GherkinMessageReporter`)
- Model classes: `PascalCase` using `attrs` `@define` decorator (e.g., `Run`, `ScenarioRun`, `FeatureRuntimeBinding`)
- Parser implementations: lowercase to match API surface (e.g., class `re`, class `parse`, class `string` in `parsers.py`)
- Public API functions: lowercase (e.g., `scenario()`, `scenarios()`, `given()`, `when()`, `then()`, `step()`)

**Constants:**
- `STASH_KEY`: ClassVar string used by `StashBound` subclasses (e.g., `"_pytest_bdd_batch_parser"`)
- Enum-based: `StrEnum` subclasses (e.g., `HookPhase`, `RunStage`, `RunStatus`, `Mimetype`)

## Where to Add New Code

**New Feature (BDD capability):**
- Primary code: `src/pytest_bdd/` (new module or extend existing)
- Tests: `tests/feature/` for integration, `tests/unit/` for fast tests
- Spec: `specs/NNN-feature-name/` (via SpecKit)

**New Pytest Plugin:**
- Implementation: `src/pytest_bdd/plugin/<plugin_name>/entrypoint.py` + `plugin.py` + `hook.py`
- Registration: Add `pytest11` entry in `pyproject.toml` under `[project.entry-points.pytest11]`
- Tests: Create test directory matching the plugin domain

**New Step Parser Type:**
- Implementation: Add class in `src/pytest_bdd/parsers.py` implementing `StepParserProtocol`
- Register with `StepParser.build()` in `parsers.py` line 125
- Tests: `tests/steps/` for step matching/parsing tests

**New Cucumber Formatter:**
- Implementation: Add `.py` file in `src/pytest_bdd/plugin/` (follow existing pattern like `cucumber_pretty.py`)
- Entry point: Register in `pyproject.toml` `[project.entry-points.pytest11]`
- Optional: Add Jinja2/Node.js template in `plugin/gherkin_message_reporter/resources/` for live mode

**Utilities:**
- Shared helpers: `src/pytest_bdd/util/` (no business logic, only helper functions)
- Cross-version shims: `src/pytest_bdd/compatibility/`
- Type definitions/exceptions: `src/pytest_bdd/types/`

## Special Directories

**src/pytest_bdd/model/message_jsonschema/**: Contains JSON Schema files for Cucumber Messages validation. Generated and committed -- not edited by hand. Used by `message_validation.py` for `jsonschema` validation.

**src/pytest_bdd/plugin/gherkin_message_reporter/resources/**: Contains Jinja2 templates (`.j2`) for generating Node.js formatter bridge scripts and Cucumber formatter adapter scripts. Committed and used by the live formatter runtime.

**src/pytest_bdd/template/**: Jinja2 templates for code generation (test.py stubs) and documentation generation (RST feature docs). Committed.

**features/**: Executable BDD specifications. These `.feature.md` files are both human-readable documentation AND machine-executable tests. The `tests/e2e/` suite runs them directly via `scenarios(".", ...)`.

**specs/**: SpecKit-managed specification artifacts. Each feature gets a numbered directory (`NNN-feature-name/`). Contains non-executable spec docs that drive implementation planning.

**build/**: Build output directory (not committed). Contains compiled Go shared libraries and Python build artifacts.

**dist/**: Distribution build artifacts (not committed). Contains `.whl` and `.tar.gz` packages.

**.planning/**: GSD planning artifacts including codebase maps (this directory). Generated by `/gsd-map-codebase`. Not committed by default but consumed by other GSD commands.

---

*Structure analysis: 2026-05-12*
