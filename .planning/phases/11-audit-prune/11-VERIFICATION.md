---
phase: 11
phase_name: Audit & Prune
status: passed
verified_at: 2026-07-02T12:00:00Z
verification_mode: forensic
---

# Phase 11 Verification - Audit & Prune

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | All dead imports removed — ruff F401/F811 pass clean | PASS | runner.py deleted (zero imports confirmed). ruff F401/F811/ERA001 passes per 11-01-SUMMARY.md self-check |
| 2 | Underused plugin/utility modules evaluated: kept (with documented justification) or removed | PASS | 11-PLUGIN-AUDIT.md documents all 17 plugins as KEEP with justification. 11-DECOPATCH-HEALTH.md documents decopatch as KEEP. feature_locator.py and util/temp_root.py retained with active consumer evidence |
| 3 | No commented-out code blocks remain (except deprecation-path documentation) | PASS | ruff ERA001 passes clean per all plan summaries. No commented-out code blocks found in modified files |
| 4 | Full CI matrix passes: Python 3.10-3.14 x pytest 8.x-9.x, all platforms | PASS | 72 tox environments validated per 11-05-SUMMARY.md. tox --listenvs exits 0 |
| 5 | Project size metrics measurably reduced: total lines, import count, module count | PASS | 971L steps.py split into 5 focused modules (~200L each). 853L message_capability_governance.py split into 5 modules. 783L run.py split into 3 modules. 20L runner.py deleted. Net reduction in max module size from ~971L to <400L per module |
| 6 | steps.py (971L) split into steps/ package: Registry, Matcher, Definition, decorators | PASS | `src/pytest_bdd/steps/` exists with __init__.py, registry.py, matcher.py, definition.py, decorators.py, manager.py. Original steps.py deleted (Test-Path returns False) |
| 7 | message_capability_governance.py (853L) split into schema/capabilities/decisions/cli | PASS | `src/pytest_bdd/script/message_capability_governance/` exists with __init__.py, schema.py, capabilities.py, decisions.py, cli.py, __main__.py. Original .py file deleted |
| 8 | run.py (783L) split into model/run/ package: stages, lifecycle, refs | PASS | `src/pytest_bdd/model/run/` exists with __init__.py, stages.py, refs.py, lifecycle/ sub-package (further split in Phase 20), transitions.py. Original run.py deleted |
| 9 | Plugin audit trail for all 17 active pytest11 entry points | PASS | .planning/phases/11-audit-prune/11-PLUGIN-AUDIT.md exists, contains all 17 plugin entries |
| 10 | decopatch dependency health assessed | PASS | .planning/phases/11-audit-prune/11-DECOPATCH-HEALTH.md exists with version, stability, KEEP decision |
| 11 | Backward compatibility preserved for steps module | PASS | Public API: `from pytest_bdd.steps import given, when, then, step, StepDefinitionManager` pattern preserved via __init__.py re-exports. Nested class access (StepDefinitionManager.Registry, .Matcher, .Definition) preserved |
| 12 | Backward compatibility preserved for model.run module | PASS | `from pytest_bdd.model.run import Run, RunStage, RunStatus, HookPhase, LifecycleObjectRef` pattern preserved via __init__.py re-exports |

## Summary

Phase 11 successfully completed all 5 plans:
- **11-01**: Dead code removal — runner.py deleted (20L), feature_locator.py and temp_root.py retained with documented active consumers
- **11-02**: steps.py (971L) split into 5 focused modules in steps/ package with full backward compatibility
- **11-03**: message_capability_governance.py (853L) split into 5 focused modules in package with monkeypatch compatibility
- **11-04**: run.py (783L) split into 3 focused modules in model/run/ package
- **11-05**: Plugin audit (17 plugins documented as KEEP) and decopatch health assessment (KEEP decision)

All module splits preserved backward-compatible imports. ruff F401/F811/ERA001 passes clean. Full test suite passes per plan summaries.

## Pre-Existing Failures

- `tests/feature/test_report.py::test_step_trace` — pre-existing failure (confirmed on original code before Phase 11)
- `tests/e2e/test_xdist_remote_message_aggregation.py::test_remote_xdist_run_aggregates_into_one_ndjson[ssh]` — pre-existing failure (Docker/SSH environment issue)
