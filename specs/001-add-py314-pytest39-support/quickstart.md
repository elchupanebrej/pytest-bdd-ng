# Quickstart: Python/Pytest Compatibility Validation

## 1. Create Python 3.14 environment from conda-forge

```bash
conda create -n pytest-bdd-ng-py314 -c conda-forge python=3.14 -y
conda activate pytest-bdd-ng-py314
python -m pip install -U pip
python -m pip install -e '.[test,testenv,testtypes]'
```

## 2. Validate compatibility matrix behavior

```bash
python -m pytest_bdd.script.compatibility_matrix --python 314 --pytest 90
python -m pytest_bdd.script.compatibility_matrix --python 314 --pytest 83
```

Expected:
- Compatible pair returns success with explicit compatibility reason.
- Incompatible pair returns non-zero with explicit reason code.

## 3. Validate representative matrix execution

```bash
tox -e py314-pytest90-coverage-mac -- -q
```

Expected: selected environment executes and reports deterministic pass/fail result.

## 4. Validate full compatibility/contract suites

```bash
python -m pytest -q tests/compatibility tests/contract
```

Expected:
- Compatibility and contract suites pass.
- Existing supported combinations are not regressed by the update.

## 5. Run pre-commit before commit

```bash
pre-commit run --all-files
```

Expected: all hooks pass and any reported issue is fixed before commit.
