---
quick_id: 260705-wpf
status: planned
created: 2026-07-05
---

# Quick Task 260705-wpf Plan

Refactor underscore-prefixed source packages so project code no longer uses private package names.

## Task 1: Rename Packages With Rope

Files:
- `src/pytest_bdd/_gherkin_go/`
- `src/pytest_bdd_toolchain/_pylint/`
- Python imports and string references under `src/`
- Project configuration in `pyproject.toml`

Action:
- Use a transient `rope` install to rename package resources:
  - `pytest_bdd._gherkin_go` -> `pytest_bdd.gherkin_go`
  - `pytest_bdd_toolchain._pylint` -> `pytest_bdd_toolchain.pylint_plugin`
- Apply rope-generated import/reference changes, then clean remaining non-Python configuration and docstring references.

Verify:
- Search for source references to `_gherkin_go`, `_pylint`, `pytest_bdd._`, and `pytest_bdd_toolchain._`.
- Confirm no source package directory under `src/` starts with `_`.

Done:
- Source package directories and imports use non-private package names.

## Task 2: Validate Focused Behavior

Files:
- `src/pytest_bdd/gherkin_go/`
- `src/pytest_bdd_toolchain/pylint_plugin/`
- `src/pytest_bdd_toolchain/case/unit/test_gherkin_go_*.py`
- `src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py`

Action:
- Run focused unit tests for the renamed Go parser bridge and Pylint plugin.
- Run import checks for the renamed packages.

Verify:
- `uv run pytest src/pytest_bdd_toolchain/case/unit/test_gherkin_go_parse.py src/pytest_bdd_toolchain/case/unit/test_gherkin_go_fallback.py src/pytest_bdd_toolchain/case/unit/test_gherkin_go_bridge.py src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py`
- `uv run python -c "import pytest_bdd.gherkin_go; import pytest_bdd_toolchain.pylint_plugin"`

Done:
- Focused tests and import smoke checks pass, or any environmental blockers are recorded in the summary.
