---
phase: 32-implement-unbound-feature-detection
plan: 01
subsystem: testing
tags: [pytest, bdd, feature-detection, config-model]
requires: []
provides:
  - UnboundFeatures config model (bdd_unbound_features INI, --unbound-features CLI)
  - unbound.py detection module: _detect_unbound_features, _scan_feature_files, _extract_collected_feature_uris, _parse_feature_name, UnboundFeatureItem
  - ScenarioTestCollectorPlugin.pytest_collection_finish hook wiring
affects: [32-02-unbound-feature-tests]

key-files:
  created:
    - src/pytest_bdd/plugin/scenario_test_collector/unbound.py
  modified:
    - src/pytest_bdd/model/scenario_collection.py
    - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py

key-decisions:
  - "UnboundFeatures class follows EmptyScenarios config model pattern with Ini/Cli inner StrEnum classes"
  - "UnboundFeatureItem is a pytest.Item subclass parented to session, with nodeid='unbound::rel/path'"
  - "Severity dispatch: skip→pytest.skip, warn→warnings.warn, error→pytest.fail"
  - "--unbound-features CLI defaults to 'skip' for non-breaking rollout"
  - "xdist worker guard (hasattr session.config 'workerinput') prevents duplicate detection on workers"

patterns-established:
  - "Plugin config model pattern: namespace class with Ini(StrEnum) and Cli(StrEnum) inner classes"
  - "Detection engine: scan→extract→diff→inject pattern at pytest_collection_finish"
  - "Shortcut resolution: reuse FeatureFileModule static methods for .url/.desktop/.webloc"

requirements-completed: []

coverage:
  - id: D1
    description: "UnboundFeatures config model with Ini.SEVERITY_OPTION (bdd_unbound_features) and Cli.SEVERITY_OPTION (unbound_features)"
    verification:
      - kind: unit
        ref: "python -c 'from pytest_bdd.model.scenario_collection import UnboundFeatures; assert UnboundFeatures.Ini.SEVERITY_OPTION == ...'"
        status: pass
    human_judgment: false
  - id: D2
    description: "--unbound-features CLI flag and bdd_unbound_features INI option registered in pytest_addoption"
    verification:
      - kind: integration
        ref: "python -m pytest --help | grep unbound-features"
        status: pass
    human_judgment: false
  - id: D3
    description: "unbound.py detection module: _detect_unbound_features, _scan_feature_files, _extract_collected_feature_uris, _parse_feature_name, UnboundFeatureItem"
    verification:
      - kind: unit
        ref: "python -c 'from pytest_bdd.plugin.scenario_test_collector.unbound import ...'"
        status: pass
    human_judgment: false
  - id: D4
    description: "ScenarioTestCollectorPlugin.pytest_collection_finish hook calling _detect_unbound_features"
    verification:
      - kind: unit
        ref: "ast parse; ruff check"
        status: pass
    human_judgment: false

duration: 65min
completed: 2026-07-10
status: complete
---

# Phase 32-01: Unbound Feature Detection Core

**Config model, CLI/INI options, detection engine, and hook integration for reporting orphaned .feature files as SKIPPED items in pytest output**

## Performance

- **Duration:** ~65 min
- **Tasks:** 3
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments
- Added `UnboundFeatures` config model class to `scenario_collection.py` with `Ini.SEVERITY_OPTION = "bdd_unbound_features"` and `Cli.SEVERITY_OPTION = "unbound_features"`
- Registered `--unbound-features` CLI flag (choices: skip|warn|error, default: skip) and `bdd_unbound_features` INI option in `entrypoint.py`
- Created `unbound.py` detection module with `UnboundFeatureItem` (pytest.Item subclass), `_scan_feature_files` (recursive scan with symlink/loop guards, @unbound tag exclusion, shortcut resolution), `_extract_collected_feature_uris`, `_parse_feature_name`, and `_detect_unbound_features` orchestrator
- Wired `pytest_collection_finish` hook in `ScenarioTestCollectorPlugin` with `trylast=True` and xdist worker guard

## Task Commits

1. **Task 1: Add UnboundFeatures config model** - `f6da42a` (feat)
2. **Task 2: Register --unbound-features CLI and INI options** - `423fff5` (feat)
3. **Task 3: Create unbound.py + wire hook** - `f198392` (feat)

## Files Created/Modified
- `src/pytest_bdd/model/scenario_collection.py` - Added `UnboundFeatures` class with Ini/Cli inner StrEnum classes and `__all__` export
- `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py` - Added `--unbound-features` CLI option and `bdd_unbound_features` INI registration
- `src/pytest_bdd/plugin/scenario_test_collector/unbound.py` - **NEW** Detection engine module (236 lines) with all detection functions
- `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` - Added `UnboundFeatures` import, `Session` to compatibility imports, and `pytest_collection_finish` hook method to `ScenarioTestCollectorPlugin`

## Decisions Made
- None - followed plan as specified

## Deviations from Plan

### Auto-fixed Issues

**1. [ruff - complex-structure] Extracted _process_file helper from _scan_feature_files**
- **Found during:** Task 3 (ruff lint)
- **Issue:** `_scan_feature_files` hit complexity limit (11 > 10)
- **Fix:** Extracted inner loop body into `_process_file` helper function
- **Files modified:** src/pytest_bdd/plugin/scenario_test_collector/unbound.py

**2. [mypy - arg-type] Fixed type annotations for _process_file parameters**
- **Found during:** Task 3 (pre-commit mypy hook)
- **Issue:** Incompatible types for `collectible_suffixes` (`set[Suffix]` vs `frozenset[Suffix]`) and `shortcut_resolver` dict invariance
- **Fix:** Changed to `set[Suffix]` and `Mapping[str, Callable[[Path], Any]]`; added `# type: ignore[call-arg]` for `pytest.Item` super().__init__ call
- **Files modified:** src/pytest_bdd/plugin/scenario_test_collector/unbound.py

---

**Total deviations:** 2 auto-fixed (1 ruff complexity, 1 mypy typing)
**Impact on plan:** Both auto-fixes necessary for lint/type compliance. No scope creep.

## Issues Encountered
- File had duplicated docstring blocks making `edit` tool unable to match uniquely; used Python AST insertion and bash heredoc append as workarounds
- Pre-commit hooks timed out at 120s on earlier attempts; resolved on third attempt

## Next Phase Readiness
- 32-01 core detection engine complete
- Ready for 32-02: unit and integration tests

---
*Phase: 32-implement-unbound-feature-detection*
*Completed: 2026-07-10*
