---
phase: 04-plugin-refactoring
plan: "03"
subsystem: plugin-refactoring
tags: [code-generator, class-plugin, codegen, refactor]
requires:
  - phase: 04-02
    provides: plugin structure contract and generation safety checks
provides:
  - CodeGeneratorPlugin class
  - code_generator canonical hook module
  - split code generation request, collection, and rendering helpers
affects: [plugin-refactoring, code-generation]
tech-stack:
  added: []
  patterns:
    - class-based pytest plugin orchestration
    - responsibility split for code generator helpers
key-files:
  created:
    - src/pytest_bdd/plugin/code_generator/collection.py
    - src/pytest_bdd/plugin/code_generator/hook.py
    - src/pytest_bdd/plugin/code_generator/rendering.py
    - src/pytest_bdd/plugin/code_generator/request.py
  modified:
    - src/pytest_bdd/plugin/code_generator/entrypoint.py
    - src/pytest_bdd/plugin/code_generator/plugin.py
    - tests/generation/test_generate_missing.py
key-decisions:
  - "Code generation command execution now delegates through CodeGeneratorPlugin."
  - "Missing --feature exits before wrap_session so code generation keeps deterministic exit status 100."
patterns-established:
  - "Plugin entrypoints may keep option registration but delegate command behavior to a package plugin class."
requirements-completed: [REF-02]
duration: 32 min
completed: 2026-05-13
---

# Phase 04 Plan 03: Code Generator Class Refactor Summary

Code generator plugin class orchestration with request, collection, and rendering helper modules while preserving generation behavior.

## Performance

- **Duration:** 32 min
- **Started:** 2026-05-13T20:26:00Z
- **Completed:** 2026-05-13T20:57:54Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Added `CodeGeneratorPlugin` and changed `entrypoint.py` to delegate `pytest_cmdline_main` through that class.
- Added canonical `src/pytest_bdd/plugin/code_generator/hook.py` placeholder for package structure.
- Split code generator helpers into `request.py`, `collection.py`, and `rendering.py`.
- Reduced `src/pytest_bdd/plugin/code_generator/plugin.py` from 522 lines to 175 lines.
- Added generation regression coverage for missing `--feature` returning exit status `100`.

## Task Commits

1. **Tasks 1-3: CodeGeneratorPlugin class, helper split, and behavior preservation** - `8bdf20b6` (refactor)

**Plan metadata:** this docs commit

## Files Created/Modified

- `src/pytest_bdd/plugin/code_generator/collection.py` - feature/pickle/step collection helpers.
- `src/pytest_bdd/plugin/code_generator/hook.py` - canonical hook module placeholder.
- `src/pytest_bdd/plugin/code_generator/rendering.py` - template loading, formatting, generated-code rendering, and string helpers.
- `src/pytest_bdd/plugin/code_generator/request.py` - request/option helpers including `check_existence`.
- `src/pytest_bdd/plugin/code_generator/plugin.py` - focused `CodeGeneratorPlugin` orchestration.
- `src/pytest_bdd/plugin/code_generator/entrypoint.py` - option registration plus class delegation.
- `tests/generation/test_generate_missing.py` - exit status `100` regression for missing `--feature`.

## Decisions Made

- Kept option registration in `entrypoint.py`; no plugin state is needed for `pytest_addoption`.
- Moved missing `--feature` validation before `wrap_session` to avoid pytest normalizing a no-test session to exit code 0.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added explicit exit-status regression**

- **Found during:** Task 3 (Preserve code generation behavior)
- **Issue:** Existing tests covered `--generate` and `--generate-missing`, but did not assert the documented exit status `100` when `--feature` is omitted.
- **Fix:** Added `test_generate_missing_without_feature_returns_100` and adjusted `CodeGeneratorPlugin` to return 100 before `wrap_session`.
- **Files modified:** `tests/generation/test_generate_missing.py`, `src/pytest_bdd/plugin/code_generator/plugin.py`
- **Verification:** `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/generation -q` — 14 passed.
- **Committed in:** `8bdf20b6`

**2. [Execution Granularity] Combined tightly coupled tasks into one commit**

- **Found during:** Task 1/2 execution
- **Issue:** Introducing `CodeGeneratorPlugin` and splitting helpers required the same import graph change; splitting commits would leave transient broken imports.
- **Fix:** Committed the code generator class, helper split, and behavior test together.
- **Files modified:** code generator package and generation test.
- **Verification:** focused import, line-count, generation, and feature tests passed.
- **Committed in:** `8bdf20b6`

---

**Total deviations:** 2 auto-fixed.
**Impact on plan:** Scope stayed within code generator refactor and behavior preservation.

## Issues Encountered

- The plan's `-o addopts=''` generation command removes the repository's `-p pytester` addopts, so `testdir` fixtures disappear. Verification used the documented local command with project addopts intact.

## Verification

- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -c "from pytest_bdd.plugin.code_generator.plugin import CodeGeneratorPlugin; print(CodeGeneratorPlugin.__name__)"` — passed, printed `CodeGeneratorPlugin`.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python - <<'PY' ...` line-count check — passed, `plugin.py` has 175 lines.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/generation -q` — 14 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/generation tests/feature -q` — 94 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_plugin_structure_contract.py -q` — expected red, 1 failed. Code generator-specific failures are resolved; remaining failures start at cucumber formatter package normalization.
- `uvx pre-commit run ruff-check --all-files && uvx pre-commit run ruff-format --all-files` — passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 04-04. The plugin structure contract now points past code generator and into remaining formatter/package normalization work.

---
*Phase: 04-plugin-refactoring*
*Completed: 2026-05-13*
