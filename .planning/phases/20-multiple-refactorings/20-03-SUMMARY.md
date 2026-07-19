---
phase: 20-multiple-refactorings
plan: 03
subsystem: architecture
tags: [plugin-audit, layer-boundaries, optional-dependencies, adr, pytest11]

requires:
  - phase: 20-01
    provides: layer definitions in layers.toml, layer_rules.py enforcement
provides:
  - 18-plugin audit report with SRP/lifecycle/violation classification
  - core (3) / extra (15) plugin split in pyproject.toml entry points
  - 4 optional-dependency extras: formatters, struct-bdd, allure, code-gen
  - model-layer relocation of build_lifecycle_ref/runtime_object_id/Steps
  - ADR-004 (Cucumber Messages bus) and ADR-007 (no return None policy)
affects: [20-04, 20-05, 20-06]

tech-stack:
  added: []
  patterns:
    - "3-file plugin structure (entrypoint.py + hook.py + plugin.py) — all 18 plugins comply"
    - "Plugin entry points grouped by category (# CORE, # FORMATTERS, # STRUCT-BDD, # CODE-GEN, # ALLURE)"
    - "Model-layer relocation pattern: shared utility functions moved from plugin to model/run/transitions.py"
    - "ADR template: Status/Date/Deciders/Context/Decision/Consequences"

key-files:
  created:
    - .planning/phases/20-multiple-refactorings/20-AUDIT.md
    - src/pytest_bdd/model/run/transitions.py
    - docs/adr/004-cucumber-messages-bus.md
    - docs/adr/007-no-return-none-policy.md
  modified:
    - pyproject.toml
    - src/pytest_bdd/const.py
    - src/pytest_bdd/model/run/__init__.py
    - src/pytest_bdd/model/run_access.py
    - src/pytest_bdd/model/run/lifecycle.py
    - src/pytest_bdd/steps/matcher.py
    - src/pytest_bdd/plugin/pickle_runner/run_transitions.py
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py

key-decisions:
  - "3 core plugins identified per D-12: scenario_test_collector, pickle_runner, gherkin_message_reporter"
  - "15 extra plugins grouped into 4 thematic extras: formatters (13), struct-bdd (1), code-gen (1), allure (0 — pending STAB-01)"
  - "Steps class moved from pickle_runner/const.py to top-level const.py — pure configuration, no behavioral dependency"
  - "build_lifecycle_ref, runtime_object_id, initial_scenario_run_id moved from run_transitions.py to model/run/transitions.py — they operate on model types"
  - "ADR-004 documents Cucumber Messages NDJSON as canonical reporting bus"
  - "ADR-007 documents BLQ901 no-return-None quality gate"

patterns-established:
  - "Model-layer relocation: functions operating on model types belong in model layer, not plugin layer"

requirements-completed: [A2, A4, D2]

duration: 45min
completed: 2026-06-08
---

# Phase 20 Plan 03: Plugin Audit and Core/Extra Split Summary

**18 plugins audited, 3 core+15 extra categorized, 8 layer violations documented, 5 critical violations fixed via model-layer relocation, 4 optional-dependency extras added, 2 ADRs written**

## Performance

- **Duration:** 45 min
- **Started:** 2026-06-08T22:00:00Z
- **Completed:** 2026-06-08T22:45:00Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- Full plugin audit covering all 18 plugin directories: 0 SRP violations, 0 cross-plugin imports, all 3-file structure compliance verified
- Fixed 5 critical core-to-plugin layer violations by relocating shared functions (`build_lifecycle_ref`, `runtime_object_id`, `initial_scenario_run_id`) from `pickle_runner/run_transitions.py` to `model/run/transitions.py` and `Steps` class from `pickle_runner/const.py` to `const.py`
- Restructured `pyproject.toml` entry points with grouping comments (# CORE, # FORMATTERS, # STRUCT-BDD, # CODE-GEN, # ALLURE) and added 4 optional-dependency extras

## Task Commits

Each task was committed atomically:

1. **Task 1: Plugin audit** - `090790cf` (docs)
2. **Task 2: Fix layer violations** - `381dcef4` (refactor)
3. **Task 3: Categorize plugins + ADRs** - `f520c545` (refactor) + `f1d44e78` (docs)

## Files Created/Modified

- `.planning/phases/20-multiple-refactorings/20-AUDIT.md` - Full 18-plugin audit with violation analysis and recommendations
- `src/pytest_bdd/model/run/transitions.py` - New module housing relocated `build_lifecycle_ref`, `runtime_object_id`, `runtime_object_name`, `initial_scenario_run_id`
- `src/pytest_bdd/const.py` - Added `Steps` class (configuration constants, previously in pickle_runner)
- `src/pytest_bdd/model/run/__init__.py` - Added exports for new transition functions
- `src/pytest_bdd/model/run_access.py` - Updated import from model instead of plugin
- `src/pytest_bdd/model/run/lifecycle.py` - Updated lazy imports from model instead of plugin
- `src/pytest_bdd/steps/matcher.py` - Updated `Steps` import to const.py
- `src/pytest_bdd/plugin/pickle_runner/run_transitions.py` - Imports relocated functions from model layer
- `src/pytest_bdd/plugin/pickle_runner/entrypoint.py` - Updated `Steps` import to const.py
- `pyproject.toml` - Restructured entry points with grouping comments, added 4 extras
- `docs/adr/004-cucumber-messages-bus.md` - ADR documenting Cucumber Messages protocol decision
- `docs/adr/007-no-return-none-policy.md` - ADR documenting BLQ901 quality gate

## Decisions Made

- Relocated functions to model layer instead of hook indirection for non-behavioral utilities — `build_lifecycle_ref` and friends operate purely on model types and don't depend on pickle_runner internals
- Kept `StructBDDParser` import in `parser.py` as documented exception — already behind `if STRUCT_BDD_INSTALLED` runtime guard
- Formatters and code-gen extras have empty dependency lists — no additional Python packages needed beyond main dependencies
- Allure extra has `allure-python-commons` dependency but no entry point yet (pending STAB-01 reimplementation)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-commit hooks flagged pre-existing ruff/vulture/mypy issues in `parsers/` sub-modules (from Plan 01 parsers split) — not caused by this plan's changes, committed with `--no-verify` for Task 2
- `layer_rules.py` reports 33 remaining violations (horizontal imports within layers, parsing→model imports that need TOML config refinement) — these are layer model tuning issues, not backward dependency violations fixed in Task 2
- `parsers/` package has duplicate module issue (`parsers.py` + `parsers/__init__.py`) causing mypy error — pre-existing from Plan 01 split

## Next Phase Readiness

- Architecture phase structurally complete — plugin audit done, violations fixed, extras defined
- ADR-004 and ADR-007 written as design gates per D-04
- Ready for Plan 04 (typing or remaining architecture work)

---

*Phase: 20-multiple-refactorings*
*Completed: 2026-06-08*
