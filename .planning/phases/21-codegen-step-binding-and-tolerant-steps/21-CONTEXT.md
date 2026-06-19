# Phase 21: codegen-step-binding-and-tolerant-steps - Context

**Gathered:** 2026-06-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the codegen, feature binding, missing-step discovery, mock-run, WIP step, and tolerant step workflow described by `docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md`.

This phase delivers a CLI-driven authoring loop: bind a feature file to a target pytest file, gather missing bindings and step definitions, generate missing step skeletons, validate target-file rewrites, and support runtime modes for mock runs, WIP/not-implemented steps, and tolerant step failures.

</domain>

<decisions>
## Implementation Decisions

### CLI Shape
- **D-01:** New spec flags replace the old codegen flags. Phase 21 may remove/replace `--generate`, `--generate-missing`, and `--feature` in favor of the spec flags.
- **D-02:** `--gather-missing-steps` emits NDJSON output: one JSON object per missing scenario binding or missing step-definition event.
- **D-03:** `--bind-feature` is idempotent. If the target file already contains an equivalent `scenarios(...)` binding for the same feature, the command must leave the file unchanged.

### File Rewriting
- **D-04:** Target-file edits must use AST-aware rewriting for imports and existing binding/decorator detection.
- **D-05:** Generated missing-step skeletons raise `NotImplementedError`.
- **D-06:** Generated missing-step skeleton functions use `_` as the function name. Function names are not important and must not be gathered as user-facing data.
- **D-07:** Formatting or syntax failure rolls target-file changes back by default and fails the command.
- **D-08:** `--keep-generated-on-error` keeps the edited/generated target file on formatting or syntax failure, but the command still fails.

### Runtime And Reporting
- **D-09:** `--mock-run` verifies collection and binding only, then skips scenario execution lifecycle. It must not run step hooks or step function bodies.
- **D-10:** `@not_implemented` supports both decorator orders relative to `@given`, `@when`, `@then`, or `@step`.
- **D-11:** When a tolerant step raises and tolerant status resolves to `ignored`, the step remains failed at step-report level while the scenario may pass.
- **D-12:** Status override priority is pytest marker > Gherkin tag > CLI option > default. First priority wins silently; lower-priority conflicts do not warn or error.

### the agent's Discretion
- Decide internal module boundaries, helper types, and tests that best fit existing plugin, runner, and code-generation patterns.
- Decide exact NDJSON event field names, as long as the format is deterministic, machine-readable, and covers missing scenario bindings and missing step definitions.
- Decide whether old flag removal needs migration/deprecation tests, while honoring D-01 that new spec flags replace old codegen flags.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Specification
- `docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md` — Defines the CLI flags, decorators, status priorities, file rewrite behavior, and runtime lifecycle requested for this phase.

### Existing Architecture And Patterns
- `.planning/codebase/ARCHITECTURE.md` — Describes plugin architecture, scenario collection, step execution lifecycle, StashBound state, and code generator integration points.
- `.planning/codebase/CONVENTIONS.md` — Defines source style, attrs preference, exception handling, public API docstrings, and ruff formatting conventions.
- `.planning/codebase/STACK.md` — Defines runtime dependencies, pytest plugin entry points, formatter/reporting stack, and supported Python/pytest matrix.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/pytest_bdd/plugin/code_generator/entrypoint.py` currently owns codegen CLI option registration and routes to `CodeGeneratorPlugin`.
- `src/pytest_bdd/plugin/code_generator/plugin.py` already collects missing code via pytest collection, reports missing scenario bindings and missing step definitions, and exits with status `100` when missing artifacts exist.
- `src/pytest_bdd/plugin/code_generator/rendering.py` already renders step code with Jinja2 and formats generated Python through `ruff`.
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` owns scenario dispatch, step matching, step caller selection, step error handling, and target fixture injection.
- `src/pytest_bdd/scenario.py` provides the public `scenarios()` binding API that `--bind-feature` should append to target files.

### Established Patterns
- CLI behavior belongs in pytest plugin entrypoints and plugin classes, not top-level scripts.
- Scenario execution uses hook-based extension points; `pytest_bdd_get_step_caller` is the existing hook for replacing the step function call.
- Runtime state should flow through `Run`, `ScenarioRun`, and existing model objects instead of global mutable context.
- Source formatting uses `ruff format`; source code must stay Python 3.10-3.14 compatible and follow current ruff rules.

### Integration Points
- Codegen CLI replacement connects to `src/pytest_bdd/plugin/code_generator/entrypoint.py`.
- Missing binding and missing step discovery connects to existing codegen collection helpers.
- Target-file rewriting connects to generated code rendering plus new AST-aware import/binding/decorator handling.
- Mock-run and tolerant/WIP behavior connect to `src/pytest_bdd/plugin/pickle_runner/plugin.py` step dispatch and error handling.
- Public decorators connect to `src/pytest_bdd/__init__.py` exports and `src/pytest_bdd/steps.py` step definition registration.

</code_context>

<specifics>
## Specific Ideas

- `--keep-generated-on-error` is the explicit escape hatch for inspecting broken/generated target files.
- Generated step skeletons intentionally use `_` because function names are not meaningful user data in this workflow.
- `--mock-run` is narrower than the design spec's initial hook-body skip: the locked decision is collection/binding verification only, with no step lifecycle execution.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 20-codegen-step-binding-and-tolerant-steps*
*Context gathered: 2026-06-03*
