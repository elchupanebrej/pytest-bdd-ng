---
phase: 04-plugin-refactoring
plan: "01"
subsystem: verification
tags: [pytester, xdist, pre-commit, environment]
requires:
  - phase: 03-core-runtime-refactor
    provides: runtime split blocker evidence
provides:
  - Phase 4 environment blocker reproduction evidence
affects: [phase-04, verification, plugin-refactoring]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/04-plugin-refactoring/04-01-SUMMARY.md
  modified: []
key-decisions: []
patterns-established: []
requirements-completed: [REF-02, REF-03]
duration: pending
completed: pending
---

# Phase 04 Plan 01: Environment Unblocker Summary

Phase 3 verification blockers reproduced as concrete pytester, xdist, and hook environment failures before source fixes.

## Task 1 Reproduction Evidence

### Focused pytester feature set

Command:

```bash
UV_PROJECT_ENVIRONMENT=.venv-linux timeout 300s uv run --extra test python -m pytest -s -o addopts='' tests/hook/test_scenario_run_characterization.py tests/hook/test_run_transitions.py tests/hook/test_scenario_run_model.py tests/hook/test_run_scenario_runtime_unit.py tests/hook/test_reporting_context_snapshot_unit.py tests/hook/test_run_diagnostics.py tests/hook/test_scenario_reference_resolution.py tests/feature/test_run_lifecycle.py tests/feature/test_run_hooks.py tests/hook/test_scenario_locator_pipeline.py tests/hook/test_scenario_collection_read_hooks.py -q
```

Observed result: `53 passed, 2 failed`.

Failure category: pytester capture cleanup.

First failing stack/module: `_pytest/capture.py`, `snap()`, `self.tmpfile.truncate()`, raising `FileNotFoundError`.

Impact: nested inprocess pytester runs collected zero tests, so `tests/feature/test_run_lifecycle.py` and `tests/feature/test_run_hooks.py` asserted `passed=0` instead of expected scenario counts.

Suspected owner file: `tests/conftest.py` pytester configuration or pytester run mode/capture setup.

### Full test suite

Command:

```bash
UV_PROJECT_ENVIRONMENT=.venv-linux timeout 360s uv run --extra test python -m pytest -s -o addopts='' tests/ -q
```

Observed result: timed out with exit code `124` after repeated pytester failures.

Failure category: pytester capture cleanup.

First failing stack/module: `_pytest/capture.py`, `snap()`, `self.tmpfile.truncate()`, raising `FileNotFoundError`.

Impact: many testdir-based nested runs reported `collected 0 items` or `no tests ran`, matching Phase 3 blocker notes.

Suspected owner file: `tests/conftest.py` pytester configuration or pytester run mode/capture setup.

### xdist smoke

Command:

```bash
env UV_PROJECT_ENVIRONMENT=.venv-linux timeout 90s uv run --extra test python -m pytest -s -o addopts='' tests/ -q -n 2
```

Observed result: exit code `5`, no tests ran.

Failure category: xdist worker bootstrap.

First failing stack/module: `src/pytest_bdd_worker_bootstrap/xdist_remote.py`, `_prepare_worker_config()`, `_prepareconfig(args, None)`.

Error: `pytest.PytestAssertRewriteWarning: Module already imported so cannot be rewritten; xdist`.

Suspected owner file: `src/pytest_bdd_worker_bootstrap/xdist_remote.py`, with entrypoint behavior in `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`.

### pre-commit

Command:

```bash
uvx pre-commit run --all-files
```

Observed result: exit code `1`.

Failure category: `.venv/Scripts` hook I/O.

First failing hook/module: local hooks `generate-feature-doc` and `validate-feature-headings`.

Error: `error: failed to remove directory '/mnt/c/Users/bulky/Projects/pytest-bdd/.venv/Scripts': Input/output error (os error 5)`.

Suspected owner file: `.pre-commit-config.yaml`, local hook environment/entry command.

## Task Commits

Pending.

## Deviations from Plan

- RTK shell proxy required by AGENTS.md was not available on `PATH`; direct shell commands were used after `rtk: command not found`.

## Known Stubs

None.

## Threat Flags

None.
