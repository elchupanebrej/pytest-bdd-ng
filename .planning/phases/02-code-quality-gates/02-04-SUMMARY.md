---
phase: 02-code-quality-gates
plan: "04"
subsystem: quality-gates
tags: [exceptions, result, zero-match, collection, lint]
requires:
  - phase: 02-code-quality-gates
    provides: "Plan 01 quality gate checker and failure reason enums"
  - phase: 02-code-quality-gates
    provides: "Plan 02-03 return None cleanup"
provides:
  - "Full-codebase quality gate passes for BLQ901 and BLQ902"
  - "Logged broad exception handlers with Ruff-compatible noqa exemptions where intentional"
  - "Result-backed heuristic parser build attempts"
  - "Collection-time zero-match scenario error with CLI and ini escape hatches"
affects: [phase-02, parsers, collection, quality-gates]
tech-stack:
  added: []
  patterns: [Result parser build, collection-time validation, Ruff-compatible noqa]
key-files:
  created:
    - .planning/phases/02-code-quality-gates/02-04-SUMMARY.md
  modified:
    - src/pytest_bdd/_ruff/rules/quality_gates.py
    - src/pytest_bdd/parsers.py
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py
    - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py
    - src/pytest_bdd/plugin/scenario_test_collector/const.py
    - tests/feature/test_steps.py
    - pyproject.toml
key-decisions:
  - "Use `# noqa: BLE001` as the source-level exemption so Ruff and the custom gate agree."
  - "Zero-match validation checks whether a scenario has no matching steps at collection time, then raises UsageError unless escape hatches are enabled."
  - "Escape hatches skip zero-match scenario items instead of allowing a later runtime lookup failure."
patterns-established:
  - "Custom quality gate recognizes normal Ruff noqa comments rather than custom rule IDs in source."
  - "Collection validation builds a temporary step registry from loaded module and plugin registries."
requirements-completed: [STAB-02, STAB-03]
duration: 70 min
completed: 2026-05-12
---

# Phase 02 Plan 04: Exception Fixes, Parser Result, Zero-Match UX Summary

Phase 02 now has an operational full-codebase quality gate for non-hook `return None` and unlogged broad exception handlers.

## Accomplishments

- Added logging to broad exception handlers in collector, batch parser, code generator, message transport, reporter lifecycle, hook catalog, and pickle runner paths.
- Updated custom quality gate suppression to accept Ruff-compatible `# noqa: BLE001`.
- Converted the heuristic step parser construction chain to `Result[StepParser, ParserFailure]` attempts.
- Added `--allow-empty-scenarios` and `bdd_allow_empty_scenarios` to skip zero-match scenarios.
- Added collection-time `pytest.UsageError` for scenarios where no steps match any registered step definition.
- Added feature tests for zero-match error and both escape hatches.

## Verification

- `python3 src/pytest_bdd/_ruff/rules/quality_gates.py src/pytest_bdd/` — passed.
- `uvx pre-commit run ruff-check --files ...` — passed.
- `uvx pre-commit run ruff-format --files ...` — passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/feature/test_steps.py -k 'zero_match or allow_empty' -q` — 3 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/hook/test_scenario_locator_pipeline.py tests/model/test_scenario_run_returns_contract.py tests/compatibility/test_public_api_exports.py -q` — 7 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/unit -k 'parser or gherkin_go' -q` — 37 passed.

## Known Verification Limitation

- Full `tests/feature/test_steps.py` under Python 3.14 still fails in many pre-existing pytester in-process cases with `FileNotFoundError` in pytest capture teardown and zero collected inner items. The isolated new subprocess zero-match tests pass.

## Task Commit

- Pending commit: `fix(02-04): close exception and zero-match quality gates`

---
*Phase: 02-code-quality-gates*
*Completed: 2026-05-12*
