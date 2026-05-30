<!-- markdownlint-disable MD013 -->

# Quickstart: Session Fixture + Stash Context Hierarchy Validation

## 1. Prepare local environment

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pip install -e '.[test,testenv,testtypes]'
uv sync --extra test --extra testenv --extra testtypes
```

Expected:
- Local package and all validation dependencies are installed.

## 2. Validate session-root fixture and stash initialization

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/hook/test_execution_context_model.py \
#   tests/hook/test_execution_context_transitions.py \
#   tests/hook/test_execution_context_fixture_stash.py
uv run python -m pytest -q \
  tests/hook/test_execution_context_model.py \
  tests/hook/test_execution_context_transitions.py \
  tests/hook/test_execution_context_fixture_stash.py
```

Expected:
- `SessionExecutionContext` is created at `pytest_sessionstart`.
- Session fixture resolves successfully at early runtime stages.
- Fixture and `pytest.config.stash` references are identity-equal for one session.

## 3. Validate hook parameter model integration and lifecycle isolation

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/feature/test_execution_context_hooks.py \
#   tests/feature/test_execution_context_lifecycle.py \
#   tests/hook/test_hook_execution_context_regression.py
uv run python -m pytest -q \
  tests/feature/test_execution_context_hooks.py \
  tests/feature/test_execution_context_lifecycle.py \
  tests/hook/test_hook_execution_context_regression.py
```

Expected:
- Hook parameter models expose `execution_context` as embedded field/reference.
- Context transitions remain deterministic with no cross-scenario leakage.

## 4. Validate reporting hierarchy consumption

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/feature/test_report_context_hierarchy.py \
#   tests/struct_bdd/test_execution_context_diagnostics.py
uv run python -m pytest -q \
  tests/feature/test_report_context_hierarchy.py \
  tests/struct_bdd/test_execution_context_diagnostics.py
```

Expected:
- Reporting reads from hierarchy when scoped nodes are active.
- Reporting degrades gracefully to session-level context with structured fallback metadata when node scope is inactive.

## 5. Validate contracts and compatibility guardrails

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest -q \
#   tests/contract/test_execution_context_contract.py \
#   tests/compatibility/test_hook_execution_context_api_surface.py
uv run python -m pytest -q \
  tests/contract/test_execution_context_contract.py \
  tests/compatibility/test_hook_execution_context_api_surface.py
```

Expected:
- Contract paths for session fixture, stash binding, hierarchy transitions, and reporting snapshots are covered.
- Additive-only API guarantee remains enforced (`removed_symbols=0`, `renamed_symbols=0`).

## 6. Validate full integration and lint gates

```bash
# Legacy workflow:
# cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
# conda run -n pytest-bdd-ng-py314 python -m pytest tests/e2e -q
uv run python -m pytest tests/e2e -q
bash .codex/skills/precommit-runner/scripts/run_precommit.sh --all-files
# conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-coverage-mac
uvx --with tox-uv tox -e py314-pytestlatest-coverage-mac
```

Expected:
- E2E behavior remains stable.
- Pre-commit hooks pass with no unresolved findings.
- Coverage/matrix validation remains green on supported macOS environment.
