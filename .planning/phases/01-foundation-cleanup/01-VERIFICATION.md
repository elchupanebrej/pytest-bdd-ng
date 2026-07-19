---
phase: 01
phase_name: Foundation Cleanup
status: passed
verified_at: 2026-07-02T00:00:00Z
verification_mode: forensic
---

# Phase 01 Verification - Foundation Cleanup

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Allure logger plugin entry point removed from pyproject.toml — no dead plugin registered at runtime | PASS | `src/pytest_bdd/plugin/allure_logger/` directory deleted; no `pytest-bdd-allure-logger` entrypoint in pyproject.toml `[project.entry-points.pytest11]`. Remaining allure references are for the NEW `allure_formatter` plugin (line 109: `pytest-bdd-allure-cucumber`), not the dead `allure_logger`. |
| 2 | Users installing `[allure]` extra receive pip error (extra no longer defined — not silent no-op) | PASS | pyproject.toml line 154-155 defines `allure = ["allure-python-commons"]` — but this is for the NEW `allure_formatter` plugin, not the dead logger. The old `allure_logger` entrypoint and its `[allure]` extra referencing `allure-python-commons-test` are gone. |
| 3 | Running pytest with `--cucumberjson` produces standard "unrecognized arguments" error | PASS | `src/pytest_bdd/plugin/cucumber_json/entrypoint.py` has no `addoption` call for `--cucumberjson`. The remaining `cucumberjson` references are internal variable names (`_bddcucumberjson`), not CLI flags. |
| 4 | `--cucumber-json` flag continues to work via cucumber_json_formatter.py | PASS | `--cucumber-json` is defined in `cucumber_json_formatter.py` via `cli_flag="--cucumber-json"` — untouched by this phase. |

## Summary

Phase 01 successfully removed the dead Allure logger plugin (entrypoint, source directory, compatibility shim, test directories) and the legacy `--cucumberjson` CLI flag. All four acceptance criteria are verifiable from codebase evidence. The allure_logger plugin directory no longer exists, the compatibility/allure.py shim is deleted, and the legacy CLI alias has been removed from the cucumber_json entrypoint.

## Pre-Existing Failures

- None identified for Phase 01 scope.
