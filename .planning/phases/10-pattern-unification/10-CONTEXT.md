# Phase 10: Pattern Unification - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Consistent programming patterns across all plugins and core modules — no cross-plugin imports, uniform StashBound usage, lint gate for pattern enforcement.

**Requirement:** SIM-02 — "Unify programming approaches across plugins (consistent patterns)"

**Scope:**
1. Remove empty plugin directories (`cucumber_formatter_support`, `scenario_runner`)
2. Verify all plugins follow identical `class + entrypoint + hook.py + plugin.py` structure
3. Confirm no cross-plugin direct imports between plugin modules — all inter-plugin state via hooks
4. Verify `StashBound` pattern used uniformly for all `pytest.config.stash` access
5. Confirm `attrs` library used consistently across all data classes (no stdlib `dataclass`)
6. Add custom ruff/pre-commit lint gate for plugin pattern validation

**Exclusions:**
- Dead code audit and pruning → Phase 11
- Decopatch replacement → Phase 11 (document status, defer action)
- `parsers.py` modifications — FROZEN (tests only)
- New plugin development — not in scope

</domain>

<decisions>
## Empty Plugin Directories

- **D-01:** Remove `cucumber_formatter_support` and `scenario_runner` directories — both are empty, no entry points reference them in pyproject.toml

## Plugin Structure Consistency

- **D-02:** All 17 active plugins already follow `entrypoint.py + hook.py + plugin.py` structure — no structural changes needed
- **D-03:** `gherkin_message_reporter` entrypoint uses class methods on `_QuietTerminalReporter` (TerminalReporter subclass) — this is correct pytest pattern, not an inconsistency

## Cross-Plugin Imports

- **D-04:** No cross-plugin imports found between different plugin packages — only intra-plugin imports within same package (e.g., `gherkin_message_reporter` internal modules) — already compliant

## StashBound Coverage

- **D-05:** All 5 StashBound subclasses confirmed: `Run`, `FeatureBatchParser`, `_ReporterStateEntry`, `ReportingEventSenderBinding`, `EnvelopeRegistry`
- **D-06:** Only direct `config.stash[` reference is in `types/exception.py` error message formatting — not actual stash access — no migration needed

## attrs vs dataclass

- **D-07:** No `@dataclass` instances found in codebase — already fully using `attrs` (`@define`, `@frozen`)

## Decopatch Status

- **D-08:** Document decopatch health status (last release 2022, low activity but functional, open PR pending merge). Defer replacement evaluation to Phase 11 (Audit & Prune)

## Lint Gate

- **D-09:** Add custom ruff/pre-commit check that validates: entrypoint.py, hook.py, plugin.py exist in each plugin directory; no cross-plugin imports between different plugin packages; StashBound used for all config.stash access. Fails CI if violations found.

### the agent's Discretion
- Exact implementation approach for lint gate (custom ruff rule vs pre-commit script vs validation script)
- Specific ruff rule codes or custom plugin for pattern validation
- Whether to add plugin structure documentation in DEVELOPMENT.rst

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/ROADMAP.md` — Phase 10 goal: "Consistent plugin patterns; eliminate cross-plugin imports"
- `.planning/REQUIREMENTS.md` — SIM-02: "Unify programming approaches across plugins (consistent patterns)"
- `.planning/PROJECT.md` — Core value, constraints (ruff, attrs, StashBound, no comments unless asked)
- `.planning/STATE.md` — Blockers: "Decopatch health unverified — audit needed during Phase 10"
- `.planning/codebase/ARCHITECTURE.md` — Plugin-oriented architecture overview, layer definitions, data flow
- `.planning/codebase/CONVENTIONS.md` — Coding conventions, import organization, attrs usage patterns

### Source Code — Plugin Directory Structure
- `src/pytest_bdd/plugin/` — 19 directories (17 active, 2 empty for removal)
- `src/pytest_bdd/plugin/code_generator/` — entrypoint.py, hook.py, plugin.py + supporting modules
- `src/pytest_bdd/plugin/cucumber_json/` — entrypoint.py, hook.py, plugin.py, model.py
- `src/pytest_bdd/plugin/cucumber_json_formatter/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/cucumber_junit/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/cucumber_pretty/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/cucumber_progress/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/cucumber_progress_bar/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/cucumber_snippets/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/cucumber_summary/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/cucumber_usage/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/cucumber_usage_json/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/gherkin_message_reporter/` — entrypoint.py, hook.py, plugin.py + 20 supporting modules
- `src/pytest_bdd/plugin/gherkin_terminal_reporter/` — entrypoint.py, hook.py, plugin.py, exception.py
- `src/pytest_bdd/plugin/pickle_runner/` — entrypoint.py, hook.py, plugin.py, run_transitions.py, api_compatibility.py
- `src/pytest_bdd/plugin/scenario_reporter/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/scenario_test_collector/` — entrypoint.py, hook.py, plugin.py
- `src/pytest_bdd/plugin/struct_bdd/` — entrypoint.py, hook.py, plugin.py, model.py, model_builder.py, parser.py
- `src/pytest_bdd/plugin/cucumber_formatter_support/` — EMPTY, remove
- `src/pytest_bdd/plugin/scenario_runner/` — EMPTY, remove

### Source Code — StashBound Subclasses
- `src/pytest_bdd/model/scenario_run.py` — `Run` (StashBound subclass, session-scoped runtime)
- `src/pytest_bdd/collector_batch.py` — `FeatureBatchParser` (StashBound subclass)
- `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py` — `_ReporterStateEntry` (StashBound subclass)
- `src/pytest_bdd/model/message_transport.py` — `ReportingEventSenderBinding` (StashBound subclass)
- `src/pytest_bdd/model/message_registry.py` — `EnvelopeRegistry` (StashBound subclass)

### Source Code — Stash Access Pattern
- `src/pytest_bdd/model/stash_access.py` — `StashBound` base class, `StashAccess` static methods
- `src/pytest_bdd/types/exception.py` — Stash exception classes (PytestBDDStashLookupError, etc.)

### Source Code — Hook Infrastructure
- `src/pytest_bdd/hook.py` — decopatch-based decorator infrastructure for `@given`, `@when`, `@then`, `@before_mark`, `@after_mark`, `@around_mark`

### Source Code — Entry Points
- `pyproject.toml` — `[project.entry-points.pytest11]` section (lines 86-104), 17 plugin registrations

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `model/stash_access.py` — `StashBound` base class with `from_stash()`, `initialize_in_stash()`, `find_in_stash()` patterns
- All 17 active plugins — already follow canonical `entrypoint.py + hook.py + plugin.py` structure
- `types/exception.py` — Stash exception hierarchy for stash access errors

### Established Patterns
- Plugin structure: `entrypoint.py` (pytest hooks), `hook.py` (hook specs), `plugin.py` (plugin class)
- Intra-plugin imports allowed within same package (e.g., `gherkin_message_reporter` internal modules)
- Cross-plugin communication exclusively via pytest hook system
- `attrs` (`@define`, `@frozen`) for all data classes — no `@dataclass` instances
- `from __future__ import annotations` in all 86 source files
- StashBound pattern: classvar `STASH_KEY`, classmethods for stash access

### Integration Points
- Lint gate → pre-commit hooks configuration in `pyproject.toml`
- Plugin validation → ruff custom rules or pre-commit script
- Empty directory removal → update pyproject.toml entry points if referenced (none found)

</code_context>

<specifics>
## Specific Ideas

- Lint gate could be a pre-commit script that scans plugin directories for required files and forbidden import patterns
- `gherkin_message_reporter` has 20+ supporting modules — most complex plugin, but structure is consistent
- `cucumber_formatter_support` and `scenario_runner` have no pyproject.toml entry points — safe to delete without config changes
- Decopatch: last release 1.4.10 (2022-03-01), last commit 2024-06-01, open PR from Feb 2026 (pkg_resources fix), 25 stars — stable but low-activity

</specifics>

<deferred>
## Deferred Ideas

- Decopatch replacement evaluation → Phase 11 (Audit & Prune)
- Dead code audit for underused plugin/utility modules → Phase 11

</deferred>

---

*Phase: 10-Pattern Unification*
*Context gathered: 2026-05-16*
