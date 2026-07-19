---
phase: 15
topic: target-failfast-guide
created: 2026-05-24
---

# Phase 15: Single-Target Fail-Fast Guide

Use this guide when fixing one test target at a time. Goal: run the narrowest
Make/tox command, stop at the first failure, fix that failure, then repeat until
the target is green or blocked by an unavailable backend.

## Rules

- Prefer `make test-platform-*` when validating platform routing.
- Prefer direct `tox run -e <env> -- <pytest-posargs>` when fixing one specific
  test file, marker, or node id.
- Always include `-x --maxfail=1` in pytest args while fixing.
- Fix one failure at a time. Re-run the exact same command after each fix.
- Commit only after the target is green or the remaining blocker is external
  infrastructure.
- Do not bypass tests by changing markers, skipping tests, or weakening asserts.

## Pick Environment

| Environment | Make target | Default tox envs |
|-------------|-------------|------------------|
| Native host | `test-platform-native` | `$(TOX_NATIVE_ENVS)` |
| Linux | `test-platform-linux` | `$(TOX_LINUX_ENVS)` |
| Windows | `test-platform-windows` | `$(TOX_WINDOWS_ENVS)` |
| macOS | `test-platform-macos` | `$(TOX_MACOS_ENVS)` |

Current Phase 15 defaults:

```text
TOX_LINUX_ENVS=py314-pytestlatest-coverage-lin,py314-pytestlatest-gherkinlatest-xdist-coverage-lin
TOX_WINDOWS_ENVS=py314-pytestlatest-coverage-win,py314-pytestlatest-gherkinlatest-xdist-coverage-win
TOX_MACOS_ENVS=py314-pytestlatest-coverage-mac,py314-pytestlatest-gherkinlatest-xdist-coverage-mac
```

## Run One Make Platform Target

Use platform args to pass pytest selectors through Make into tox:

```bash
rtk make test-platform-native FAIL_FAST=1 REPORT_MODE=skip TEST_NATIVE_ARGS="tests/cases/contract/test_makefile_test_api.py -x --maxfail=1 -q"
rtk make test-platform-linux FAIL_FAST=1 REPORT_MODE=skip TEST_LINUX_ARGS="tests/cases/contract/test_makefile_test_api.py -x --maxfail=1 -q"
rtk make test-platform-windows FAIL_FAST=1 REPORT_MODE=skip TEST_WINDOWS_ARGS="tests/cases/contract/test_makefile_test_api.py -x --maxfail=1 -q"
rtk make test-platform-macos FAIL_FAST=1 REPORT_MODE=skip TEST_MACOS_ARGS="tests/cases/contract/test_makefile_test_api.py -x --maxfail=1 -q"
```

If backend setup is missing, stop and report the exact blocker. Do not replace
platform execution with a different platform unless the task explicitly says to
perform static-only validation.

## Run One Tox Env Directly

Use this when fixing a concrete test failure inside one tox environment:

```bash
rtk uvx --with tox-uv tox run -e py314-pytestlatest-coverage-lin -- tests/cases/contract/test_makefile_test_api.py -x --maxfail=1 -q
rtk uvx --with tox-uv tox run -e py314-pytestlatest-coverage-win -- tests/cases/contract/test_makefile_test_api.py -x --maxfail=1 -q
rtk uvx --with tox-uv tox run -e py314-pytestlatest-coverage-mac -- tests/cases/contract/test_makefile_test_api.py -x --maxfail=1 -q
```

For a single test node:

```bash
rtk uvx --with tox-uv tox run -e py314-pytestlatest-coverage-lin -- tests/cases/contract/test_makefile_test_api.py::test_phase15_test_all_validates_backends_before_platform_work -x --maxfail=1 -q
```

## Fix Loop

1. Run chosen command.
2. If backend unavailable, record blocker and stop.
3. If test fails, inspect only the first failure.
4. Fix root cause without weakening coverage.
5. Re-run same command.
6. Repeat until command exits 0.
7. Run a broader nearest-neighbor command, for example the containing file or
   target without node id.
8. Commit with `test(...)` or `fix(...)` message.

## Worker Report Format

Each environment worker must return:

```text
ENV: linux|windows|macos|native
TARGET: <make target or tox env>
COMMAND: <exact command run>
RESULT: green|fixed|blocked
FIXES:
- <file>: <summary>
BLOCKERS:
- <external blocker, if any>
COMMITS:
- <hash message>
```
