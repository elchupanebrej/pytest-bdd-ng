<!-- markdownlint-disable MD013 -->

# Quickstart: Strict Non-Null Lifecycle Validation

## 1. Prepare the local environment

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pip install -e '.[test,testenv,testtypes]'
```

Expected:

- Local package and validation dependencies are available in the `pytest-bdd-ng-py314` environment.

## 2. Validate stash identity and root lifecycle guard behavior

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/hook/test_run_fixture_stash.py \
  tests/hook/test_scenario_run_model.py \
  tests/hook/test_run_scenario_runtime_unit.py
```

Expected:

- The canonical `Run` object is created in stash and shared through fixture and hook access.
- Root lifecycle access uses explicit empty-state or deterministic failure behavior instead of returning `None`.

## 3. Validate lifecycle transitions and hook-visible non-null guarantees

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/hook/test_run_transitions.py \
  tests/feature/test_run_hooks.py \
  tests/feature/test_run_lifecycle.py \
  tests/feature/test_report_context_hierarchy.py
```

Expected:

- Hook phases preserve deterministic lifecycle transitions.
- Required runtime objects are present in active hook phases or fail fast through centralized lifecycle guards.
- Covered inactive-by-design phases expose dedicated Empty-State Objects rather than missing values.

## 4. Validate reporting, enrichment, and parse-error boundaries

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/hook/test_reporting_context_snapshot_unit.py \
  tests/hook/test_scenario_reference_resolution.py \
  tests/hook/test_parse_error_sink.py \
  tests/hook/test_run_diagnostics.py
```

Expected:

- Reporting snapshots remain deterministic for active, idle, and teardown stages.
- Missing enrichment and parse-error emission remain contract-compatible without caller-side `None` checks.
- Reporter and parser consumers rely on centralized boundary behavior rather than ad-hoc inline absence checks.

## 5. Validate public contracts and lifecycle compatibility surfaces

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/contract/test_hook_lifecycle_non_null_contract.py \
  tests/contract/test_run_contract.py \
  tests/contract/test_event_message_reporting_contract.py \
  tests/contract/test_xdist_consolidated_stream_contract.py \
  tests/contract/test_cucumber_formatter_cli_contract.py
```

Expected:

- Lifecycle and reporting contracts reflect dedicated Empty-State Objects and centralized lifecycle guards.
- Public hook/plugin integration points stay deterministic and compatibility-safe.

## 6. Validate repository-wide compatibility and quality gates

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest tests/compatibility -q
conda run -n pytest-bdd-ng-py314 pre-commit run --all-files
```

Expected:

- Compatibility behavior remains aligned with supported pytest/Python expectations.
- Pre-commit hooks pass with no unresolved findings.

## 7. Optional matrix discovery before broader implementation rollout

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 tox -l
```

Expected:

- Available tox environments are listed for selecting a broader validation slice after the targeted lifecycle refactor lands.
