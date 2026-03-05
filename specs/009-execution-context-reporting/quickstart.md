# Quickstart: Execution Context + Message Adapter Refactor

## Preconditions

- Repo root: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng`
- Branch: `009-execution-context-reporting`
- Environment: `conda` env `pytest-bdd-ng-py314`

## Scenario 1: Reporter Uses Read-Only Context Access (US1)

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/hook/test_gherkin_reporter_context_lifecycle.py \
  tests/messages/test_message_emission_points.py -q
```

Expected:
- Reporter does not bootstrap/mutate context.
- Lifecycle IDs are context-derived.

## Scenario 2: Registry Ownership Stays in Execution Context (US2)

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/model/gherkin_document/test_feature_context_lookup.py \
  tests/hook/test_scenario_reference_resolution.py -q
```

Expected:
- `Feature` model has no registry ownership.
- Lookups resolve through execution context / stash-backed context path.

## Scenario 3: Adapter Round-Trip Integrity (US3)

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/messages/test_execution_message_adapter.py \
  tests/messages/test_execution_message_adapter_roundtrip.py -q
```

Expected:
- `execution -> message -> execution` preserves deterministic IDs and links.
- Missing links generate deterministic diagnostics (no synthetic fabrication).

## Scenario 4: Strict Governance Gate

```bash
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 \
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/messages/test_governance.py \
  tests/messages_coverage/test_execution_context_governance_regression.py \
  tests/messages_coverage/test_full_capability_governance.py -q
```

Expected:
- Runtime-required fields are enforced by runtime evidence.
- Remaining fields are covered or explicitly classified with valid evidence.

## Scenario 5: E2E NDJSON + HTML Report

```bash
mkdir -p /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/artifacts
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 \
conda run -n pytest-bdd-ng-py314 python -m pytest tests/messages_coverage -q \
  -p no:pytest-bdd-gherkin-message-reporter \
  -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
  --messages-ndjson /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/artifacts/messages-coverage-e2e.ndjson \
  --cucumber-html /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/artifacts/messages-coverage-e2e.html
```

Expected artifacts:
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/artifacts/messages-coverage-e2e.ndjson`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/artifacts/messages-coverage-e2e.html`
