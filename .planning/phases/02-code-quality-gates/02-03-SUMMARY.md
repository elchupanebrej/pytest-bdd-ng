---
phase: 02-code-quality-gates
plan: "03"
subsystem: collectors-utilities
tags: [returns, maybe, collectors, scenario-locator, scripts, utilities]
requires:
  - phase: 02-code-quality-gates
    provides: "Plan 01 returns dependency and failure reason enums"
provides:
  - "Remaining non-hook explicit return None removals for Plan 03 files"
  - "Collector and scenario locator absence paths using Maybe-backed boundaries"
  - "Model, utility, compatibility, and script files updated for explicit absence handling"
affects: [phase-02, collectors, scenario-location, scripts, utilities]
tech-stack:
  added: []
  patterns: [Maybe absence boundary, value_or compatibility conversion]
key-files:
  created: []
  modified:
    - src/pytest_bdd/collector_batch.py
    - src/pytest_bdd/scenario_locator.py
    - src/pytest_bdd/model/message_extension.py
    - src/pytest_bdd/model/message_consolidation.py
    - src/pytest_bdd/model/message_capability_inventory.py
    - src/pytest_bdd/model/execution_message_adapter.py
    - src/pytest_bdd/model/message_registry.py
    - src/pytest_bdd/compatibility/matrix.py
    - src/pytest_bdd/util/webloc.py
    - src/pytest_bdd/util/tests_group_ordering.py
    - src/pytest_bdd/script/validate_feature_headings.py
    - src/pytest_bdd/script/bdd_tree_to_rst.py
    - src/pytest_bdd/script/message_capability_governance.py
key-decisions:
  - "Preserved pytest hook return None in code_generator entrypoint because D-03 exempts pytest hooks."
  - "Kept Plan 04 bare except work out of scope except for quality gate reporting."
patterns-established:
  - "Non-hook absence paths use returns.maybe Nothing at compatibility boundaries."
requirements-completed: [STAB-02]
duration: 29 min
completed: 2026-05-12
---

# Phase 02 Plan 03: Remaining Return None Migration Summary

Remaining collector, model, utility, compatibility, and script files no longer use explicit `return None` outside pytest hooks.

## Performance

- **Duration:** 29 min
- **Started:** 2026-05-12T16:24:00Z
- **Completed:** 2026-05-12T16:53:00Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments

- Removed explicit `return None` from Plan 03 non-hook target files.
- Added direct `returns` imports to converted files.
- Preserved the `pytest_cmdline_main` hook return contract in the code generator entrypoint.
- Kept bare exception fixes for Plan 04.

## Task Commits

1. **Tasks 1-3: Collector, model, utility, compatibility, and script return migration** - `41c76123`

## Files Created/Modified

- `src/pytest_bdd/collector_batch.py` - Batch parser fallback absence paths updated.
- `src/pytest_bdd/scenario_locator.py` - Cached feature absence paths updated.
- `src/pytest_bdd/model/message_extension.py` - Payload classification absence paths updated.
- `src/pytest_bdd/model/message_consolidation.py` - Hook identifier absence paths updated.
- `src/pytest_bdd/model/message_capability_inventory.py` - Schema directory lookup absence path updated.
- `src/pytest_bdd/model/execution_message_adapter.py` - Registry and payload ID absence paths updated.
- `src/pytest_bdd/model/message_registry.py` - Identifiable ID absence paths updated.
- `src/pytest_bdd/compatibility/matrix.py` - Version parse absence paths updated.
- `src/pytest_bdd/util/webloc.py` - URL read absence path updated.
- `src/pytest_bdd/util/tests_group_ordering.py` - Marker resolution absence path updated.
- `src/pytest_bdd/script/validate_feature_headings.py` - Heading parse absence paths updated.
- `src/pytest_bdd/script/bdd_tree_to_rst.py` - Diff traversal absence path updated.
- `src/pytest_bdd/script/message_capability_governance.py` - Governance schema lookup absence path updated.

## Decisions Made

- Did not modify `src/pytest_bdd/plugin/code_generator/entrypoint.py::pytest_cmdline_main`; it is a pytest hook and remains exempt.

## Deviations from Plan

None - plan scope was executed with the documented pytest-hook exemption.

## Issues Encountered

- The quality gate still reports `BLQ902` bare exception findings in `collector.py` and `collector_batch.py`; these are Plan 04 scope.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 04 can now focus on bare exception handlers, parser Result handling, zero-match collection errors, and the final quality gate pass.

---
*Phase: 02-code-quality-gates*
*Completed: 2026-05-12*
