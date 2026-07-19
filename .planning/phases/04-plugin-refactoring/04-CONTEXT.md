# Phase 4: Plugin Refactoring - Context

**Gathered:** 2026-05-13T09:02:47Z
**Status:** Ready for planning

<domain>
## Phase Boundary

Normalize pytest-bdd plugin structure and reduce oversized reporting/validation modules without changing formatter behavior. Phase scope is fixed by ROADMAP.md: all 17 pytest plugins move toward the canonical class + entrypoint + hook.py pattern, `code_generator` gets a `CodeGeneratorPlugin` class, `live_formatter_runtime.py` and `message_validation.py` drop below 400 lines, and plugin-to-plugin coupling is removed.

</domain>

<decisions>
## Implementation Decisions

## Large-file split boundary
- **D-01:** Split large files into responsibility modules, not minimal helper dumps.
- **D-02:** Split `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py` by transport/process/session/render responsibilities.
- **D-03:** Split `src/pytest_bdd/model/message_validation.py` into schema/load, protobuf mapping, validation API, and error-formatting responsibilities.
- **D-04:** Do not keep compatibility shims for old private module paths. Update internal imports to owning modules, matching the Phase 3 direct-import decision.
- **D-05:** Do not expand Phase 4 to `src/pytest_bdd/steps.py` unless planning proves it is necessary for the selected plugin/refactor goals.

## Cross-plugin boundary rule
- **D-06:** Enforce a hard rule: remove all direct imports of another plugin's internals from plugin code.
- **D-07:** Cross-plugin communication may use pytest hooks plus typed service objects in `src/pytest_bdd/model/`.
- **D-08:** Keep service objects narrow and stable: formatter events, validation results, and codegen requests only. Do not create a broad service layer.
- **D-09:** External imports of plugin internals are not supported compatibility surface. Treat plugin internals as private; add a changelog note rather than aliases or deprecation shims.

## Verification gate
- **D-10:** Fix the Phase 3 full-suite environment blockers before doing Phase 4 refactor work. Phase 4 cannot close on documented blockers alone.
- **D-11:** Add golden before/after formatter-output checks for affected formatters.
- **D-12:** Add a source contract test proving every `pytest11` plugin has class + entrypoint + hook module structure.
- **D-13:** Add a test or script that blocks plugin-internal imports from plugin code.

## the agent's Discretion
No explicit agent-discretion decisions were selected. Planner should use existing repository patterns and roadmap success criteria where this context is silent.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

## Scope and requirements
- `.planning/ROADMAP.md` — Phase 4 goal, dependencies, requirements, and success criteria.
- `.planning/PROJECT.md` — project constraints, core value, and active requirements.
- `.planning/REQUIREMENTS.md` — REF-02 and REF-03 definitions, plus out-of-scope constraints.
- `.planning/STATE.md` — current workflow state and Phase 3 blocker carry-forward.

## Prior phase decisions
- `.planning/phases/01-foundation-cleanup/01-CONTEXT.md` — deletion/cleanup precedent and plugin-entrypoint cleanup patterns.
- `.planning/phases/02-code-quality-gates/02-CONTEXT.md` — return-value, exception, lint, `attrs`, and quality-gate conventions.
- `.planning/phases/03-core-runtime-refactor/03-CONTEXT.md` — direct owning-module import rule, no compatibility shims, characterization-first refactor pattern.
- `.planning/phases/03-core-runtime-refactor/03-03-SUMMARY.md` — exact full-suite, xdist, and pre-commit environment blockers that Phase 4 must address first.

## Codebase maps
- `.planning/codebase/ARCHITECTURE.md` — plugin architecture, pytest hook integration, stash-backed runtime state.
- `.planning/codebase/CONVENTIONS.md` — class-based plugin conventions, file style, typing, and formatting rules.
- `.planning/codebase/STRUCTURE.md` — plugin directory layout and existing module inventory.

</canonical_refs>

<code_context>
## Existing Code Insights

## Reusable Assets
- `src/pytest_bdd/plugin/gherkin_message_reporter/` already has service-style runtime modules (`transport_runtime.py`, `lifecycle_runtime.py`, `scenario_runtime.py`, `step_catalog_runtime.py`) that should guide the `live_formatter_runtime.py` split.
- `src/pytest_bdd/plugin/code_generator/entrypoint.py` and `plugin.py` exist, but `plugin.py` is large and needs a canonical `CodeGeneratorPlugin` class shape.
- Existing `hook.py` modules in `pickle_runner`, `scenario_test_collector`, and `gherkin_message_reporter` are the nearest local examples for plugin hook contracts.

## Established Patterns
- Phase 3 established direct imports from owning modules and rejected compatibility re-export shims.
- Phase 2 established `attrs` over dataclasses, explicit return values outside hooks, and quality gates around broad exceptions.
- Class-based plugins generally live in package directories with `entrypoint.py`, `plugin.py`, and optional `hook.py`; single-file formatter modules are the structure outliers.

## Integration Points
- `pyproject.toml` `[project.entry-points.pytest11]` defines the plugin registry that source contract tests should inspect.
- Formatter bridge modules currently import `pytest_bdd.plugin.gherkin_message_reporter.session` from multiple formatter plugins; these imports are key boundary-refactor targets.
- Current direct plugin imports appear in formatter support, reporter plugins, collector plugins, and core modules. The Phase 4 boundary rule applies to plugin-to-plugin imports; core-module imports should be reviewed separately before moving stable contracts to `model/`.

</code_context>

<specifics>
## Specific Ideas

- Use responsibility-oriented modules instead of cosmetic line-count moves.
- Preserve formatter output exactly through golden before/after checks.
- Keep new service objects narrow and domain-stable.
- Resolve local verification environment first so Phase 4 can finish with a real full-suite gate.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 4-Plugin Refactoring*
*Context gathered: 2026-05-13T09:02:47Z*
