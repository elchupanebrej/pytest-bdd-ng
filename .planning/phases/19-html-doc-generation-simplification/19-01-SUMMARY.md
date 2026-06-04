---
phase: 19-html-doc-generation-simplification
plan: 01
subsystem: docs
tags: [sphinx, myst, feature-tree, pytest, ruff]

requires:
  - phase: 19-html-doc-generation-simplification
    provides: Phase 19 context and approved feature-tree migration design
provides:
  - Shared ordering-prefix validation utility for feature documentation sources
  - Local Sphinx extension that validates and copies feature Markdown sources
  - Contract tests for ordering failures, generated MyST toctrees, and manual block preservation
affects: [docs, feature-doc-generation, phase-19]

tech-stack:
  added: []
  patterns:
    - Sphinx builder-inited extension for transient feature Markdown mirroring
    - Shared feature-tree validation utility under pytest_bdd.script

key-files:
  created:
    - src/pytest_bdd/script/_feature_tree.py
    - docs/ext/__init__.py
    - docs/ext/feature_tree.py
  modified:
    - tests/cases/contract/doc/test_doc.py

key-decisions:
  - "Feature-tree ordering validation now lives outside the pypandoc/RST conversion script."
  - "The Sphinx extension raises ExtensionError for validation, copy, and write failures instead of warning."
  - "Feature documentation contract tests no longer depend on pypandoc or generated .feature.rst output."

patterns-established:
  - "Use explicit MyST markers in docs/features/features.md to preserve manual text around generated toctrees."
  - "Use walk_feature_tree() for deterministic prefix-ordered feature source traversal."

requirements-completed: []

duration: 45 min
completed: 2026-06-04
---

# Phase 19 Plan 01: Feature Tree Foundation Summary

**Sphinx feature-tree foundation with shared ordering validation, hard-fail build preparation, and contract coverage for MyST feature indexes**

## Performance

- **Duration:** 45 min
- **Started:** 2026-06-04T06:39:00Z
- **Completed:** 2026-06-04T07:24:14Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Added `src/pytest_bdd/script/_feature_tree.py` with `OrderingValidationError`, prefix parsing, duplicate/missing sibling validation, and deterministic feature-tree walking.
- Added `docs/ext/feature_tree.py`, a local Sphinx extension that validates `features/`, copies `.feature.md` files into `docs/features/`, and writes MyST `{toctree}` blocks between generated markers.
- Replaced old doc contract tests that imported `bdd_tree_to_rst` and asserted `.feature.rst` generation with tests for shared validation and extension behavior.

## Task Commits

1. **Task 19-01-01: Shared feature-tree ordering utility** - `719f7bc3` (`feat`)
2. **Task 19-01-02: Sphinx feature-tree extension** - `7fdf7cb7` (`feat`)
3. **Task 19-01-03: Contract tests** - `7c40aced` (`test`)

## Files Created/Modified

- `src/pytest_bdd/script/_feature_tree.py` - Shared feature-tree ordering and validation helpers.
- `docs/ext/__init__.py` - Local Sphinx extension package marker required by ruff.
- `docs/ext/feature_tree.py` - Builder-inited Sphinx extension for feature Markdown copying and generated MyST toctrees.
- `tests/cases/contract/doc/test_doc.py` - Contract tests for ordering errors, extension hook registration, toctree output, manual text preservation, and hard Sphinx errors.

## Verification

- `uv run --extra test python -m pytest tests/cases/contract/doc/test_doc.py` - PASS, 6 tests passed; used once to sync the declared `test` extra because `pytest-order` was absent.
- `uv run python -m pytest tests/cases/contract/doc/test_doc.py` - PASS, 6 tests passed.
- `uv run ruff check src/pytest_bdd/script/_feature_tree.py docs/ext/feature_tree.py tests/cases/contract/doc/test_doc.py` - PASS.
- Task 19-01-01 acceptance snippets passed for duplicate prefix, missing prefix, deterministic file order, and `from __future__ import annotations`.
- Task 19-01-02 acceptance snippets passed for generated `features.md`, copied Markdown feature pages, suffixless toctree entries, manual block preservation, and `ExtensionError` on validation failure.

## Decisions Made

- Kept the new utility small and conversion-free so future deletion of `bdd_tree_to_rst.py` does not remove ordering validation.
- Used Sphinx `ExtensionError` as the hard-fail mechanism for invalid trees, copy failures, and index write failures.
- Loaded the local extension by path in tests to avoid requiring `docs/ext` to be on `sys.path`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added local extension package marker**
- **Found during:** Task 19-01-02 (Sphinx feature-tree extension)
- **Issue:** `ruff check docs/ext/feature_tree.py` rejected the new extension as an implicit namespace package.
- **Fix:** Added `docs/ext/__init__.py`.
- **Files modified:** `docs/ext/__init__.py`
- **Verification:** `uv run ruff check docs/ext/__init__.py docs/ext/feature_tree.py` passed before commit; final plan ruff verification also passed.
- **Committed in:** `7fdf7cb7`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required for repository lint compliance. No behavioral scope expansion.

## Issues Encountered

- The first exact pytest verification failed before test collection because `pytest-order` was not present in the current `uv run` environment while `pyproject.toml` config uses `--order-scope=session`. Running `uv run --extra test python -m pytest tests/cases/contract/doc/test_doc.py` synced the declared test extra, then the exact plan pytest command passed.

## Known Stubs

None.

## Threat Flags

None - new generated-block and copy surfaces match the plan threat model mitigations T-19-01 and T-19-02.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Plan 19-02. The feature-tree validation and Sphinx extension foundation exists, but later plans still need to wire the extension into Sphinx configuration, migrate durable docs files, remove the old RST/pandoc pipeline, and update ignore/dependency metadata.

## Self-Check: PASSED

- Files found: `src/pytest_bdd/script/_feature_tree.py`, `docs/ext/__init__.py`, `docs/ext/feature_tree.py`, `tests/cases/contract/doc/test_doc.py`, `.planning/phases/19-html-doc-generation-simplification/19-01-SUMMARY.md`.
- Commits found: `719f7bc3`, `7fdf7cb7`, `7c40aced`.

---
*Phase: 19-html-doc-generation-simplification*
*Completed: 2026-06-04*
