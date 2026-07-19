# Phase 17: Code Review Fix Report

## Overview
All findings from `17-REVIEW.md` have been addressed and resolved. Verification tests pass successfully.

## Findings Resolved

### CR-01: GitHub Actions Windows CI Broken Due to Missing Bash Shell Default
- **Resolution**: Added `defaults: run: shell: bash` to the test job in `.github/workflows/main.yml`.
- **Status**: Fixed.

### CR-02: `FAIL_FAST=1` Logic in `validate-test-all-backends` Unconditionally Fails on All OSes
- **Resolution**: Refactored `validate-test-all-backends` to dynamically check only platform backends supported by the host. Cleaned up platform target handlers to exit gracefully with a skip message on incompatible environments.
- **Status**: Fixed.

### WR-01: Shell Command Injection Vulnerability in WSL Platform Test Command
- **Resolution**: Refactored `wsl.exe` invocation in the `Makefile` to pass variables securely through `WSLENV=TEST_ALL_ARGS/u:TEST_LINUX_ARGS/u` rather than directly expanding them in the outer shell.
- **Status**: Fixed.

### WR-02: Hardcoded Executable Paths for Git Bash and Docker on MINGW
- **Resolution**: Modified the shell and Docker path resolution to search the system `PATH` using `command -v` and `which` before falling back to default Program Files directories.
- **Status**: Fixed.

### WR-03: Deprecated `codecov` Python Package Usage in Workflow
- **Resolution**: Migrated from the deprecated `codecov` Python package to the official `codecov/codecov-action@v4` in `.github/workflows/main.yml`.
- **Status**: Fixed.

### WR-04: Naive Makefile Parser in Tests Misidentifies Assignments/Exports as Targets
- **Resolution**: Refactored `_parse_targets` parser in `tests/cases/contract/test_makefile_test_api.py` to reset target tracking on non-matching lines and ignore Makefile keywords and assignment expressions.
- **Status**: Fixed.

## Verification
- Pre-commit checks run and pass: `uvx pre-commit run --all-files` (Pass).
- Makefile API contract tests pass: `uv run pytest tests/cases/contract/test_makefile_test_api.py` (Pass).
