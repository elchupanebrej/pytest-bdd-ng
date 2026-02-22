# Quickstart: Validate E2E Conversion Workstream

## 1) Validate marker registration and classification tests (expected: pass)

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility/test_e2e_classification.py
```

## 2) Run parity and inventory guardrails (expected: all pass)

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/compatibility/test_e2e_inventory.py \
  tests/compatibility/test_e2e_migration_threshold.py \
  tests/compatibility/test_e2e_no_duplicates.py
```

## 3) Run E2E conversion harness (expected: all pass)

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/e2e
```

## 4) Run CI-aligned validation slice used in this spec (expected: all pass)

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility tests/e2e
```

## 5) Run pre-commit checks before commits (expected: all hooks pass)

```bash
conda run -n pytest-bdd-ng-py314 pre-commit run --all-files
```

## 6) List tox environments used by CI

```bash
conda run -n pytest-bdd-ng-py314 tox -l
```

## 7) Non-native platform execution rule

- For non-native platform test environments, execute via Docker skill.
- Windows targets are exempt and may use non-Docker execution.
