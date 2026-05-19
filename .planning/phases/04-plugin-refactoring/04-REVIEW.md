---
phase: 04-plugin-refactoring
reviewed: 2026-05-19T18:11:59Z
depth: standard
files_reviewed: 43
files_reviewed_list:
  - src/pytest_bdd/model/cucumber_formatter_contract.py
  - src/pytest_bdd/model/message_schema_validation.py
  - src/pytest_bdd/model/message_stream_validation.py
  - src/pytest_bdd/model/message_validation.py
  - src/pytest_bdd/model/message_validation_result.py
  - src/pytest_bdd/model/message_validation_xdist.py
  - src/pytest_bdd/model/run_access.py
  - src/pytest_bdd/model/scenario_collection.py
  - src/pytest_bdd/model/scenario_report.py
  - src/pytest_bdd/plugin/code_generator/collection.py
  - src/pytest_bdd/plugin/code_generator/entrypoint.py
  - src/pytest_bdd/plugin/code_generator/hook.py
  - src/pytest_bdd/plugin/code_generator/plugin.py
  - src/pytest_bdd/plugin/code_generator/rendering.py
  - src/pytest_bdd/plugin/code_generator/request.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_payload.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/session.py
  - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py
  - src/pytest_bdd/plugin/pickle_runner/plugin.py
  - src/pytest_bdd/plugin/scenario_reporter/plugin.py
  - src/pytest_bdd/plugin/scenario_test_collector/plugin.py
  - src/pytest_bdd/script/message_capability_governance/__init__.py
  - src/pytest_bdd/script/message_capability_governance/__main__.py
  - src/pytest_bdd/script/message_capability_governance/capabilities.py
  - src/pytest_bdd/script/message_capability_governance/cli.py
  - src/pytest_bdd/script/message_capability_governance/decisions.py
  - src/pytest_bdd/script/message_capability_governance/schema.py
  - src/pytest_bdd_worker_bootstrap/xdist_remote.py
  - tests/conftest.py
  - tests/cases/contract/contract/test_formatter_golden_parity.py
  - tests/cases/contract/contract/test_large_file_contract.py
  - tests/cases/contract/contract/test_plugin_boundary_contract.py
  - tests/cases/contract/contract/test_plugin_structure_contract.py
  - tests/cases/contract/contract/test_xdist_worker_controller_boundary_contract.py
  - tests/fixtures/cucumber_formatter_golden.json
  - tests/cases/integration/generation/test_generate_missing.py
  - tests/cases/integration/hook/test_gherkin_reporter_context_lifecycle.py
findings:
  critical: 2
  warning: 1
  info: 0
  total: 3
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-05-19T18:11:59Z
**Depth:** standard
**Files Reviewed:** 43
**Status:** issues_found

## Summary

Reviewed listed source scope at standard depth. Some configured paths were stale after moves/rename, so review followed current renamed package/test paths for `message_capability_governance` and `tests/cases/...`.

## Critical Issues

### CR-01: Governance schema lookup now points at `src`, not repo root

**File:** `src/pytest_bdd/script/message_capability_governance/schema.py:20`
**Issue:** `_repo_root()` returns `Path(__file__).resolve().parents[3]`. After refactor from single file to package, this resolves to `.../pytest-bdd/src`, not repository root. `discover_governance_schema_path()` then builds `src/specs/008-maximize-messages-coverage/...`, so `python -m pytest_bdd.script.message_capability_governance report` can fail to locate default schema when cwd is not repo or ancestor. Pre-refactor depth from `src/pytest_bdd/script/message_capability_governance.py` was correct; package nesting added one parent.
**Fix:**
```python
def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]
```
Add regression asserting `_repo_root()` equals repo root from an arbitrary cwd, or avoid parent-depth math by walking upward for `pyproject.toml`.

### CR-02: Generated Python literals break on valid step text with backslashes/newlines

**File:** `src/pytest_bdd/plugin/code_generator/rendering.py:137`
**Issue:** `make_string_literal()` only escapes single quotes. A Gherkin step/scenario containing a trailing backslash generates invalid Python like `'abc\'`; embedded newlines also produce invalid single-quoted literals. `make_python_docstring()` has same ad hoc escaping risk for backslashes and changes content by always appending `.`. Code generation can emit unusable tests for valid feature text.
**Fix:**
```python
def make_python_docstring(string: str) -> str:
    return repr(f"{string}.")

def make_string_literal(string: str) -> str:
    return repr(string)
```
If triple-quoted docstrings are required for readability, build them with a real escaping helper and cover trailing backslash, newline, quote, and triple-quote cases.

## Warnings

### WR-01: Code-generation collection can leak pytest setup state on unexpected errors

**File:** `src/pytest_bdd/plugin/code_generator/collection.py:55`
**Issue:** `process_single_item()` calls `item.session._setupstate.setup(item)` and only tears down at line 67 after all fixture and matching work succeeds. Any unexpected exception before line 67, such as fixture setup failure or hook error, skips `teardown_exact(None)` and can leave fixture/session setup state active for remaining generation processing.
**Fix:**
```python
def process_single_item(...):
    item.session._setupstate.setup(item)
    try:
        item_request = item._request
        pickle = item_request.getfixturevalue("pickle")
        gherkin_document = item_request.getfixturevalue("gherkin_document")
        feature_source = item_request.getfixturevalue("feature_source")
        ...
        process_pickle_steps(...)
    finally:
        item.session._setupstate.teardown_exact(None)
```

---

_Reviewed: 2026-05-19T18:11:59Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
