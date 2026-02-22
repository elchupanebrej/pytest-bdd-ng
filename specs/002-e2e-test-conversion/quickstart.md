# Quickstart: Validate E2E Conversion Workstream

## 1) Validate marker registration and classification tests

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility/test_e2e_classification.py
```

## 2) Run E2E conversion harness

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/e2e
```

## 3) Validate conversion inventory quality checks

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility/test_e2e_inventory.py tests/compatibility/test_e2e_migration_threshold.py
```

## 4) Validate parity and duplicate-removal guardrails

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility/test_e2e_no_duplicates.py
```

## 5) Run pre-commit checks before commits

```bash
conda run -n pytest-bdd-ng-py314 pre-commit run --all-files
```

## 6) Run CI-aligned static checks and matrix listing

```bash
conda run -n pytest-bdd-ng-py314 tox -l
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility tests/e2e
```

## 7) Non-native platform execution rule

- For non-native platform test environments, execute via Docker skill.
- Windows targets are exempt and may use non-Docker execution.
