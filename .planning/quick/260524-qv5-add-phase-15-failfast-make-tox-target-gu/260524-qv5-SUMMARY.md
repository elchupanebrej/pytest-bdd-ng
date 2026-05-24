---
quick_id: 260524-qv5
status: complete
completed: 2026-05-24
commits:
  - 64f85dfc
  - 5a76c53f
---

# Quick Task 260524-qv5 Summary

## Goal

Add a Phase 15 guide for running any specific Make/tox target in fail-fast mode, then dispatch one worker per environment to run a single target and fix failures one by one.

## Completed

- Added `.planning/phases/15-cross-platform-test-suite-entrypoint-makefile-mingw-sh/15-TARGET-FAILFAST-GUIDE.md`.
- Spawned Linux, Windows, and macOS workers with the guide and one target each.
- Linux worker blocked because this host cannot run Linux tox directly and PowerShell is not Git Bash.
- macOS worker blocked because this host cannot run macOS tox directly and PowerShell is not Git Bash.
- Windows worker found real target failures; integrated and completed fixes locally.

## Fixes

- Added `vulture` to the test optional dependency group so Windows tox has the dead-code checker.
- Removed stale Windows vulture false-positive allowlist entry.
- Moved fake node/npm runtime templates into `pytest_bdd.testing` package resources and declared package data.
- Added package-data contract coverage for those test-support templates.
- Guarded gherkin message reporter lifecycle against pytest `NotSet` runtime pickle/document state for non-BDD tests under message reporting.

## Verification

- `rtk uv run python -m pytest tests/cases/contract/generation/test_template_packaging.py tests/cases/compat/compatibility/test_render_cucumber_formatters.py -q` -> 16 passed
- `rtk uv run python -m pytest tests/cases/e2e/e2e/test_cucumber_formatters_feature.py::test_e2e_formatter_support_module_is_only_a_thin_reexport -q --messages-ndjson .tmp/node.ndjson` -> 1 passed
- `rtk uv run pre-commit run --files pyproject.toml src/pytest_bdd/testing/cucumber_formatters.py src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py tests/cases/contract/generation/test_template_packaging.py src/pytest_bdd/testing/resources/templates/cucumber_formatters/fake_node_runtime.py.j2 src/pytest_bdd/testing/resources/templates/cucumber_formatters/fake_npm_runtime.py.j2` -> passed
- `rtk uvx --with tox-uv tox run -e py314-pytestlatest-coverage-win -- -x --maxfail=1 -q` -> 1686 passed, 22 skipped, 9 deselected

## Worker Results

```text
ENV: linux
TARGET: test-platform-linux
RESULT: blocked
BLOCKERS:
- Make requires Git Bash on Windows.
- Direct Linux tox env skipped: platform win32 does not match linux.

ENV: macos
TARGET: test-platform-macos
RESULT: blocked
BLOCKERS:
- Make requires Git Bash on Windows.
- Direct macOS tox env skipped: platform win32 does not match darwin.

ENV: windows
TARGET: test-platform-windows
RESULT: fixed
FIXES:
- pyproject.toml: added vulture test dependency.
- tests/cases/unit/unit/test_dead_code.py: removed stale Windows vulture false-positive entry.
- src/pytest_bdd/testing/cucumber_formatters.py and package data: fixed installed Windows env template loading.
- src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py: fixed NotSet runtime state handling.
```
