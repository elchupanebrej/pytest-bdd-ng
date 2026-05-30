---
phase: 04
slug: plugin-refactoring
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-13
---

# Phase 04 - Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pyproject.toml` |
| Quick run command | `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract tests/messages/test_message_validation.py -q` |
| Full suite command | `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/ -q` |
| Estimated runtime | Unknown; full suite previously reached 430 passed in 5 minutes before environmental failure |

## Sampling Rate

- After every task commit: run the task's focused command.
- After every plan wave: run the relevant contract and focused regression set.
- Before `$gsd-verify-work`: full suite, xdist smoke, formatter parity, and pre-commit must be green.
- Max feedback latency: focused checks should stay under 120 seconds where practical.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | REF-02/REF-03 | T-04-01 | Full-suite gate not bypassed | env regression | `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/ -q` | yes | pending |
| 04-02-01 | 02 | 2 | REF-02/REF-03 | T-04-02 | Contract tests fail before migration and pass after | contract | `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract -q` | yes | pending |
| 04-03-01 | 03 | 3 | REF-02 | T-04-03 | Codegen behavior unchanged | focused | `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/generation tests/feature -q` | yes | pending |
| 04-04-01 | 04 | 3 | REF-02/REF-03 | T-04-04 | Plugin boundary enforced | contract | `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract -q` | yes | pending |
| 04-05-01 | 05 | 4 | REF-03 | T-04-05 | Formatter output unchanged | golden | `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/compatibility/test_render_cucumber_formatters.py tests/e2e/test_cucumber_formatters.py -q` | yes | pending |
| 04-06-01 | 06 | 5 | REF-03 | T-04-06 | Validation behavior unchanged | focused/full | `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/messages/test_message_validation.py tests/messages -q` | yes | pending |

## Wave 0 Requirements

Existing infrastructure covers this phase. Plan 02 adds missing source contract and formatter golden tests before large moves.

## Manual-Only Verifications

None. All Phase 4 success criteria need automated evidence.

## Validation Sign-Off

- [x] All tasks have automated verify commands or explicit investigation commands.
- [x] Sampling continuity has no three-task gap without automation.
- [x] Wave 0 uses existing pytest infrastructure.
- [x] No watch-mode flags.
- [x] `nyquist_compliant: true` set in frontmatter.

Approval: pending execution
