# Contract: Execution Context Ownership Boundary

## Scope

Defines ownership of runtime execution state after removal of `src/pytest_bdd/model/gherkin_document/core.py::Feature` from parser, locator, hook, fixture, and reporting boundaries.

## Canonical Runtime Root

- Session root: `Run`
- Scenario root: `ScenarioRun`
- Feature-level state: `Run.feature_bindings_by_uri`
- Shared stash transport:
  - `Run` stash key: `_pytest_bdd_run`
  - Envelope registry stash key: `_pytest_bdd_envelope_registry`
  - ID generator stash key: `_pytest_bdd_id_generator`

## Writers (Execution and Collection Layers)

Allowed writers:
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/parser.py`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/scenario_locator.py`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/scenario_test_collector/plugin.py`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/scenario_run.py`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/plugin.py`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/run_transitions.py`

Writer obligations:
- Register or update `FeatureRuntimeBinding` records in `Run`.
- Maintain active `ScenarioRun` bindings for `gherkin_document`, `feature_source`, `pickle`, and step objects.
- Maintain lifecycle refs and `ReportingLifecycleState`.
- Publish `Run`, `EnvelopeRegistry`, and `pytest_bdd_id_generator` into `config.stash`.

## Readers (Reporting and Consumer Layers)

Read-only consumers:
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/scenario_reporter/report.py`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/allure_logger/plugin.py`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/code_generator/plugin.py`

Reader obligations:
- Resolve state via `Run.from_pytest_stash(...)`, `Run.active_scenario_run`, and run-owned feature binding helpers.
- Never bootstrap or mutate runtime context.
- Emit deterministic diagnostics when required context bindings are missing.

## Prohibited Runtime Surface

The following are forbidden in hooks, fixtures, locator callbacks, and reporters:
- `src/pytest_bdd/model/gherkin_document/core.py::Feature`
- feature-wrapper-specific helper methods
- reporter-local `current_<item>` mirrors
- reporter-side calls to context bootstrap/mutation APIs
- ad-hoc runtime-service attributes such as `config.pytest_bdd_id_generator`
- storing `ScenarioRun` directly in `config.stash`

## Naming Semantics Contract

- `pickle` means executable runtime scenario object (`cucumber_messages.Pickle`).
- `scenario` means Gherkin AST `Scenario` semantics only.
- `feature` in runtime context means a feature document identity or run-owned feature binding, not a `Feature` adapter instance.

## Validation Requirements

- Hook tests verify all plugins can consume `run: Run` and recover active `ScenarioRun` safely.
- Fixture/API tests verify `Feature` is not exposed on the runtime surface.
- Collection tests verify the feature pipeline works with `Source`, `GherkinDocument`, and `Pickle` only.
