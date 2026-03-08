# Quickstart: Execution Context Reporting Consistency

## Preconditions

- Repository root: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng`
- Branch: `009-execution-context-reporting`
- Python environment: `conda` env `pytest-bdd-ng-py314`

## 1. Validate Collection Without `Feature`

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/hook/test_scenario_locator_pipeline.py \
  tests/model/gherkin_document/test_feature_context_lookup.py -q
```

Expected:
- Locators and collectors operate on `Source`, `GherkinDocument`, and `Pickle`.
- No collection callback constructs or consumes `src/pytest_bdd/model/gherkin_document/core.py::Feature`.
- Feature-level AST lookup state resolves through `Run`-owned bindings.

## 2. Validate Runtime Hook and Fixture Surface

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/compatibility/test_hook_run_api_surface.py \
  tests/hook/test_run_scenario_runtime_unit.py \
  tests/hook/test_scenario_run_model.py -q
```

Expected:
- Hooks receive `run: Run` and recover active runtime objects from context.
- Fixtures expose `gherkin_document`, `feature_source`, `pickle`, and `run_context`.
- No runtime fixture named `feature` or `scenario` remains in the executable-scenario API surface.

## 3. Validate Reporter and Scenario Serialization Paths

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/hook/test_gherkin_reporter_context_lifecycle.py \
  tests/feature/test_report_context_hierarchy.py \
  tests/feature/test_report.py -q
```

Expected:
- Reporters read only from stash-backed `Run` / `ScenarioRun`.
- Scenario serialization derives feature metadata and step lookup data through run-owned bindings instead of a `Feature` adapter.
- Missing context still produces deterministic diagnostics without mutation.

## 4. Validate Adapter and Governance Paths

```bash
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 \
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/messages/test_execution_message_adapter.py \
  tests/messages/test_execution_message_adapter_roundtrip.py \
  tests/messages/test_message_validation.py \
  tests/messages/test_governance.py \
  tests/messages_coverage/test_full_capability_governance.py \
  tests/messages_coverage/test_run_governance_regression.py -q
```

Expected:
- The execution/message adapter remains the single conversion path.
- Validation and governance rely on canonical envelopes plus run-owned registries.
- Uncovered capabilities still require valid `Partly-Applicable` or `Non-Implementable` evidence.

## 5. Full Strict Regression Suite

```bash
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 \
conda run -n pytest-bdd-ng-py314 python -m pytest -q --tb=no
```

Expected:
- Full suite remains green under strict audit mode.
- No hook, fixture, collector, or reporter path depends on `Feature`.
