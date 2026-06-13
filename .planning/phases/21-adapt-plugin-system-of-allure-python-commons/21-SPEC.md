# Phase 21: Adapt plugin system of allure-python commons - Specification

**Created:** 2026-06-13
**Updated:** 2026-06-14 — architecture revision for hook-based interception
**Ambiguity score:** 0.11 (gate: <= 0.20)
**Requirements:** 9 locked

## Goal

The Allure integration changes from a file-first converter plugin into a pytest-native plugin that consumes `pytest_bdd_message` hook calls **in real-time** and writes Allure 3 results through `allure-python-commons` lifecycle. The plugin architecture follows the patterns established by `allure-pytest` and `allure-pytest-bdd`, adapted for Cucumber Message envelopes as the data source.

## Background

Phase 20 created `pytest_bdd.plugin.allure_cucumber` as a Cucumber Messages NDJSON to Allure JSON converter with a standalone CLI and a pytest wrapper. The current implementation collects `pytest_bdd_message` envelopes into `self.envelopes` but only converts them at `pytest_sessionfinish` (batch mode). This violates the architectural intent: the plugin should intercept messages and produce Allure results **as they arrive** during test execution.

**Current code:**
- `src/pytest_bdd/plugin/allure_cucumber/cli.py` — standalone file-in/file-out converter.
- `src/pytest_bdd/plugin/allure_cucumber/entrypoint.py` — exposes `--allure-cucumber-output` and `--allure-cucumber-messages-in`.
- `src/pytest_bdd/plugin/allure_cucumber/plugin.py` — collects envelopes in `self.envelopes`, converts at session finish.
- `src/pytest_bdd/plugin/allure_cucumber/adapter.py` — batch converter: `convert_to_allure_commons(projections, output_dir)`.
- `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py` — declares `pytest_bdd_message`.
- `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py` — emits Cucumber envelopes via `config.hook.pytest_bdd_message(...)`.

**New wave decision:** Previous independence from `allure-python-commons` is overridden for the pytest plugin path. `allure-pytest` is irrelevant: it may be installed or absent, but this plugin must not depend on it.

**Reference implementations (architectural pattern source):**
- `allure-framework/allure-python/allure-pytest-bdd` — pytest-bdd adapter using `AllureLifecycle` directly, hook-driven step/scenario lifecycle.
- `allure-framework/allure-python/allure-pytest` — pytest adapter using `AllureReporter`, hookwrapper-based test protocol interception.

## Requirements

### R1: pytest-native Allure plugin
Normal pytest usage writes Allure results without manual NDJSON handoff.
- Current: User must coordinate message output and Allure input paths.
- Target: `pytest --allure-cucumber-output <dir>` runs tests and writes Allure results through the plugin.
- Acceptance: A pytest run with only `--allure-cucumber-output <dir>` produces valid Allure result files.

### R2: allure-python-commons backend
The pytest plugin writes through `allure-python-commons`.
- Current: Phase 20 converter emits JSON files directly and has tests forbidding `allure-python-commons`.
- Target: pytest plugin path uses `allure-python-commons` plugin/lifecycle/logger APIs as the output backend.
- Acceptance: Contract test proves pytest plugin imports/uses `allure-python-commons`; obsolete "forbid allure-python-commons" contract is removed or narrowed to standalone converter only.

### R3: No allure-pytest coupling
The plugin does not require or integrate with `allure-pytest`.
- Current: `allure-pytest` is not part of the plugin path.
- Target: Plugin behavior is identical whether `allure-pytest` is installed or not.
- Acceptance: Tests run in environments with `allure-pytest` absent and, where feasible, present without duplicate results or registration conflicts.

### R4: Real-time pytest_bdd_message interception (NEW — supersedes batch collection)
The plugin intercepts `pytest_bdd_message` hook calls and produces Allure results **during test execution**, not at session finish.
- Current: `AllureCucumberPlugin.pytest_bdd_message()` appends to `self.envelopes` list; conversion at `pytest_sessionfinish` only.
- Target: Each `pytest_bdd_message` envelope is deserialized, mapped, and written through `AllureLifecycle` incrementally. The plugin maintains stateful tracking of test case lifecycle transitions (TestCaseStarted → StepStarted → StepFinished → TestCaseFinished).
- Acceptance: Allure result files are written to the output directory incrementally during test execution (verifiable by watching directory during `pytest -s`).

### R5: pytest-bdd-ng hook compatibility
Existing pytest-bdd-ng lifecycle hooks can drive Allure reporting.
- Current: Reporting depends on serialized Cucumber Messages file shape.
- Target: Data produced by pytest-bdd-ng hook calls is sufficient to create scenarios, steps, attachments, descriptions, tags, failures, and run-level state.
- Acceptance: E2E feature with background, rule, examples, doc strings, data tables, tags, attachments, passing scenario, assertion failure, and exception failure renders correctly in Allure.

### R6: NDJSON import mode
The plugin can consume an existing filesystem NDJSON file without running test scenarios.
- Current: Standalone CLI handles this as primary path.
- Target: pytest plugin supports `--allure-cucumber-messages-in <path>` as import mode; in this mode it processes the file and writes Allure output without requiring collected pytest-bdd scenarios to run.
- Acceptance: `pytest --allure-cucumber-output <dir> --allure-cucumber-messages-in <messages.ndjson>` produces Allure results from the file and does not execute BDD scenarios as the source of truth.

### R7: Single ingestion pipeline
Hook mode and NDJSON import mode share conversion semantics.
- Current: Runtime and file paths can drift.
- Target: Both modes feed the same envelope-to-Allure adapter before writing through `allure-python-commons`.
- Acceptance: Golden test compares hook-mode and NDJSON-import-mode output for the same message stream and verifies matching test names, steps, statuses, tags, descriptions, parameters, and attachments.

### R8: xdist total report
Distributed runs produce one complete Allure result set.
- Current: Existing message reporter has xdist message batching/manifest plumbing; Allure plugin does not own total aggregation.
- Target: Workers forward/report message streams; controller merges them and writes one total Allure result directory.
- Acceptance: `pytest -n 2 --allure-cucumber-output <dir>` over multiple BDD scenarios produces one Allure report containing all scenarios, all attachments, no duplicate scenario results, and correct run-level status.

### R9: Plugin architecture mirrors allure-pytest/allure-pytest-bdd patterns (NEW)
The internal plugin structure follows the established patterns from the reference implementations.
- **Listener class**: A `MessageDrivenListener` that receives Cucumber envelope events and calls `AllureLifecycle` methods.
- **allure-commons hook implementation**: A separate `AllureCucumberApiHooks` class registered with `allure_commons.plugin_manager` that implements allure-commons hooks (`start_step`, `stop_step`, `attach_data`, etc.).
- **Plugin registration**: `entrypoint.py` registers both the listener and the API hooks as cleanup-registered plugins via `config.pluginmanager.register()` and `allure_commons.plugin_manager.register()`.
- Acceptance: Plugin file structure matches `entrypoint.py` + `listener.py` + `api_hooks.py` + `message_adapter.py`; registration follows the `cleanup_factory` pattern from allure-pytest.

## Boundaries

**In scope:**
- New pytest-native Allure plugin behavior using `allure-python-commons`.
- Real-time `pytest_bdd_message` interception (hook-based, not batch).
- `--allure-cucumber-output <dir>` normal mode.
- `--allure-cucumber-messages-in <path>` import mode name and behavior.
- Compatibility with `allure-pytest` absent or present, without depending on it.
- Shared hook/NDJSON ingestion adapter.
- xdist total aggregation for Allure output.
- Updated contracts, docs, and e2e UAT for new behavior.

**Out of scope:**
- Depending on `allure-pytest` — plugin is built around pytest-bdd-ng hooks.
- Preserving old `--allure-cucumber-messages` as the main user API — replaced by `--allure-cucumber-messages-in`.
- Keeping the "no allure-python-commons" decision for pytest plugin path — explicitly overridden.
- Changing pytest-bdd-ng scenario execution semantics — reporting only.
- Building or serving HTML report as plugin responsibility — plugin writes `allure-results`; HTML generation remains external/Docker/UAT.

## Constraints

- Use `attrs` for new structured model classes.
- Plugin structure follows: `entrypoint.py` + `listener.py` + `api_hooks.py` + `message_adapter.py`.
- Cross-plugin communication must use pytest/pluggy hooks or public contracts, not direct imports of another plugin's internals where avoidable.
- Worker/controller behavior must not require shared mutable filesystem writes from workers as final truth.
- Normal pytest mode must not require user to pass `--messages-ndjson`.
- Plugin architecture must follow `allure-pytest` / `allure-pytest-bdd` patterns (see Architecture: Reference Mapping section).

## Acceptance Criteria

- [ ] `pytest --allure-cucumber-output <dir>` creates valid Allure result files without `--messages-ndjson`.
- [ ] Plugin uses `allure-python-commons` for pytest output.
- [ ] Plugin does not import or require `allure-pytest`.
- [ ] Plugin implements `pytest_bdd_message` as a hookimpl (not hookwrapper) that feeds each envelope to `AllureLifecycle` incrementally.
- [ ] Allure results are written incrementally during test execution (not batch at session finish).
- [ ] Plugin architecture follows `allure-pytest` / `allure-pytest-bdd` patterns:
  - `entrypoint.py` — option registration and plugin registration via `cleanup_factory`
  - `listener.py` — `MessageDrivenListener` class with lifecycle methods
  - `api_hooks.py` — `AllureCucumberApiHooks` registered with `allure_commons.plugin_manager`
  - `message_adapter.py` — `CucumberEnvelopeAdapter` state machine for envelope routing
- [ ] `EnvelopeStateCache` tracks `test_case_started_id → Allure uuid` mappings (following `allure-pytest`'s `ItemCache` pattern).
- [ ] `--allure-cucumber-messages-in <path>` imports NDJSON and writes Allure output without using running scenarios as source of truth.
- [ ] Hook mode and NDJSON import mode produce equivalent semantic results for the same message stream.
- [ ] `pytest -n 2 --allure-cucumber-output <dir>` produces one total report with all scenarios and attachments.
- [ ] Full-surface e2e Allure report validates scenario count, step counts, tags, attachments, descriptions, tables/doc strings, and statuses.
- [ ] Obsolete contracts/docs claiming pytest Allure integration must avoid `allure-python-commons` are removed or scoped to the standalone converter only.
- [ ] Reference implementations are cited in architecture docs with specific file paths for validation.

## Architecture: Message Flow

```
pytest_bdd_message(config, message)     # Called by LifecycleService for each envelope
       │
       ▼
AllureCucumberPlugin.pytest_bdd_message()  # hookimpl (NOT hookwrapper)
       │
       ├─ Deserialize envelope → ExecutionProjection
       │
       ├─ Route by payload_kind:
       │   ├─ test_case_started     → lifecycle.schedule_test_case(uuid)
       │   ├─ test_step_started     → lifecycle.start_step(uuid, parent)
       │   ├─ test_step_finished    → lifecycle.stop_step(uuid, status)
       │   ├─ test_case_finished    → lifecycle.update_test_case(uuid) → lifecycle.write_test_case(uuid)
       │   ├─ attachment            → lifecycle.attach_data/attach_file()
       │   ├─ test_run_started      → (initialize run context)
       │   └─ test_run_finished     → (finalize run context)
       │
       ▼
AllureLifecycle (allure-python-commons)
       │
       ▼
AllureFileLogger → writes *-result.json and *-container.json to output_dir
```

## Architecture: File Structure

```text
src/pytest_bdd/plugin/allure_cucumber/
├── __init__.py
├── entrypoint.py          # pytest_addoption, pytest_configure, pytest_unconfigure
├── listener.py            # MessageDrivenListener — receives pytest_bdd_message, maps to lifecycle
├── api_hooks.py           # AllureCucumberApiHooks — implements allure_commons hooks
├── message_adapter.py     # CucumberEnvelopeAdapter — envelope → AllureLifecycle state machine
├── plugin.py              # (deprecated — kept for backward compat, delegates to listener)
├── adapter.py             # (deprecated — batch converter, kept for import mode only)
├── cli.py                 # (standalone converter, unchanged)
└── converter/             # (Phase 20 converter, unchanged)
```

## Architecture: Reference Mapping

| Reference Pattern | Source File | Our Adaptation |
|-------------------|-------------|----------------|
| `PytestBDDListener.__init__(lifecycle)` | `allure-pytest-bdd/src/pytest_bdd_listener.py:16` | `MessageDrivenListener.__init__(lifecycle, output_dir)` |
| `@pytest.hookimpl pytest_bdd_before_scenario` | `allure-pytest-bdd/src/pytest_bdd_listener.py:23` | `pytest_bdd_message` routes `test_case_started` → `schedule_test_case` |
| `@pytest.hookimpl pytest_bdd_before_step` | `allure-pytest-bdd/src/pytest_bdd_listener.py:41` | `pytest_bdd_message` routes `test_step_started` → `start_step` |
| `@pytest.hookimpl pytest_bdd_after_step` | `allure-pytest-bdd/src/pytest_bdd_listener.py:49` | `pytest_bdd_message` routes `test_step_finished` → `stop_step` |
| `@pytest.hookimpl(hookwrapper=True) pytest_runtest_makereport` | `allure-pytest-bdd/src/pytest_bdd_listener.py:57` | `pytest_bdd_message` routes `test_case_finished` status from envelope |
| `AllurePytestBddApiHooks(config, lifecycle)` | `allure-pytest-bdd/src/allure_api_listener.py:15` | `AllureCucumberApiHooks(config, lifecycle)` |
| `allure_commons.plugin_manager.register(listener)` | `allure-pytest-bdd/src/plugin.py:81` | `allure_commons.plugin_manager.register(listener)` |
| `cleanup_factory(plugin)` | `allure-pytest-bdd/src/plugin.py:77` | `cleanup_factory(plugin)` — same pattern |
| `AllureLifecycle` for step/test management | `allure-pytest-bdd/src/pytest_bdd_listener.py:1` | `AllureLifecycle` — same API |
| `AllureFileLogger(report_dir, clean)` | `allure-pytest-bdd/src/plugin.py:83` | `AllureFileLogger(report_dir)` — same API |
| `ItemCache` for UUID management | `allure-pytest/src/listener.py:283` | `EnvelopeStateCache` — tracks TestCaseStarted → uuid mapping |

---

*Phase: 21-adapt-plugin-system-of-allure-python-commons*
*Spec created: 2026-06-13*
*Spec updated: 2026-06-14 — architecture revision for hook-based interception*
*Next step: Implement MessageDrivenListener with real-time envelope processing*
