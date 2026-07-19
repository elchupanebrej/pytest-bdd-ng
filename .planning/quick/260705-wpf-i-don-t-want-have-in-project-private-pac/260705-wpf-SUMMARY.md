---
status: complete
quick_id: 260705-wpf
date: 2026-07-05
commit: fe96b9c4
---

# Quick Task 260705-wpf Summary

Refactored source packages that used private underscore-prefixed names.

## Completed

- Renamed `pytest_bdd._gherkin_go` to `pytest_bdd.gherkin_go` using `rope.refactor.rename.Rename`.
- Renamed `pytest_bdd_toolchain._pylint` to `pytest_bdd_toolchain.pylint_plugin` using `rope.refactor.rename.Rename`.
- Updated imports, tests, Pylint plugin loading, setuptools build command paths, package data config, and lint overrides.
- Confirmed no underscore-prefixed package directories remain under `src/` except `__pycache__`.

## Verification

- `uv run python -c "import pytest_bdd.gherkin_go; import pytest_bdd_toolchain.pylint_plugin"` passed.
- `uv run ruff check pyproject.toml src/pytest_bdd/collector_batch.py src/pytest_bdd/parser.py src/pytest_bdd/gherkin_go src/pytest_bdd_toolchain/pylint_plugin src/pytest_bdd_toolchain/case/unit/test_gherkin_go_parse.py src/pytest_bdd_toolchain/case/unit/test_gherkin_go_fallback.py src/pytest_bdd_toolchain/case/unit/test_gherkin_go_bridge.py src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py src/pytest_bdd_toolchain/case/unit/test_phase14_import_coverage.py src/pytest_bdd_toolchain/step/go_parser.py` passed.
- `uv run pytest --basetemp=tmp-quick-260705-wpf src/pytest_bdd_toolchain/case/unit/test_gherkin_go_parse.py src/pytest_bdd_toolchain/case/unit/test_gherkin_go_fallback.py src/pytest_bdd_toolchain/case/unit/test_gherkin_go_bridge.py src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py` passed: 81 passed.

Implementation commit: `fe96b9c4`
