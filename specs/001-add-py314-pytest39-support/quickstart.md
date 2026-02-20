# Quickstart: Validate Python/Pytest Compatibility Coverage

## 1. Create Python 3.14 environment from conda-forge

```bash
conda create -n pytest-bdd-py314 -c conda-forge python=3.14 -y
conda activate pytest-bdd-py314
python -m pip install -U pip
python -m pip install -e .[test,testenv,testtypes]
```

## 2. Confirm matrix environments exist

```bash
tox -l
```

Expected: entries for Python 3.14 and pytest 9.0 combinations (for example `py314-pytest90-*`).

## 3. Run full matrix

```bash
tox
```

Expected: every configured compatible pair reports a result (pass or fail), not missing/undefined.

## 4. Run targeted pair checks

```bash
python -m pytest_bdd.script.compatibility_matrix --python 314 --pytest 90
python -m pytest_bdd.script.compatibility_matrix --python 314 --pytest 83
tox -e py314-pytest90-coverage-lin -- -q
```

Expected:
- `314/90` returns compatible.
- `314/83` returns incompatible with explicit reason code.
- tox pair command executes or fails with actionable interpreter availability guidance.

## 5. Run pre-commit and fix issues before committing

```bash
pre-commit run --all-files
```

Expected: all hooks pass; any reported issue must be fixed before commit.

## 6. Verify feature scope includes all uncommitted files

```bash
git status --short
```

Expected: all listed modified/added/deleted paths are included in this feature's planned implementation and commits.
