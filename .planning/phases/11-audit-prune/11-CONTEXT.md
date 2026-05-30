# Phase 11: Audit & Prune - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Zero dead code, unused imports, or stale modules; full CI matrix validation.

**Requirement:** SIM-03 — "Audit and prune underused plugin/utility modules"

**Scope:**
1. Remove all dead imports — ruff F401/F811 must pass clean
2. Evaluate underused plugin/utility modules: keep (with documented justification) or remove
3. Remove all commented-out code blocks (except deprecation-path documentation)
4. Split large files: steps.py (803L), message_capability_governance.py (751L), run.py (630L) into logical sub-modules
5. Full CI matrix validation — all Python 3.10-3.14 × pytest 7.x-latest combinations
6. Document decopatch health status (keep as-is, no replacement)

**Exclusions:**
- decopatch replacement → deferred (keep as-is)
- New plugin development → not in scope
- `parsers.py` modifications — FROZEN (tests only)
- Python version support matrix changes — keep 3.10-3.14

</domain>

<decisions>
## Implementation Decisions

### Decopatch Dependency

- **D-01:** Keep decopatch as-is — functional, stable, low risk. Not worth rewrite during stabilization phase. Document health status in audit report.

### Large File Splitting

- **D-02:** Split `steps.py` (803L) — separate StepDefinitionManager.Registry, StepDefinitionManager.Matcher, StepDefinitionManager.Definition into sub-modules
- **D-03:** Split `message_capability_governance.py` (751L) — separate governance logic into logical sub-modules
- **D-04:** Split `run.py` (630L) — further modularize runtime execution code (already split from scenario_run.py 1422L in earlier phase)

### Plugin Audit Strategy

- **D-05:** Keep all 17 active plugins — audit each, document usage justification. Remove only truly dead/zero-consumer plugins. No removals based on assumed low usage.
- **D-06:** All 17 plugins confirmed active with entry points in pyproject.toml — none are dead code

### CI Matrix Validation

- **D-07:** Full matrix validation required — all Python 3.10-3.14 × pytest 7.x-latest combinations (~20+ tox environments)
- **D-08:** CI matrix validation is a gate — phase fails if any combination in the matrix fails

### the agent's Discretion

- Exact sub-module naming and boundaries for large file splits
- Which specific plugins need usage documentation (all 17, but depth varies by complexity)
- Specific tox environment configuration for full matrix run

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/ROADMAP.md` — Phase 11 goal: "Dead code removal; stale module evaluation; final CI validation"
- `.planning/REQUIREMENTS.md` — SIM-03: "Audit and prune underused plugin/utility modules"
- `.planning/PROJECT.md` — Core value, constraints (ruff, attrs, StashBound, Python 3.10-3.14, pytest >=7.0.0)
- `.planning/phases/10-pattern-unification/10-CONTEXT.md` — Prior phase: plugin structure verified, cross-plugin imports eliminated
- `.planning/phases/09-compatibility-streamlining/09-CONTEXT.md` — Prior phase: compatibility layer consolidated

### Source Code — Large Files to Split
- `src/pytest_bdd/steps.py` (803 lines) — StepDefinitionManager with Registry, Matcher, Definition classes
- `src/pytest_bdd/model/message_capability_governance.py` (751 lines) — Message governance logic
- `src/pytest_bdd/model/run.py` (630 lines) — Runtime execution (split from scenario_run.py)

### Source Code — Plugin Registry (17 active)
- `pyproject.toml` — `[project.entry-points.pytest11]` section (lines 91-108), 17 plugin registrations
- `src/pytest_bdd/plugin/` — 17 active plugin directories (code_generator, cucumber_json, cucumber_json_formatter, cucumber_junit, cucumber_pretty, cucumber_progress, cucumber_progress_bar, cucumber_snippets, cucumber_summary, cucumber_usage, cucumber_usage_json, gherkin_message_reporter, gherkin_terminal_reporter, pickle_runner, scenario_reporter, scenario_test_collector, struct_bdd)

### Source Code — Decopatch Usage
- `src/pytest_bdd/hook.py` — decopatch.function_decorator for @given/@when/@then/@before_mark/@after_mark/@around_mark
- `pyproject.toml` — decopatch dependency (line 60), type ignore (line 197)

### Source Code — CI Matrix
- `src/pytest_bdd/compatibility/runtime_compat.py` (134 lines) — PYTEST_COMPATIBILITY_BOUNDS, is_pair_compatible()
- `src/pytest_bdd/util/matrix.py` (179 lines) — CI/tox helpers (build_matrix, expand_tox_env_names, etc.)
- `tox.ini` — tox environment configuration

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `model/stash_access.py` — StashBound base class, all plugin config access pattern
- `compatibility/runtime_compat.py` — Version compatibility bounds for Python/pytest matrix
- `util/matrix.py` — CI matrix generation utilities (build_matrix, expand_tox_env_names, discover_*)
- All 17 plugins — follow canonical entrypoint.py + hook.py + plugin.py structure (Phase 10)

### Established Patterns
- Plugin structure: entrypoint.py (pytest hooks), hook.py (hook specs), plugin.py (plugin class)
- `attrs` (@define, @frozen) for all data classes — no @dataclass instances
- `from __future__ import annotations` in all 86 source files
- ruff linting with ~60 rule categories, ERA001 (eradicate) enforced
- StashBound pattern: classvar STASH_KEY, classmethods for stash access
- Cross-plugin communication exclusively via pytest hook system

### Integration Points
- Large file splits → maintain existing public API imports (backward compatibility)
- Plugin audit → pyproject.toml entry points must be updated if any plugin removed
- CI matrix → tox.ini configuration, compatibility/runtime_compat.py bounds
- ruff gates → F401/F811/ERA001 must pass clean after audit

</code_context>

<specifics>
## Specific Ideas

- steps.py split: Registry (registration + parent chain), Matcher (three-pass matching), Definition (wrapped function + parser + converters) are natural boundaries
- message_capability_governance.py split: capability detection, status governance, checklist generation are separable concerns
- run.py split: already split from scenario_run.py — further split by execution lifecycle stages (setup, running, teardown)
- decopatch: last release 1.4.10 (2022-03-01), last commit 2024-06-01, 25 stars, open PR from Feb 2026 — stable but low-activity
- Only 1 TODO found in codebase: bdd_tree_to_rst.py side effect migration

</specifics>

<deferred>
## Deferred Ideas

- decopatch replacement evaluation → future phase (keep as-is for now)
- parsers.py refactoring → FROZEN (tests only)

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-Audit & Prune*
*Context gathered: 2026-05-16*
