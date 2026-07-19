---
created: "2026-06-09T17:19:30.112Z"
title: "Move tests to separate package under ./src (NOT nested in pytest_bdd)"
area: testing
status: REOPENED — 20-23 placed tests under src/pytest_bdd/testing/ (wrong location)
files:
  - tests/ (old — needs removal after migration)
  - src/pytest_bdd/testing/ (wrong location — needs UNDO/revert)
  - pyproject.toml
  - Makefile
---

## Problem

**FORENSICS FINDING (2026-06-09):** Plan 20-23 nested tests inside `src/pytest_bdd/testing/` as a subpackage. This is wrong because:

1. Tests must be a **separate package** at `./src` level (e.g., `src/pytest_bdd_toolchain/`), NOT nested under `pytest_bdd`
2. The old `tests/` directory was retained (not removed) — still has 843 files including `__init__.py`, assets, Docker compose files
3. Docker compose and other assets in old `tests/` need rework for new layout
4. "Documented as deferred" ≠ solved — actual cleanup required

## Solution

1. **UNDO** 20-23 migration — move tests OUT of `src/pytest_bdd/testing/` back to a separate package:
   - Target: `src/pytest_bdd_toolchain/` (or similar) — a completely separate package, NOT a subpackage of `pytest_bdd`
   - This package lives at `./src` level, parallel to `pytest_bdd`, not inside it

2. **Remove** old `tests/` directory entirely:
   - Clean up `__init__.py` files in old test directories
   - Rework Docker compose files to use new paths
   - Migrate any remaining assets/scripts

3. Update `pyproject.toml`:
   - Register `pytest_bdd_toolchain` as a separate package (own `[project]` or `[tool.setuptools.packages.find]` entry if needed)
   - **CRITICAL:** The `[project.optional-dependencies]` `testing` extra MUST list the new package as its dependency:
     ```toml
     [project.optional-dependencies]
     testing = ["pytest_bdd_toolchain"]
     ```
     This is not empty — the extra pulls in the test package. `pip install pytest-bdd[testing]` installs both `pytest-bdd` and `pytest-bdd-testing`.
   - Update testpaths, test_group_paths to point to new package location

4. Update Makefile targets.

## Dependencies

- Must be done BEFORE `__init__.py` elimination
- Docker compose paths must be verified after migration
