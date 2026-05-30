---
phase: 12-restructure-test-suite-into-semantic-groups
plan: 06
status: complete
date: 2026-05-19
requirements_addressed: [final-validation, compatibility-sweep]
---

# 12-06 Plan Summary: Final Compatibility/Full Validation

## Objective

Run final validation proving the restructure works through new supported entrypoints and record environment-specific outcomes.

## Task 1: Guard and Semantic Slice Validation

**Wave 0 Guards** (10 passed, 0 failed):
- `test_test_suite_classification.py` — passed: semantic path mapping valid, no tests under assets
- `test_makefile_test_api.py` — passed: required Make targets present, env checks read-only
- `test_e2e_loader_shape.py` — passed: no `scenarios(".")` or broad feature-directory loaders

**Semantic Slices:**
- `test-unit`: 588 passed, 1 skipped (1 flaky xdist barrier test on Windows — PermissionError on barrier.json, unrelated to restructure)
- `test-integration`: 252 passed, 3 skipped
- `test-contract`: 217 passed, 9 skipped
- `test-e2e`: 69 passed, 62 skipped (browser tests skip without Playwright per D-10)
- `test-compat`: 39 passed
- `test-perf`: 1 passed
- `test-slow`: 11 passed, 2 skipped, 3 failed (Docker Desktop not running — environment-gated per D-10)
- `test-posix`: all deselected on Windows (expected)

## Task 2: Full Feasible Entrypoint and Tox List

- `tox -l`: exit 0, all 79 environments resolved
- `make test-all` equivalents: all feasible local targets pass; Docker/platform targets correctly gated behind env-check failures per D-08/D-09/D-10

## Task 3: Stale Path and Helper Import Audit

**Issues found and fixed during validation:**

1. **`tests/e2e/steps_batch_collection.py:2`** — stale import `from tests.e2e.conftest` → fixed to `from tests.cases.e2e.conftest`
2. **`tests/cases/e2e/e2e/test_cucumber_formatters.py:27-28`** — `parents[2]` no longer resolves to repo root after nesting; updated to `parents[4]` and corrected path from `tests/support/` to `src/pytest_bdd/testing/`
3. **`tests/cases/e2e/conftest.py:229`** — `_REMOTE_XDIST_FIXTURE_DIR` pointed to old `tests/e2e/fixtures/remote_xdist`; updated to `tests/assets/docker/remote_xdist`
4. **`tests/cases/e2e/conftest.py:359`** — `parents[2]` for PYTHONPATH resolution → fixed to `parents[4]`
5. **`tests/cases/compat/compatibility/test_render_cucumber_formatters.py:208`** — `parents[2]` → `parents[4]`
6. **`tests/assets/docker/remote_xdist/verify_report.py:13`** — stale import `from tests.messages.message_stream_assertions` → `from tests.cases.contract.messages.message_stream_assertions`

**Final audit:** no stale executable test imports remain; `pytest_bdd.testing` has no public API export addition.

## Environment-Gated Outcomes

- Docker Desktop unavailable → docker/slow tests fail with `pytest.fail("Docker Desktop did not start within timeout")` per D-10
- Browser (Playwright) unavailable → browser-dependent e2e tests skip
- Windows host → posix tests deselected

## Verification

| Command | Exit | Result |
|---------|------|--------|
| `uv run python -m pytest tests/cases/unit/test_test_suite_classification.py tests/cases/unit/test_e2e_loader_shape.py tests/cases/contract/test_makefile_test_api.py -q` | 0 | 10 passed |
| `make test-unit` | 0 | 588 passed |
| `make test-integration` | 0 | 252 passed |
| `make test-contract` | 0 | 217 passed |
| `make test-e2e` | 0 | 69 passed |
| `make test-compat` | 0 | 39 passed |
| `make test-perf` | 0 | 1 passed |
| `uvx --with tox-uv tox -l` | 0 | 79 envs resolved |
| Stale import audit | 0 | clean |
