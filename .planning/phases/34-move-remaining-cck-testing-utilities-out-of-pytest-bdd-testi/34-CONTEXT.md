# Phase 34: Move remaining CCK testing utilities out of pytest_bdd/testing - Context

**Gathered:** 2026-07-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Move `cck.py` (CCK download/parsing utilities, 552 lines) from `src/pytest_bdd/testing/` to `src/pytest_bdd_toolchain/case/contract/cck/`. Delete the now-empty `src/pytest_bdd/testing/` directory. Update all 4 consumer imports to reference the new location.

This is cleanup — the test suite was already migrated to `pytest_bdd_toolchain` in prior phases, but the CCK utility module was left behind in `pytest_bdd/testing/`.

</domain>

<decisions>
## Implementation Decisions

### Destination
- **D-01:** Move `cck.py` to `src/pytest_bdd_toolchain/case/contract/cck/cck.py` — co-located with the three CCK test modules that consume it:
  - `conftest.py` — uses `download_all_cck_samples`, `extract_scenario_names`, `extract_step_texts`
  - `test_cck_allure_conversion.py` — uses `CCK_SAMPLE_NAMES`
  - `test_cck_allure_rendering.py` — uses `CCK_SAMPLE_NAMES`, `extract_scenario_names`, `extract_step_texts`

### Import Path Updates
- **D-02:** Direct import path updates only — no compatibility shims, no deprecation period.
  - Three files in `case/contract/cck/` switch to relative imports (`from .cck import ...`)
  - `step/steps_cck_allure.py` changes from `from pytest_bdd.testing.cck import download_cck_sample` to `from pytest_bdd_toolchain.case.contract.cck.cck import download_cck_sample`
  - Zero external consumers exist; all imports are within `pytest_bdd_toolchain`

### Package Cleanup
- **D-03:** Delete the entire `src/pytest_bdd/testing/` directory after the move. It contains only `__init__.py` (empty, just `__all__ = []`) with nothing remaining of value. No parent `__init__.py` references it, no `pyproject.toml` config references it.

### the agent's Discretion
- The planner/executor decides the exact order of operations for the move (copy-then-delete vs. git mv).
- The planner decides whether `cck.py` needs any internal changes beyond the module move (no API changes expected).
- The planner decides the verification strategy (run the CCK contract tests, import checks, lint checks).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source File to Move
- `src/pytest_bdd/testing/cck.py` — 552 lines of CCK download/parse/extract utilities. Contains `CCK_SAMPLE_NAMES` (44 samples), `download_cck_sample`, `download_all_cck_samples`, `extract_scenario_names`, `extract_step_texts`, `extract_expected_status`, and two private download strategies (`_download_via_gh_api`, `_download_via_urllib`).

### Consumer Files (import paths must be updated)
- `src/pytest_bdd_toolchain/case/contract/cck/conftest.py` — Imports `CCK_RELEASE_TAG`, `download_all_cck_samples`, `extract_scenario_names`, `extract_step_texts` from `pytest_bdd.testing.cck`
- `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_conversion.py` — Imports `CCK_SAMPLE_NAMES` from `pytest_bdd.testing.cck`
- `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_rendering.py` — Imports `CCK_SAMPLE_NAMES`, `extract_scenario_names`, `extract_step_texts` from `pytest_bdd.testing.cck`
- `src/pytest_bdd_toolchain/step/steps_cck_allure.py` — Imports `download_cck_sample` from `pytest_bdd.testing.cck`

### Source Directory to Delete
- `src/pytest_bdd/testing/__init__.py` — Empty placeholder (`__all__ = []`, `__tracebackhide__ = True`)

### Project Conventions
- `.planning/PROJECT.md` — Project constraints: ruff rules, attrs over dataclass, StashBound pattern, code style
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pytest_bdd_toolchain/case/contract/cck/` — Destination directory already exists with 3 test consumers. The move is purely additive to this directory.

### Established Patterns
- Prior phases already moved tests from `tests/` into `pytest_bdd_toolchain/case/` — this is the last remaining utility module that was overlooked
- `pytest_bdd_toolchain` uses a flat package structure under `case/contract/cck/` — no `__init__.py` in that directory, all imports are direct module references
- Relative imports used elsewhere in the toolchain (`.conftest` pattern) — consistent with D-02

### Integration Points
- Only 4 files reference `pytest_bdd.testing` — all identified above. No other modules, configs, or scripts reference this path.
- `src/pytest_bdd/__init__.py` does NOT import or reference `testing` — no re-export cleanup needed
</code_context>

<specifics>
## Specific Ideas

- The CCK contract tests in `case/contract/cck/` use multiple markers: `@pytest.mark.contract`, `@pytest.mark.xdist_group("cck")`, `@pytest.mark.docker`, `@pytest.mark.browser`, `@pytest.mark.slow` — these tests should continue to pass after the move
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 34-move-remaining-cck-testing-utilities-out-of-pytest-bdd-testi*
*Context gathered: 2026-07-12*
