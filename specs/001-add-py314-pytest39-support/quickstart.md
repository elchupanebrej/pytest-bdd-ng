# Quickstart: Python/Pytest Compatibility Validation (3.10-3.14, pytest>=6.2.5)

## 1. Create Python 3.14 environment from conda-forge

```bash
conda create -n pytest-bdd-ng-py314 -c conda-forge python=3.14 -y
conda run -n pytest-bdd-ng-py314 python -m pip install -U pip
conda run -n pytest-bdd-ng-py314 python -m pip install -e '.[test,testenv,testtypes]'
```

## 2. Validate supported and unsupported pairs via matrix CLI

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.compatibility_matrix --python 314 --pytest 625
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.compatibility_matrix --python 39 --pytest 625
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.compatibility_matrix --python 310 --pytest 620
```

Expected:
- Supported pair (`314` + `625`) returns compatible/supported result.
- EOL Python pair (`39` + `625`) fails fast with explicit EOL reason.
- EOL pytest pair (`310` + `620`) fails fast with explicit EOL reason.

## 3. Validate supported tox matrix environments

```bash
conda run -n pytest-bdd-ng-py314 tox -l
conda run -n pytest-bdd-ng-py314 tox -e py310-pytest625-coverage-lin -- -q
conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-coverage-lin -- -q
```

Expected:
- Listed tox envs include supported combinations only.
- Selected supported envs execute and report deterministic pass/fail results.

## 4. Run compatibility and contract checks

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility tests/contract
```

Expected:
- Compatibility and contract suites pass.
- Negative checks for unsupported EOL pairs are present and passing.

## 5. Run pre-commit before commit

```bash
conda run -n pytest-bdd-ng-py314 pre-commit run --all-files
```

Expected: all hooks pass and all reported issues are fixed before commit.
