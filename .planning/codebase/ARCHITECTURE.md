---
last_mapped_commit: c59470a9bc50f5ae0f628a572832a5b614d862a7
mapped_at: 2026-05-12
focus: arch
---

# Architecture

**Analysis Date:** 2026-05-12

## Pattern Overview

**Overall:** Plugin-Oriented Architecture (POA) layered on pytest's hook + plugin system

**Key Characteristics:**
- pytest plugin via `pytest11` entry points in `pyproject.toml` (lines 86-104) -- registers 17 plugins covering collection, execution, reporting, formatting, and struct-BDD
- `config.stash` is the canonical runtime state container -- all session-scoped objects (`Run`, `FeatureBatchParser`, `IdGenerator`) are stored/retrieved via `StashBound` subclasses in `src/pytest_bdd/model/stash_access.py`
- Hook-driven lifecycle -- collection and execution decomposed into fine-grained pytest-bdd hooks that formatters and custom plugins intercept
- Public API is thin wrappers over pytest marks + fixtures -- `scenario()`, `given()`, `when()`, `then()` build pytest-compatible decorators
- Polymorphic step parsing -- `StepParser` ABC with concrete implementations: `re`, `parse`, `cfparse`, `cucumber_expression`, `cucumber_regular_expression`, `string`, and `heuristic` (tries all)
- Optional Go parser backend via ctypes shared library in `src/pytest_bdd/_gherkin_go/` for faster Gherkin parsing
- Cucumber Messages protocol compliance for interoperable reporting

## Layers

**Plugin Layer (pytest hooks):**
- Purpose: Connect pytest runtime events to BDD semantics -- file collection, feature parsing, scenario parametrization, step execution, reporting
- Location: `src/pytest_bdd/plugin/`
- Contains: Pytest hook implementations (`pytest_collect_file`, `pytest_generate_tests`, `pytest_runtest_*` hooks), formatter plugins (`cucumber_json/`, `cucumber_pretty.py`, `cucumber_junit.py`, etc.), live reporter (`gherkin_message_reporter/`), struct-BDD plugin (`struct_bdd/`), code generator (`code_generator/`)
- Depends on: model layer, parser, steps, scenario_locator
- Used by: pytest runtime (discovered via `pytest11` entry points)

**Model Layer (domain objects):**
- Purpose: Represent BDD runtime state -- Run, ScenarioRun, FeatureRuntimeBinding, lifecycle tracking, message conversion, governance
- Location: `src/pytest_bdd/model/`
- Contains: `Run` (session-scoped container), `FeatureRuntimeBinding` (per-feature), `ScenarioRun` (per-test), `StashBound`/`StashAccess` (stash access pattern), Cucumber message protocol conversion (`message_converter.py`), validation (`message_validation.py`), serialization (`message_serialization.py`), transport (`message_transport.py`), governance (`message_capability.py`, `message_status_governance.py`, `message_governance_checklist.py`), heading validation (`heading_validation.py`)
- Key files: `scenario_run.py` (1422 lines, core runtime), `stash_access.py` (188 lines), `message_converter.py`, `message_registry.py`
- Depends on: `cucumber-messages`, `attrs`, `gherkin` (pickles compiler)
- Used by: plugin layer, collector layer, public API

**Collector Layer (test discovery):**
- Purpose: Discover `.feature` files, parse Gherkin, build scenario parametrized tests
- Location: `src/pytest_bdd/collector.py`, `collector_batch.py`, `scenario_locator.py`, `feature_locator.py`
- Contains: `FeatureFileModule` (pytest collector for feature files), `FeatureBatchParser` (lazy-batched async parsing via `asyncio` + `multiprocessing`), `FileScenarioLocator` (local file globs), `UrlScenarioLocator` (async HTTP fetch), `ScenarioLocatorBuilder` (binds marks to locators)
- Depends on: parser layer, model layer, `plugin/scenario_test_collector`
- Used by: `plugin/scenario_test_collector/plugin.py`

**Parser Layer (Gherkin parsing):**
- Purpose: Parse `.feature` files into `GherkinDocument` + `Source` objects
- Location: `src/pytest_bdd/parser.py` (Python parser), `src/pytest_bdd/_gherkin_go/` (Go parser backend)
- Contains: `BaseParser` (normalize, emit parse errors), `GherkinParser` (plain Gherkin via `gherkin.parser.Parser`), `MarkdownGherkinParser` (Markdown Gherkin via `GherkinInMarkdownTokenMatcher`), Go ctypes bridge (`_bridge.py`, `_build.py`, `_types.py`)
- Depends on: `gherkin-official` (Python), Go shared library compiled from `gherkin_go/` (Go), `cucumber-messages`
- Used by: `FileScenarioLocator`, `UrlScenarioLocator`

**Step Definition Layer:**
- Purpose: Register and match step definitions to scenario steps
- Location: `src/pytest_bdd/steps.py` (755 lines), `parsers.py` (762 lines)
- Contains: `StepDefinitionManager` (registry + matcher), `StepDefinitionManager.Registry` (set of `Definition` objects with parent chain for hierarchical lookup), `StepDefinitionManager.Matcher` (three-pass matching: strict type match, unspecified/UNKNOWN type, liberal cross-keyword), `StepDefinitionManager.Definition` (wraps a `@given`/`@when`/`@then` function with parser, converters, target fixtures), `StepParser` hierarchy (7 parser types: `re`, `parse`, `cfparse`, `cucumber_expression`, `cucumber_regular_expression`, `string`, `heuristic`)
- Depends on: `cucumber-messages`, `cucumber-expressions`, `parse`, `parse_type`
- Used by: `plugin/pickle_runner/plugin.py` (step execution)

**Public API Layer (user-facing):**
- Purpose: Decorators and functions that test authors import: `from pytest_bdd import scenario, scenarios, given, when, then, step`
- Location: `src/pytest_bdd/__init__.py` (lazy imports via PEP 562 `__getattr__`), `scenario.py`, `steps.py` (top-level functions), `hook.py` (before/after/around hooks)
- Contains: `scenario()`, `scenarios()`, `given()`, `when()`, `then()`, `step()`, `before_mark`, `after_mark`, `before_tag`, `after_tag`, `around_mark`, `around_tag`
- Depends on: step definition layer, pytest marks/fixtures
- Used by: test files

**Compatibility Layer (cross-version):**
- Purpose: Abstract over pytest/Python version differences
- Location: `src/pytest_bdd/compatibility/`
- Contains: Re-exports of pytest types (`pytest/__init__.py`), `pathlib` shims (`pathlib.py`), `enum` (`enum.py`), `importlib` (`importlib/`), `parser` protocol (`parser.py`), `pytest` outcomes (`pytest/outcomes.py`), `tomllib` shim (`tomllib.py`), `struct_bdd` guard (`struct_bdd.py`), `git.py`, `jsonschema.py`, `typing.py`, `allure.py`, `matrix.py`
- Depends on: pytest stdlib
- Used by: all other layers

**Utility Layer:**
- Purpose: Shared helpers
- Location: `src/pytest_bdd/util/`
- Contains: `toolz_extra.py` (functional utilities), `other.py` (IdGenerator, Python identifier formatting), `data_table.py`, `tests_group_ordering.py` (test grouping for CI), `cucumber_formatters.py` (formatter detection), `npm_resource.py` (Node.js resource management), `live_reporting.py`, `pytest_extra.py`, `inspect_extra.py`, `packaging.py`, `url.py`, `webloc.py`
- Depends on: stdlib
- Used by: all other layers

## Data Flow

**Feature Collection and Test Generation Flow:**

1. `pytest_collect_file` hook in `plugin/scenario_test_collector/plugin.py` checks file suffix (matches `.feature`, `.gherkin`, or link suffixes `.url`, `.desktop`, `.webloc`)
2. `FeatureFileCollector` in `collector.py` wraps the feature path via `scenarios()` call which builds a pytest mark + fixture stack (`gherkin_document`, `pickle`, `feature_source`)
3. `FeatureBatchParser` in `collector_batch.py` optionally accumulates file paths during directory walk, then flushes through concurrent `asyncio` reads + `multiprocessing` parses on first `get()` call
4. `pytest_generate_tests` hook in `plugin/scenario_test_collector/plugin.py` resolves the `PYTEST_BDD_SCENARIOS_MARK` mark via `ScenarioLocatorBuilder` in `feature_locator.py`, creating `FileScenarioLocator` or `UrlScenarioLocator`
5. Locator calls `parser.parse(config, path, uri, encoding=...)` in `scenario_locator.py` -- uses either `GherkinParser` or `MarkdownGherkinParser` from `parser.py`
6. `FeatureRuntimeBinding.ensure_pickles()` compiles pickles via `gherkin.pickles.compiler.Compiler` and indexes them into `Run.identifiable_registry`
7. `metafunc.parametrize("gherkin_document, pickle, feature_source", ...)` creates one parametrized test per scenario (including one per Examples table row)

**Scenario Execution Flow:**

1. `pytest_runtest_setup` hook in `plugin/pickle_runner/plugin.py` checks `PYTEST_BDD_MARK`, resolves runtime params from `item.callspec.params`, calls `Run.create_scenario_run(request, gherkin_document=..., feature_source=..., pickle=...)` which creates a `ScenarioRun` with lifecycle state machine
2. `pytest_runtest_call` hook resolves fixtures `gherkin_document`, `pickle`, `feature_source` via `request.getfixturevalue()`, then invokes the BDD hook chain:
   - `pytest_bdd_before_scenario` hook via `_invoke_bdd_hook()` -- calls `apply_transition()` in `plugin/pickle_runner/run_transitions.py` to advance the `ScenarioRun` state machine to `RunStage.scenario_running`
   - `pytest_bdd_run_scenario` hook -- fetches `steps_left` fixture (a `deque`), extends with `pickle.steps`, gets step dispatcher via `pytest_bdd_get_step_dispatcher` hook
   - Step dispatcher (default implementation in `plugin/pickle_runner/plugin.py` lines 272-290) pops steps from deque and calls `pytest_bdd_run_step` for each
   - `pytest_bdd_run_step` implementation in pickle_runner:
     a. Creates `StepRun` object on `ScenarioRun`, enriches with keyword, doc_string, data_table, line_number from AST
     b. Calls `_match_to_step()` which invokes `pytest_bdd_match_step_definition_to_step` hook (implemented by `ScenarioTestCollector` in `plugin/scenario_test_collector/plugin.py` lines 208-228)
     c. Step matching uses `StepDefinitionManager.Matcher` with three passes: strict (exact type match), unspecified (UNKNOWN type), liberal (cross-keyword with config toggle). Parent registries are traversed if no match found
     d. Step function executes as a pytest fixture via `call_fixture_func` -- step parameters parsed from step text are injected as fixtures
     e. Each step fires: `pytest_bdd_before_step` -> `pytest_bdd_before_step_call` -> step function call -> `pytest_bdd_after_step` (or `pytest_bdd_step_error` on exception)
     f. Step return value injected as target fixture via `_inject_target_fixtures()`
   - `pytest_bdd_after_scenario` in finally block (always runs)
3. `pytest_runtest_teardown` hook in `plugin/pickle_runner/plugin.py` yields (to let fixture teardown run), then calls `Run.pop_scenario_run()`

**State Management:**
- `config.stash` is the central state store -- all `StashBound` subclasses define `STASH_KEY` classvar and use `from_stash()`, `initialize_in_stash()`, `find_in_stash()` accessors via `StashAccess` in `model/stash_access.py`
- `Run` (`STASH_KEY` in `model/scenario_run.py`) holds session-level runtime: feature bindings dict (`{uri: FeatureRuntimeBinding}`), scenario runs stack, reporting lifecycle state, identifiable registry, reference resolver state, context error state
- `ScenarioRun` tracks per-scenario execution stage transitions: `RunStage.idle` -> `scenario_setup` -> `scenario_running` -> `step_running` -> `scenario_teardown` -> `finished`
- `StepDefinitionManager.Registry` chains parent registries -- test modules register local step definitions, conftest.py registries become parents, enabling hierarchical step resolution across directory boundaries

## Key Abstractions

**StashBound:**
- Purpose: Base class for objects stored/retrieved from pytest's `config.stash` by type key
- Examples: `Run`, `FeatureBatchParser`, `IdGenerator`, `_ReporterStateEntry`
- Location: `src/pytest_bdd/model/stash_access.py`
- Pattern: ClassVar `STASH_KEY` (string key), classmethods `from_stash(stash)`, `find_in_stash(stash)`, instance methods `initialize_in_stash(stash)`, `set_in_stash(stash)`. Backed by `StashAccess` static methods operating on `pytest.Stash`

**Run:**
- Purpose: Session-scoped container for the entire BDD test run
- Location: `src/pytest_bdd/model/scenario_run.py` (defined as `@define` class within an automated section)
- Key methods: `create_scenario_run(request, gherkin_document, pickle, feature_source)`, `pop_scenario_run(request)`, `ensure_feature_binding(gherkin_document, source, filename)`, `index_identifiable_tree(nodes)`, `require_active_scenario_run(hook_name)`
- Stores: feature bindings dict, scenario runs stack, reporting state, identifiable registry, reference resolver state

**FeatureRuntimeBinding:**
- Purpose: Per-feature-file runtime data holding the `GherkinDocument`, compiled `Pickle` objects, and AST node resolution capabilities
- Location: `src/pytest_bdd/model/scenario_run.py`
- Key methods: `ensure_pickles(id_generator)`, `resolve_node(object_id)`, `linked_ast_nodes_for(obj)`, `pickle_table_rows_breadcrumb(pickle)`, `pickle_ast_scenario(pickle)`, `index_runtime_objects()`

**ScenarioRun:**
- Purpose: Per-scenario execution state tracking
- Location: `src/pytest_bdd/model/scenario_run.py`
- Pattern: State machine transitioning through `RunStage` values, driven by `apply_transition()` in `plugin/pickle_runner/run_transitions.py`
- Contains: `request`, `active_objects` (feature, scenario, step, previous_step refs), `stage`, `step_run` (current step data), `status`

**StepDefinitionManager:**
- Purpose: Registry of step definitions with hierarchical lookup and multi-pass matching
- Location: `src/pytest_bdd/steps.py`
- Sub-components:
  - `Registry` -- set of `Definition` objects, optional parent chain (`self.parent`), auto-injection of `step_registry` pytest fixture, auto-registration from decorated module callables
  - `Matcher` -- three-pass matching: strict (exact `PickleStepType` match), unspecified (UNKNOWN type match), liberal (cross-keyword, controlled by `--liberal-steps` CLI flag or `liberal_steps` ini option)
  - `Definition` -- wraps a decorated Python function with: `func`, `type_` (step keyword type), `parser` (StepParser), `converters`, `target_fixtures`, `fixtures_mapped_from_step_definition`, `as_message()` (Cucumber Messages StepDefinition output)

**StepParser:**
- Purpose: Polymorphic step pattern parsing -- extract arguments from step text strings
- Location: `src/pytest_bdd/parsers.py`
- Implementations (all implementing `StepParserProtocol`):
  - `string` -- exact match, no arguments (`StepDefinitionPatternType.pytest_bdd_string_expression`)
  - `re` -- Python regex with named groups (`StepDefinitionPatternType.pytest_bdd_regular_expression`)
  - `parse` -- parse library format strings (`StepDefinitionPatternType.pytest_bdd_parse_expression`)
  - `cfparse` -- parse_type library, extends parse with cardinality (`StepDefinitionPatternType.pytest_bdd_cfparse_expression`)
  - `cucumber_expression` -- Cucumber expression syntax (`StepDefinitionPatternType.cucumber_expression`)
  - `cucumber_regular_expression` -- Cucumber regular expression (`StepDefinitionPatternType.regular_expression`)
  - `heuristic` -- tries cucumber_expression, cfparse, then regex in priority order (`StepDefinitionPatternType.pytest_bdd_heuristic_expression`)
- Pattern: All implement `is_matching(request, name)`, `parse_arguments(request, name, anonymous_group_names)`, `arguments` property, `__str__()`

**ScenarioLocatorFilterMixin:**
- Purpose: Resolve feature files to Gherkin documents, compile pickles, filter scenarios
- Location: `src/pytest_bdd/scenario_locator.py`
- Subclasses: `FileScenarioLocator` (local file path globbing), `UrlScenarioLocator` (async HTTP fetch via `aiohttp`, writes to temp file for parsing)
- Pattern: `resolve(config, observer=None)` yields `(GherkinDocument, Pickle, Source)` tuples, with observer callbacks (`on_source_loaded`, `on_feature_loaded`, `on_pickle_loaded`) for plugin notification

## Entry Points

**pytest11 plugin registration:**
- Location: `[project.entry-points.pytest11]` section in `pyproject.toml` (lines 86-104)
- Triggers: pytest auto-discovers plugins on startup via setuptools entry points
- Key plugins and their domains:
  - `pytest-bdd-scenario-test-collector` (collection) -> `plugin/scenario_test_collector/entrypoint.py`
  - `pytest-bdd-scenario-runner` (execution) -> `plugin/pickle_runner/entrypoint.py`
  - `pytest-bdd-gherkin-message-reporter` (live reporting) -> `plugin/gherkin_message_reporter/entrypoint.py`
  - `pytest-bdd-struct-bdd` (YAML/JSON BDD) -> `plugin/struct_bdd/entrypoint.py`
  - 12 formatter entry points -> `plugin/cucumber_json_formatter.py`, `plugin/cucumber_junit.py`, `plugin/cucumber_pretty.py`, `plugin/cucumber_progress.py`, `plugin/cucumber_progress_bar.py`, `plugin/cucumber_snippets.py`, `plugin/cucumber_summary.py`, `plugin/cucumber_usage.py`, `plugin/cucumber_usage_json.py`, `plugin/cucumber_json/entrypoint.py`
  - `pytest-bdd-code-generator` -> `plugin/code_generator/entrypoint.py`
  - `pytest-bdd-allure-logger` -> `plugin/allure_logger/entrypoint.py`

**Public API:**
- Location: `src/pytest_bdd/__init__.py` (44 lines)
- Imports: Uses PEP 562 `__getattr__` for lazy loading of `given`, `when`, `then`, `step`, `scenario`, `scenarios`, `FeaturePathType`, `PytestBDDStepDefinitionWarning`
- Triggers: Test author writes `from pytest_bdd import scenario, given, when, then`
- Responsibilities: Expose BDD decorators, scenario binding, step definition keywords, and warnings

**CLI Scripts:**
- Location: `[project.scripts]` in `pyproject.toml`
- `compatibility_matrix` -> `script/compatibility_matrix.py` -- Python/pytest version compatibility matrix generation
- `render_cucumber_formatters` -> `script/render_cucumber_formatters.py` -- generate formatter adapter templates

**Build-time entry point:**
- Location: `[tool.setuptools.cmdclass] build_go` in `pyproject.toml` (line 418)
- `build_go` -> `pytest_bdd._gherkin_go._build.BuildGoCommand` -- compiles Go shared library during `python setup.py build_go`

## Error Handling

**Strategy:** Exceptions propagate through pytest hook chain with `__tracebackhide__ = True` set for clean error messages in step execution

**Patterns:**
- Parse errors: `FeatureConcreteParseError` in `types/exception.py` wraps `gherkin.errors.CompositeParserException` with source context (line number, source line, URI). Emitted as Cucumber `ParseError` messages via `BaseParser.emit_parse_error()`
- Step lookup: `StepDefinitionNotFoundError` in `types/exception.py` captures undefined step diagnostics and calls `pytest_bdd_step_func_lookup_error` hook for snippet generation
- Stash integrity: `PytestBDDStashLookupError`, `PytestBDDStashTypeMismatchError`, `PytestBDDStashAlreadyInitializedError` in `types/exception.py` guard against stash misconfiguration
- Hook failures: `try/finally` in `plugin/pickle_runner/plugin.py` ensures `pytest_bdd_after_scenario` always runs; step execution errors fire `pytest_bdd_step_error` hook before re-raising
- Collection errors: `continue_on_collection_errors` pytest config option (`PytestConfigParam.CONTINUE_ON_COLLECTION_ERRORS` in `const.py`) allows skipping unparseable features during collection

## Cross-Cutting Concerns

**Logging:** Standard `logging.getLogger(__name__)` used in `_gherkin_go/__init__.py` (Go parser availability), `collector_batch.py` (batch collection), and `plugin/gherkin_message_reporter/` (live reporting transport)

**Validation:** JSON Schema validation for Cucumber Messages via `jsonschema` in `model/message_validation.py`; heading validation for feature files in `model/heading_validation.py`; capability governance in `model/message_capability.py` and `model/message_status_governance.py`

**Authentication:** Not applicable -- no built-in auth; URL-based feature loading (`UrlScenarioLocator`) uses standard HTTPS with `certifi` CA certificates

**Multiprocessing:** `FeatureBatchParser` uses `multiprocessing.Pool` for parallel Gherkin parsing; `pytest-xdist` integration via `plugin/gherkin_message_reporter/entrypoint.py` (`pytest_xdist_getremotemodule`)

---

*Architecture analysis: 2026-05-12*
