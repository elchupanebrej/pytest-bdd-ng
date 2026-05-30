<!-- markdownlint-disable MD013 -->

# Quickstart: Validate Non-empty BDD Heading Enforcement

## 1. Prepare environment

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pip install -e '.[test,testtypes]'
uv sync --extra test --extra testtypes
```

Expected:
- Local editable install is ready for parser/validation test execution.

## 2. Validate parser-level empty heading rejection (US1)

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/feature/test_empty_bdd_headings_validation.py \
#   tests/hook/test_heading_validation_diagnostics.py
uv run python -m pytest -q \
  tests/feature/test_empty_bdd_headings_validation.py \
  tests/hook/test_heading_validation_diagnostics.py
```

Expected:
- Empty `Feature`, `Scenario`, and `Scenario Outline` titles are detected.
- Diagnostics include file path, line number, heading type, and stable error code.

## 3. Validate repository baseline compliance (US2)

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/contract/test_empty_heading_validation_contract.py \
#   tests/doc/test_features_repository_heading_baseline.py
uv run python -m pytest -q \
  tests/contract/test_empty_heading_validation_contract.py \
  tests/doc/test_features_repository_heading_baseline.py
```

Expected:
- Baseline scan over `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/` reports zero violations.
- Contract-level payload fields remain deterministic.

## 4. Validate false-positive boundaries for snippet content (US3)

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/feature/test_heading_validation_snippet_boundaries.py
uv run python -m pytest -q \
  tests/feature/test_heading_validation_snippet_boundaries.py
```

Expected:
- Non-parsed literal/code snippets containing keyword-like text are ignored.
- Only parser-recognized headings are enforced.

## 5. Run contributor workflow gates

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
bash .codex/skills/precommit-runner/scripts/run_precommit.sh --all-files
```

Expected:
- Pre-commit hooks pass with no unresolved violations.
- Empty-heading regressions are blocked before commit.

## 6. Optional matrix check

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest
uvx --with tox-uv tox -e py314-pytestlatest
```

Expected:
- Target matrix slice passes with heading validation behavior consistent on supported Python/pytest combination.

## Execution Evidence (2026-02-25)

### T043: Targeted heading-validation pytest suites

Command:

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/feature/test_empty_bdd_headings_validation.py \
#   tests/hook/test_heading_validation_diagnostics.py \
#   tests/contract/test_empty_heading_validation_contract.py \
#   tests/doc/test_features_repository_heading_baseline.py \
#   tests/feature/test_heading_validation_snippet_boundaries.py
uv run python -m pytest -q \
  tests/feature/test_empty_bdd_headings_validation.py \
  tests/hook/test_heading_validation_diagnostics.py \
  tests/contract/test_empty_heading_validation_contract.py \
  tests/doc/test_features_repository_heading_baseline.py \
  tests/feature/test_heading_validation_snippet_boundaries.py
```

Result:
- `14 passed in 0.32s`

### T044: Pre-commit validation

Command:

```bash
bash .codex/skills/precommit-runner/scripts/run_precommit.sh --all-files
```

Result:
- All hooks passed, including `generate-feature-doc` and `validate-feature-headings`.

### T045: Optional tox matrix slice

Command:

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest
uvx --with tox-uv tox -e py314-pytestlatest
```

Result:
- `389 passed, 5 skipped`
- Tox environment status: `py314-pytestlatest: OK`
