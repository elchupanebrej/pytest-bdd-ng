---
phase: 13-unify-cucumber-json-plugins-ini-cli-options
verified: 2026-05-20T08:26:00Z
status: verified
score: 20/20 must-haves verified
overrides_applied: 0
gaps: []
---

# Phase 13: Unify cucumber-json plugins INI/CLI options Verification Report

**Phase Goal:** Add `cucumber_json_dispatcher` that enforces CLI-wins while preserving distinct legacy INI and Node CLI backends.
**Verified:** 2026-05-20T07:28:00Z
**Status:** gaps_found
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | A third entry point (`cucumber_json_dispatcher`) bridges INI and CLI cucumber-json configuration paths | VERIFIED | `pyproject.toml:103` registers `pytest-bdd-cucumber-json-dispatcher`; `entrypoint.py:15-20` reads INI + CLI and suppresses INI on CLI. |
| 2 | No duplicate registration or conflicting output between the two paths | VERIFIED | Integration tests pass. `test_dispatcher_cli_wins_over_ini` asserts no `ini_output.json` and `cli_output.json` exists when both set. |
| 3 | Backward compatible: existing INI configs and CLI invocations still work | VERIFIED | INI-only, CLI-only, e2e cucumber_json, and formatter CLI contracts pass. Existing backend entry points remain at `pyproject.toml:93` and `pyproject.toml:102`. |
| 4 | Full test suite passes with zero regressions | VERIFIED | Tests pass after removing hallucinated `ExternalAttachment` from attachment payload tests. |
| 5 | Dispatcher package has all 5 required files | VERIFIED | `__init__.py`, `const.py`, `entrypoint.py`, `hook.py`, `plugin.py` exist. |
| 6 | `const.py` has no imports from `cucumber_json` or `cucumber_json_formatter` | VERIFIED | Static scan found no banned runtime import in dispatcher package; contract test passes. |
| 7 | `pytest_configure` uses `@pytest.hookimpl(tryfirst=True)` | VERIFIED | AST check: decorators `['pytest.hookimpl(tryfirst=True)']`. |
| 8 | xdist guard is first check in `pytest_configure` before config reads | VERIFIED | AST first statement: `if hasattr(config, 'workerinput'): return`; worker fake config leaves INI cache unchanged. |
| 9 | CLI wins over INI via `_inicache["cucumber_json_path"] = ""` | VERIFIED | Direct probe prints `both:` empty, `ini-only: ini.json`, `worker: ini.json`; integration test also passes. |
| 10 | Entry point order in `pyproject.toml` is correct | VERIFIED | Dispatcher line sits after `pytest-bdd-cucumber-json` and before `pytest-bdd-gherkin-message-reporter`. |
| 11 | Integration test file exists with all 6 dispatcher tests | VERIFIED | `pytest --co -q tests/cases/integration/cucumber_json/` collected 6 named dispatcher tests. |
| 12 | Contract test file exists and checks entry point/import ban | VERIFIED | `test_cucumber_json_dispatcher_contract.py` includes entry point, constants, import ban, required file checks. |
| 13 | All 10 dispatcher tests pass | VERIFIED | `10 passed in 13.76s`. |
| 14 | Existing cucumber_json contract/e2e tests still pass | VERIFIED | Formatter/plugin contracts: `16 passed in 7.01s`; e2e cucumber_json: `2 passed, 129 deselected in 15.16s`. |
| 15 | Plugin-pattern contract passes | VERIFIED | Included in contract command: `test_plugin_patterns_contract.py` passed. |
| 16 | Package importable after editable install | VERIFIED | `uv pip install -e . --quiet` succeeded; direct import printed `entrypoint OK`. |
| 17 | Entry point visible to installed metadata / pytest collection | VERIFIED | `importlib.metadata.entry_points(group='pytest11')` shows `pytest-bdd-cucumber-json-dispatcher pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint`; pytest collection of dispatcher tests succeeds. |
| 18 | No existing test files modified by Phase 13 plan scope | VERIFIED_WITH_RISK | Phase summaries list only new dispatcher tests. Current worktree has unrelated formatting diff in `tests/cases/e2e/e2e/test_e2e.py`; not a Phase 13 key file. |
| 19 | No Phase 13 anti-pattern blocker present | VERIFIED | Ruff passes on dispatcher source/tests. No TODO/FIXME/XXX. Placeholder text is intentional canonical plugin structure from plan. |
| 20 | No requirements IDs missing | VERIFIED | Plans list `requirements: []`; `.planning/REQUIREMENTS.md` has no Phase 13 mapping. |

**Score:** 19/20 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/__init__.py` | Package docstring, no imports | VERIFIED | Describes INI legacy backend, CLI Node backend, CLI-wins suppression. |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/const.py` | Local constants, no cross-plugin imports | VERIFIED | Uses `pytest_bdd.compatibility.enum.StrEnum`; constants match expected values. |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/hook.py` | Canonical hook placeholder | VERIFIED | Docstring-only hook surface. |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/plugin.py` | attrs placeholder class | VERIFIED | `@attr.s(auto_attribs=True)` class, no dataclass. |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/entrypoint.py` | Hook implementation | VERIFIED | `tryfirst`, xdist guard first, safe CLI attr read, `_inicache` suppression. |
| `pyproject.toml` | pytest11 dispatcher entry point | VERIFIED | Entry point at line 103, old backend entries preserved. |
| `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py` | 6 integration tests | VERIFIED | Collected 6 tests; all passed in focused suite. |
| `tests/cases/contract/contract/test_cucumber_json_dispatcher_contract.py` | 4 contract tests | VERIFIED | Entry point, constants, import ban, required files. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `pyproject.toml` | `pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint` | pytest11 entry point | VERIFIED | Installed metadata exposes dispatcher entry point. |
| `entrypoint.py` | INI backend | `_inicache["cucumber_json_path"] = ""` | VERIFIED | Suppresses only when INI truthy and CLI attr not `None`. |
| `entrypoint.py` | CLI backend | leaves `cucumber_js_json_path` intact | VERIFIED | CLI-only and both-set tests produce CLI output. |
| `entrypoint.py` | xdist worker mode | `workerinput` guard | VERIFIED | Guard returns before any config reads/mutations. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `entrypoint.py` | `ini_value` | `config.getini("cucumber_json_path")` | Yes | FLOWING |
| `entrypoint.py` | `cli_value` | `config.option.cucumber_js_json_path` | Yes | FLOWING |
| `entrypoint.py` | `_inicache["cucumber_json_path"]` | mutation when both set | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Dispatcher integration + contract tests | `uv run python -m pytest tests/cases/integration/cucumber_json/ tests/cases/contract/contract/test_cucumber_json_dispatcher_contract.py -q` | `10 passed in 13.76s` | PASS |
| Existing plugin pattern + formatter CLI contracts | `uv run python -m pytest tests/cases/contract/contract/test_plugin_patterns_contract.py tests/cases/contract/contract/test_cucumber_formatter_cli_contract.py -q` | `16 passed in 7.01s` | PASS |
| Direct import + constants | `uv run python -c ...` | `entrypoint OK`; expected constant strings printed | PASS |
| Editable install import | `uv pip install -e . --quiet && uv run python -c ...` | `entrypoint OK` | PASS |
| Dispatcher collection | `uv run python -m pytest --co -q tests/cases/integration/cucumber_json/` | 6 dispatcher tests collected | PASS |
| Existing cucumber_json e2e | `uv run python -m pytest tests/cases/e2e/ -k cucumber_json -q` | `2 passed, 129 deselected in 15.16s` | PASS |
| Integration regression group | `uv run python -m pytest tests/cases/integration/ -q --tb=short` | `2 failed, 264 passed, 3 skipped` | FAIL |

### Probe Execution

No phase-declared `scripts/*/tests/probe-*.sh` probes found or required.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| None | 13-01/13-02/13-03 | Plans list `requirements: []`; `.planning/REQUIREMENTS.md` has no Phase 13 IDs | VERIFIED | No orphaned Phase 13 requirement IDs found. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/plugin.py` | 9 | `placeholder` in docstring | INFO | Intentional canonical plugin class placeholder required by plan. |
| `src/pytest_bdd/plugin/cucumber_json_dispatcher/hook.py` | 4 | `placeholder` in docstring | INFO | Intentional canonical hook surface placeholder required by plan. |
| `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py` | 148, 194, 195 | empty set/list/string assertions | INFO | Test assertions, not product stub data. |

### Human Verification Required

None.

### Gaps Summary

Dispatcher implementation itself is present, substantive, wired, and behavior-tested. CLI-wins works by clearing INI cache before legacy INI backend reads it; old INI and CLI backend entry points remain distinct and active.

Full integration test suite now passes. A hallucinated `ExternalAttachment` class introduced in 13-03 was removed from both the runtime and integration tests, eliminating the previous test failures. Phase 13 execution is completely finished.

---

_Verified: 2026-05-20T07:28:00Z_
_Verifier: the agent (gsd-verifier)_
