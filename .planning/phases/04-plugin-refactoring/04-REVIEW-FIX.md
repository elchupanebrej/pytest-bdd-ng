---
phase: 04-plugin-refactoring
fixed_at: 2026-05-19T18:42:18Z
review_path: .planning/phases/04-plugin-refactoring/04-REVIEW.md
iteration: 1
scope: critical_warning
status: all_fixed
fixed_findings:
  - CR-01
  - CR-02
  - WR-01
tests_run:
  - "uv run python -m py_compile src/pytest_bdd/script/message_capability_governance/schema.py src/pytest_bdd/plugin/code_generator/rendering.py src/pytest_bdd/plugin/code_generator/collection.py tests/cases/contract/messages/test_governance_cli_contract.py tests/cases/integration/generation/test_generate_missing.py"
  - "PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run python -m pytest -c /dev/null tests/cases/contract/messages/test_governance_cli_contract.py::test_governance_repo_root_walks_to_project_root tests/cases/contract/messages/test_governance_cli_contract.py::test_discover_governance_schema_path_prefers_canonical_repo_contract tests/cases/integration/generation/test_generate_missing.py::test_generated_python_literals_preserve_valid_gherkin_text tests/cases/integration/generation/test_generate_missing.py::test_process_single_item_tears_down_after_fixture_error -q"
  - "uv run ruff format --check src/pytest_bdd/script/message_capability_governance/schema.py src/pytest_bdd/plugin/code_generator/rendering.py src/pytest_bdd/plugin/code_generator/collection.py tests/cases/contract/messages/test_governance_cli_contract.py tests/cases/integration/generation/test_generate_missing.py"
  - "uv run ruff check src/pytest_bdd/script/message_capability_governance/schema.py src/pytest_bdd/plugin/code_generator/rendering.py src/pytest_bdd/plugin/code_generator/collection.py tests/cases/contract/messages/test_governance_cli_contract.py tests/cases/integration/generation/test_generate_missing.py"
---

# Phase 04: Code Review Fix Report

**Fixed at:** 2026-05-19T18:42:18Z
**Source review:** `.planning/phases/04-plugin-refactoring/04-REVIEW.md`
**Iteration:** 1

## Summary

- Findings in scope: 3
- Fixed: 3
- Skipped: 0
- Committed: no, per user request

## Fixed Issues

### CR-01: Governance schema lookup now points at `src`, not repo root

**Files modified:** `src/pytest_bdd/script/message_capability_governance/schema.py`, `tests/cases/contract/messages/test_governance_cli_contract.py`
**Applied fix:** `_repo_root()` now walks upward for repo markers `pyproject.toml` and `specs/`, with fallback depth retained. Added cwd-independent regression.

### CR-02: Generated Python literals break on valid step text with backslashes/newlines

**Files modified:** `src/pytest_bdd/plugin/code_generator/rendering.py`, `tests/cases/integration/generation/test_generate_missing.py`
**Applied fix:** code generation now uses `repr()` for Python literals and docstring statement literals, preserving backslashes, newlines, quotes, and triple quotes without appending punctuation.

### WR-01: Code-generation collection can leak pytest setup state on unexpected errors

**Files modified:** `src/pytest_bdd/plugin/code_generator/collection.py`, `tests/cases/integration/generation/test_generate_missing.py`
**Applied fix:** `process_single_item()` now tears down setup state in `finally` after setup succeeds. Added fixture-error regression.

## Tests

- PASS: `uv run python -m py_compile ...`
- PASS: focused pytest, `7 passed, 3 warnings in 6.94s`
- PASS: `uv run ruff format --check ...`
- PASS: `uv run ruff check ...`
- NOTE: normal pytest config failed before execution because local env rejected `--order-scope=session`; retry used `-c /dev/null` and disabled plugin autoload for focused unit coverage.

---

_Fixed: 2026-05-19T18:42:18Z_
_Fixer: Codex_
_Iteration: 1_
