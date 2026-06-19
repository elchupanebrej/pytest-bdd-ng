# Phase 21: Codegen, Step Binding, and Tolerant Steps - Research

**Researched:** 2026-06-03
**Domain:** pytest plugin CLI/code generation, AST-aware Python test-file rewriting, BDD step runtime status handling
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
None - discussion stayed within phase scope.
</user_constraints>

## Project Constraints (from AGENTS.md)

- Prefix shell commands with `rtk`. [VERIFIED: AGENTS.md]
- Development guidelines live in `DEVELOPMENT.rst`; do not duplicate guideline content into AGENTS.md. [VERIFIED: AGENTS.md]
- Runtime supports Python 3.10-3.14. [VERIFIED: AGENTS.md]
- Core stack includes `pytest>=7`, `pluggy`, `tox>=4.2`, `pre-commit`, `ruff`, `mypy`, and `packaging`. [VERIFIED: AGENTS.md]
- Runtime state should use canonical `pytest.config.stash`-backed model objects where applicable. [VERIFIED: AGENTS.md]
- Follow repository linting/formatting through `ruff` and pre-commit hooks. [VERIFIED: AGENTS.md]
- Documentation, specification, and planning artifacts must be written in English. [VERIFIED: AGENTS.md]
- Outside pytest hook implementations, returning `None` is an antipattern; use explicit values or deterministic exceptions. [VERIFIED: AGENTS.md]
- Use `attrs` instead of builtin `dataclass` for new data holders. [VERIFIED: AGENTS.md]
- New feature development must include executable ATDD/BDD coverage under `features/`. [VERIFIED: AGENTS.md]

## Summary

Phase 21 should extend the existing pytest plugin architecture instead of adding standalone scripts. Current code generation is already a class-based pytest plugin that wraps collection through `wrap_session`, gathers unbound scenarios and unmatched steps, renders Jinja2 code, and formats generated Python with `ruff`. [VERIFIED: codebase grep] The existing CLI is legacy (`--generate`, `--generate-missing`, `--feature`) and prints human-oriented terminal output, so Phase 21 should replace that surface with spec flags, NDJSON events, and target-file rewriting. [VERIFIED: codebase grep]

The main architectural risk is mock-run placement. The design spec suggests `pytest_bdd_get_step_caller`, but the locked context narrows `--mock-run` to collection/binding verification only and explicitly forbids step hooks and step bodies. [CITED: docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md] In current runner flow, `pytest_bdd_get_step_caller` is invoked after `pytest_bdd_before_step` and `pytest_bdd_before_step_call`, so it is too late for D-09. [VERIFIED: codebase grep] Implement mock-run in `pytest_runtest_call` or `pytest_bdd_run_scenario` before invoking scenario/step lifecycle hooks. [VERIFIED: codebase grep]

**Primary recommendation:** Implement a focused `code_generator.rewrite` module using stdlib `ast` for detection plus controlled text insertion, add explicit `not_implemented` and `tolerant` fields to `Definition`, and implement runtime status policy in `PickleRunner` before/around step-call error handling. [VERIFIED: codebase grep]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| CLI flag registration and dispatch | pytest plugin entrypoint | CodeGeneratorPlugin | Options already live in `plugin/code_generator/entrypoint.py`, with command dispatch delegated to `CodeGeneratorPlugin`. [VERIFIED: codebase grep] |
| Missing binding/step discovery | Code generator plugin | Scenario collection/runtime model | Existing discovery uses pytest collection, `Run.ensure_feature_binding`, and step matching without executing step bodies. [VERIFIED: codebase grep] |
| Target-file binding and generation | Code generator plugin | Rendering/rewrite helpers | File edits belong beside codegen rendering; public `scenarios()` remains the runtime binding API. [VERIFIED: codebase grep] |
| Mock-run lifecycle | Pickle runner plugin | Scenario collection | Current runner owns `pytest_runtest_call`, scenario hooks, step dispatch, and step calls. [VERIFIED: codebase grep] |
| WIP/not-implemented status | Step definition layer + Pickle runner | Public API lazy exports | Step decorators create `Definition` objects, and runner controls call/skip/fail behavior. [VERIFIED: codebase grep] |
| Tolerant step reporting | Pickle runner + reporters | ScenarioRun/StepRun | Runner detects step errors; scenario reporter and message reporter finalize step-level failed reports from `pytest_bdd_step_error`. [VERIFIED: codebase grep] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `ast` | Python 3.10-3.14 runtime | Parse target files, detect imports, `scenarios(...)` calls, and decorator presence. | No new dependency needed; project already requires Python 3.10-3.14. [VERIFIED: AGENTS.md] |
| `pytest` | `>=7.0.0` | Plugin host, CLI options, collection, testdir integration. | Project is a pytest plugin and uses pytest11 entry points. [VERIFIED: .planning/codebase/STACK.md] |
| `attrs` | existing dependency | New policy/result data holders. | Project convention requires `attrs` over builtin dataclasses. [VERIFIED: AGENTS.md] |
| `Jinja2` | existing dependency | Render generated step snippets. | Existing codegen uses Jinja2 template rendering. [VERIFIED: codebase grep] |
| `ruff` | existing dependency | Format/validate edited target files. | Existing rendering uses `ruff`; repository formatting standard is `ruff format`. [VERIFIED: codebase grep] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `json` stdlib | Python 3.10-3.14 runtime | Emit deterministic NDJSON events. | Use for `--gather-missing-steps`. [VERIFIED: docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md] |
| `pathlib` stdlib | Python 3.10-3.14 runtime | Normalize target and feature paths. | Use for feature path binding and relative path rendering. [VERIFIED: codebase grep] |
| pytest `testdir`/`pytester` | configured plugin | Integration tests for CLI/file rewrite behavior. | Existing generation tests use `testdir.runpytest`. [VERIFIED: codebase grep] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `ast` detection plus controlled insertion | LibCST/parso/redbaron | External dependency not needed; no locked decision allows adding parser dependency. [ASSUMED] |
| Updating old Jinja2 full-file template only | Rewrite helper module | Template-only cannot idempotently inspect existing imports/bindings/decorators. [VERIFIED: codebase grep] |
| Mocking `pytest_bdd_get_step_caller` | Early return in runner | Step caller is too late to satisfy "no step hooks" because hooks already fired. [VERIFIED: codebase grep] |

**Installation:** No new external packages. [VERIFIED: codebase grep]

## Package Legitimacy Audit

No external packages are recommended or installed for Phase 21. [VERIFIED: codebase grep]

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| None | N/A | N/A | N/A | N/A | N/A | No install |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
pytest CLI
  |
  +--> code_generator.entrypoint registers spec flags
        |
        +--> CodeGeneratorPlugin dispatch
              |
              +--> bind-feature path
              |     --> parse target with ast
              |     --> detect pytest_bdd.scenarios import and existing scenarios(feature)
              |     --> insert import/binding if missing
              |     --> write temp/backup guarded edit
              |     --> ruff format + ast.parse validation
              |     --> commit file or rollback
              |
              +--> gather-missing/generate-missing path
                    --> wrap_session collection
                    --> collect scenario bindings from session.items
                    --> locate feature pickles from requested feature(s)
                    --> match steps through existing matcher
                    --> emit NDJSON events
                    --> optionally render skeletons
                    --> AST-aware import/decorator detection
                    --> append generated @not_implemented step skeletons

pytest scenario execution
  |
  +--> PickleRunner.pytest_runtest_call
        |
        +--> if mock_run: resolve fixtures/collection/binding, skip scenario and step hooks, return
        |
        +--> normal scenario lifecycle
              --> before_scenario
              --> run_scenario
                    --> run_step
                          --> match Definition
                          --> inspect Definition.not_implemented / tolerant
                          --> resolve status: pytest mark > Gherkin tag > CLI > default
                          --> call / skip / fail / collect tolerant exception
              --> after_scenario
```

### Recommended Project Structure

```text
src/pytest_bdd/plugin/code_generator/
├── entrypoint.py      # CLI option registration and plugin delegation
├── plugin.py          # command orchestration, wrap_session callbacks
├── collection.py      # missing scenario/step discovery
├── rendering.py       # snippet rendering and ruff formatting
├── rewrite.py         # AST-aware import/binding/decorator detection and guarded writes
└── events.py          # attrs event models + NDJSON serialization

src/pytest_bdd/steps/
├── decorators.py      # public step decorators plus not_implemented/tolerant wrappers
├── definition.py      # Definition fields for not_implemented/tolerant
└── manager.py         # decorator_builder applies pending function policy flags

src/pytest_bdd/plugin/pickle_runner/
├── entrypoint.py      # add --mock-run, --wip-status, --tolerant-status options
├── plugin.py          # early mock-run and status-aware step call/error behavior
└── status_policy.py   # attrs helpers for priority resolution
```

### Pattern 1: AST-Aware Rewrite With Guarded Write

**What:** Use `ast.parse()` to detect import aliases, existing `scenarios(...)` calls, and existing step decorators; use small text insertions at module boundaries rather than raw global string replacement. [VERIFIED: codebase grep]

**When to use:** `--bind-feature` and `--generate-missing-steps` target-file edits. [VERIFIED: docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md]

**Example:**

```python
# Source: stdlib ast + existing repository pattern
module = ast.parse(source, filename=str(target_file))
has_scenarios_import = any(
    isinstance(node, ast.ImportFrom)
    and node.module == "pytest_bdd"
    and any(alias.name == "scenarios" for alias in node.names)
    for node in module.body
)
```

### Pattern 2: Decorator Order Independence Through Function Policy Flags

**What:** `@not_implemented` and `@tolerant` should set a marker on the function and update any already-created `Definition` objects attached to `__pytest_bdd_step_definitions__`. [VERIFIED: codebase grep]

**When to use:** Public decorators must work both above and below `@given`/`@when`/`@then`/`@step`. [VERIFIED: docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md]

**Example:**

```python
# Source: current Definition attachment pattern in steps/manager.py
def not_implemented(step_func: StepFunc) -> StepFunc:
    setattr(step_func, "__pytest_bdd_not_implemented__", True)
    for definition in getattr(step_func, "__pytest_bdd_step_definitions__", ()):
        definition.not_implemented = True
    return step_func
```

### Pattern 3: Status Resolution Helper

**What:** Centralize priority logic in a small helper, returning `passed|skipped|failed` for WIP and `failed|ignored` for tolerant. [VERIFIED: docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md]

**When to use:** Before deciding WIP behavior and after collecting tolerant soft failures. [VERIFIED: codebase grep]

**Example:**

```python
# Source: status priority from phase context
def resolve_wip_status(item, pickle, cli_value: str, default: str = "failed") -> str:
    mark = next(item.iter_markers(name="wip_status"), None)
    if mark and mark.args:
        return str(mark.args[0])
    tag_status = _status_from_pickle_tags(pickle.tags, prefix="wip-status-")
    if tag_status is not None:
        return tag_status
    return cli_value or default
```

### Anti-Patterns to Avoid

- **Implementing mock-run in `pytest_bdd_get_step_caller`:** Too late; current runner has already fired step hooks before this hook. [VERIFIED: codebase grep]
- **String-only file rewriting:** Cannot reliably detect alias imports, duplicate `scenarios(...)` calls, or decorator order. [ASSUMED]
- **Generating user-facing function names from step text:** Locked decision says skeleton functions use `_`, and function names are not user-facing data. [VERIFIED: CONTEXT.md]
- **Reporting tolerant ignored as a passed step:** Locked decision requires step-report level failure while scenario may pass. [VERIFIED: CONTEXT.md]
- **Warning on conflicting status sources:** Locked decision says first priority wins silently. [VERIFIED: CONTEXT.md]

## Current Codegen And Missing-Step Behavior

| Area | Current Behavior | Phase 21 Change |
|------|------------------|-----------------|
| CLI | `--generate`, `--generate-missing`, `--feature`; `--feature` is required for both generation modes. [VERIFIED: codebase grep] | Replace/remove old flags with spec flags: `--bind-feature`, `--target-file`, `--gather-missing-steps`, `--generate-missing-steps`. [VERIFIED: CONTEXT.md] |
| Missing scenario binding | Runs collection, compares collected `(feature_uri, pickle.name)` with located feature pickles, prints human text. [VERIFIED: codebase grep] | Emit one NDJSON event per missing scenario binding. [VERIFIED: CONTEXT.md] |
| Missing step definitions | Sets up each collected item, creates a `ScenarioRun`, calls `pytest_bdd_match_step_definition_to_step`, collects matcher misses. [VERIFIED: codebase grep] | Reuse matching path, serialize deterministic missing-step events, optionally append skeletons. [VERIFIED: codebase grep] |
| Step skeleton rendering | Jinja2 template generates `def {python_name_from_step_text}(): raise NotImplementedError`. [VERIFIED: codebase grep] | Generate `@not_implemented` plus step decorator, `def _(): raise NotImplementedError`. [VERIFIED: CONTEXT.md] |
| Formatting | `rendering._format_code()` uses `ruff` best-effort and returns unformatted code on formatter failure. [VERIFIED: codebase grep] | Target-file writes must fail and roll back on syntax/formatting failure unless `--keep-generated-on-error`. [VERIFIED: CONTEXT.md] |
| Existing tests | Integration tests assert old terminal text and old flags; E2E codegen feature uses old flags and permissive checks. [VERIFIED: codebase grep] | Update/add tests for new flags, NDJSON, idempotent edits, rollback, `_`, and `@not_implemented`. [VERIFIED: AGENTS.md] |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Python syntax parsing | Regex parser for imports/decorators | stdlib `ast.parse` | Needed for robust import, call, and decorator detection. [ASSUMED] |
| Python formatting | Custom formatter/string normalization | Existing `ruff format` path | Repository already standardizes on `ruff format`. [VERIFIED: .planning/codebase/CONVENTIONS.md] |
| Scenario/step discovery | Separate Gherkin scanner disconnected from pytest | Existing collection + matcher helpers | Existing helpers already account for pytest fixtures, registries, and parser matching. [VERIFIED: codebase grep] |
| Status priority | Scattered checks in runner branches | Central status policy helper | Avoids inconsistent WIP/tolerant priority behavior. [ASSUMED] |
| Step report mutation | Direct reporter internals per formatter | Existing BDD hooks and `StepRun.status` | Existing reporters listen to `pytest_bdd_after_step`/`pytest_bdd_step_error`. [VERIFIED: codebase grep] |

**Key insight:** Use existing pytest collection and step matching for truth, then add machine-readable serialization and guarded rewrite around that result. [VERIFIED: codebase grep]

## Common Pitfalls

### Pitfall 1: Mock-Run Hook Placement
**What goes wrong:** `--mock-run` implemented through `pytest_bdd_get_step_caller` still fires step lifecycle hooks. [VERIFIED: codebase grep]
**Why it happens:** Current `_run_step_call()` invokes `pytest_bdd_before_step_call` before requesting a caller, and `_run_step_body()` invokes `pytest_bdd_before_step` before that. [VERIFIED: codebase grep]
**How to avoid:** Branch before `pytest_bdd_before_scenario` in `pytest_runtest_call`, or replace `pytest_bdd_run_scenario` with a collection/binding-only path that does not invoke step hooks. [VERIFIED: codebase grep]
**Warning signs:** Tests record calls to `pytest_bdd_before_step`, `pytest_bdd_before_step_call`, or `pytest_bdd_after_step` during `--mock-run`. [VERIFIED: codebase grep]

### Pitfall 2: Decorator Order Does Not Propagate
**What goes wrong:** `@not_implemented` works only when placed inside or outside step decorators, not both. [ASSUMED]
**Why it happens:** Step decorators immediately create `Definition` objects and attach them to the function. [VERIFIED: codebase grep]
**How to avoid:** Store function-level pending flags and update attached definitions in both public decorators and `decorator_builder`. [VERIFIED: codebase grep]
**Warning signs:** Two tests with reversed decorator order produce different `Definition.not_implemented` values. [ASSUMED]

### Pitfall 3: Tolerant Ignored Loses Failed Step Evidence
**What goes wrong:** Scenario passes but reports show the tolerant step as passed. [VERIFIED: CONTEXT.md]
**Why it happens:** Existing success path finalizes steps through `pytest_bdd_after_step`; failure path finalizes through `pytest_bdd_step_error`. [VERIFIED: codebase grep]
**How to avoid:** For tolerant exceptions, mark `StepRun.status = failed`, call `pytest_bdd_step_error` to let reporters emit failed step records, suppress only final scenario failure when resolved status is `ignored`. [VERIFIED: codebase grep]
**Warning signs:** Cucumber message `TestStepResult` for tolerant ignored failure is `passed`. [VERIFIED: codebase grep]

### Pitfall 4: Rollback Leaves Partial Target File
**What goes wrong:** Syntax or formatter failure leaves broken generated code in the target file. [VERIFIED: CONTEXT.md]
**Why it happens:** Existing rendering formatter is best-effort and not file-transactional. [VERIFIED: codebase grep]
**How to avoid:** Read original content, compute new content, write, run `ruff format <target>`, run `ast.parse`, and restore original content on failure unless `--keep-generated-on-error`. [VERIFIED: CONTEXT.md]
**Warning signs:** A failing command changes target file content without `--keep-generated-on-error`. [VERIFIED: CONTEXT.md]

## Code Examples

### Missing Event Shape

```python
# Source: phase discretion; deterministic NDJSON fields recommended for planner
{"type": "missing_scenario_binding", "feature": "features/example.feature", "scenario": "Checkout", "line": 12}
{
    "type": "missing_step_definition",
    "feature": "features/example.feature",
    "scenario": "Checkout",
    "keyword": "Then",
    "text": "receipt is shown",
    "line": 18,
}
```

### Generated Skeleton

```python
# Source: CONTEXT.md D-05/D-06 plus design spec decorator
from pytest_bdd import not_implemented, then


@then("receipt is shown")
@not_implemented
def _():
    raise NotImplementedError
```

### Binding Append

```python
# Source: public scenarios() API in src/pytest_bdd/scenario.py
from pytest_bdd import scenarios


scenarios("../features/example.feature")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Full generated test module printed to stdout through `--generate`. [VERIFIED: codebase grep] | Target-file binding and missing skeleton appends through spec flags. [VERIFIED: CONTEXT.md] | Phase 21 planned 2026-06-03. [VERIFIED: CONTEXT.md] | Planner should replace old CLI tests instead of preserving old behavior unless compatibility is explicitly chosen. |
| Human terminal missing-step diagnostics. [VERIFIED: codebase grep] | NDJSON event stream for missing binding/step events. [VERIFIED: CONTEXT.md] | Phase 21 planned 2026-06-03. [VERIFIED: CONTEXT.md] | Tests should parse stdout as JSON lines, not fnmatch terminal text. |
| Step body mock via `pytest_bdd_get_step_caller`. [CITED: docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md] | Collection/binding-only mock-run that skips scenario and step lifecycle. [VERIFIED: CONTEXT.md] | Context locked after spec. [VERIFIED: CONTEXT.md] | Implement stricter context decision over spec snippet. |

**Deprecated/outdated:**
- `--generate`, `--generate-missing`, and `--feature`: Phase context allows replacing/removing them with new spec flags. [VERIFIED: CONTEXT.md]
- `src/pytest_bdd/steps.py` path in phase prompt: current codebase has `src/pytest_bdd/steps/` package files. [VERIFIED: codebase grep]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Runtime/tests | yes | 3.12.7 | Use project tox/uv to provision target versions. [VERIFIED: command probe] |
| uv | Makefile/tox workflow | yes | 0.11.16 | pip/tox direct commands, but project Makefile prefers uv. [VERIFIED: command probe] |
| ruff | Formatting target files | yes | 0.14.10 | Use installed project dependency in tox env if global ruff differs. [VERIFIED: command probe] |
| graphify | Optional graph context | no | disabled | Continue with codebase grep/docs. [VERIFIED: command probe] |

**Missing dependencies with no fallback:** none. [VERIFIED: command probe]
**Missing dependencies with fallback:** graphify disabled; grep/docs covered required research. [VERIFIED: command probe]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest via repository tox/Makefile. [VERIFIED: pyproject.toml] |
| Config file | `pyproject.toml` pytest ini options and markers. [VERIFIED: pyproject.toml] |
| Quick run command | `rtk python -m pytest tests/cases/integration/generation -m integration -q` [VERIFIED: codebase grep] |
| Full suite command | `rtk make test-unit && rtk make test-integration && rtk make test-e2e` [VERIFIED: Makefile] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| P20-CLI | New flags replace old codegen flags and validate required option combinations. | integration | `rtk python -m pytest tests/cases/integration/generation -m integration -q` | Existing dir; new tests needed. [VERIFIED: codebase grep] |
| P20-NDJSON | `--gather-missing-steps` emits one JSON object per missing binding/step. | integration + e2e | `rtk python -m pytest tests/cases/integration/generation -m integration -q` | New tests needed. [VERIFIED: CONTEXT.md] |
| P20-BIND | `--bind-feature --target-file` appends idempotent `scenarios(...)` binding and import. | integration | `rtk python -m pytest tests/cases/integration/generation -m integration -q` | New tests needed. [VERIFIED: CONTEXT.md] |
| P20-GENERATE | `--generate-missing-steps` appends `_` skeletons with `@not_implemented`. | integration + e2e | `rtk python -m pytest tests/cases/integration/generation -m integration -q` | Existing tests need update. [VERIFIED: codebase grep] |
| P20-ROLLBACK | Formatting/syntax failure rolls back unless `--keep-generated-on-error`. | integration | `rtk python -m pytest tests/cases/integration/generation -m integration -q` | New tests needed. [VERIFIED: CONTEXT.md] |
| P20-MOCK | `--mock-run` verifies collection/binding and skips scenario/step hooks and bodies. | integration | `rtk python -m pytest tests/cases/integration/feature -m integration -q -k mock_run` | New tests needed. [VERIFIED: CONTEXT.md] |
| P20-WIP | `@not_implemented` status honors pytest marker > Gherkin tag > CLI > default. | unit + integration | `rtk python -m pytest tests/cases/unit tests/cases/integration/feature -q -k 'not_implemented or wip_status'` | New tests needed. [VERIFIED: CONTEXT.md] |
| P20-TOLERANT | `@tolerant` ignored keeps step failed in reports while scenario can pass. | integration + messages/e2e | `rtk python -m pytest tests/cases/integration/feature tests/cases/integration/messages -q -k tolerant` | New tests needed. [VERIFIED: CONTEXT.md] |
| P20-ATDD | Executable feature docs cover user workflow. | e2e | `rtk python -m pytest tests/cases/e2e -m e2e -q -k code_generator` | Existing feature needs expansion. [VERIFIED: AGENTS.md] |

### Sampling Rate

- **Per task commit:** `rtk python -m pytest tests/cases/integration/generation tests/cases/integration/feature -q -k "generate or bind or mock_run or tolerant or not_implemented"` [ASSUMED]
- **Per wave merge:** `rtk make test-unit && rtk make test-integration && rtk make test-e2e` [VERIFIED: Makefile]
- **Phase gate:** Full relevant unit/integration/e2e slices green before `$gsd-verify-work`. [VERIFIED: .planning/config.json]

### Wave 0 Gaps

- [ ] `tests/cases/integration/generation/test_bind_feature.py` -- target-file binding, import insertion, idempotency, rollback. [ASSUMED]
- [ ] `tests/cases/integration/generation/test_gather_missing_steps.py` -- NDJSON event contract. [ASSUMED]
- [ ] `tests/cases/integration/feature/test_mock_run.py` -- hook/body suppression. [ASSUMED]
- [ ] `tests/cases/unit/unit/test_step_policy_decorators.py` -- decorator order and `Definition` flags. [ASSUMED]
- [ ] `tests/cases/integration/feature/test_wip_and_tolerant_steps.py` -- status priority and runtime behavior. [ASSUMED]
- [ ] `features/13 Code Generator/02 Step binding and tolerant steps.feature.md` plus `tests/cases/e2e/steps_code_generator.py` updates -- required ATDD/BDD coverage. [VERIFIED: AGENTS.md]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No auth surface in this phase. [VERIFIED: .planning/codebase/ARCHITECTURE.md] |
| V3 Session Management | no | No session/auth state in this phase. [VERIFIED: .planning/codebase/ARCHITECTURE.md] |
| V4 Access Control | no | Local CLI edits user-specified files; no server access control. [ASSUMED] |
| V5 Input Validation | yes | Validate CLI option combinations, target suffix, feature existence, path normalization, and parse target Python with `ast`. [VERIFIED: CONTEXT.md] |
| V6 Cryptography | no | No cryptography in this phase. [VERIFIED: docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md] |

### Known Threat Patterns for pytest CLI File Rewriting

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Accidental overwrite of unrelated file | Tampering | Require `--target-file`, validate suffix/path, transactional rollback. [VERIFIED: CONTEXT.md] |
| Broken generated Python committed after formatter failure | Tampering | Restore original content unless `--keep-generated-on-error`. [VERIFIED: CONTEXT.md] |
| Untrusted generated code execution | Elevation of privilege | Generation writes skeletons only; `--mock-run` must not execute step bodies. [VERIFIED: CONTEXT.md] |
| Ambiguous status override source | Repudiation | Deterministic priority and silent first-wins behavior. [VERIFIED: CONTEXT.md] |

## Sequencing Recommendations

1. Add characterization tests for current codegen discovery helpers before changing CLI output. [VERIFIED: codebase grep]
2. Build `events.py` NDJSON serialization and update gather command while still reusing current collection helpers. [VERIFIED: codebase grep]
3. Add `rewrite.py` with AST detection and transactional write, then implement `--bind-feature`. [VERIFIED: CONTEXT.md]
4. Update rendering to produce imports/decorators for `not_implemented` and `_` functions, then implement `--generate-missing-steps`. [VERIFIED: CONTEXT.md]
5. Add public decorators and `Definition` fields before runner behavior so tests can inspect metadata directly. [VERIFIED: codebase grep]
6. Implement `--mock-run` early in runner before scenario hooks. [VERIFIED: codebase grep]
7. Implement WIP/tolerant status policy and reporter-preserving tolerant failure handling last, because it touches runtime/reporting semantics. [VERIFIED: codebase grep]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Avoiding LibCST/parso/redbaron is preferable because stdlib `ast` plus controlled insertion is enough. | Standard Stack / Don't Hand-Roll | If formatting-preserving rewrites become complex, planner may need to revisit dependency decision. |
| A2 | String-only rewriting is too fragile for this phase. | Anti-Patterns | If target edits are deliberately minimal, this may overstate rewrite complexity. |
| A3 | Central status policy helper is preferable to inline checks. | Don't Hand-Roll / Architecture Patterns | If runtime change remains tiny, helper could be unnecessary abstraction. |
| A4 | Proposed new test filenames are appropriate. | Validation Architecture | Planner may choose different filenames matching local ownership. |
| A5 | Local CLI file rewrite access is not an ASVS access-control concern. | Security Domain | If project treats arbitrary target paths as security boundary, stricter path allowlisting may be needed. |

## Open Questions (RESOLVED)

1. **Should old codegen flags be removed outright or kept as deprecated aliases?**
   - What we know: Context D-01 says new spec flags replace old codegen flags and may remove/replace old flags. [VERIFIED: CONTEXT.md]
   - What's unclear: Whether compatibility aliases are desired for one release. [ASSUMED]
   - Recommendation: Planner should choose removal unless maintaining old tests is explicitly required. [ASSUMED]
   - RESOLVED: Phase 21 plans replace the old flags as the primary interface. Old flags may only remain as explicit compatibility aliases if implementation discovers a required migration need, and tests must assert they are not silently treated as the primary authoring workflow.

2. **Exact NDJSON field names**
   - What we know: Context gives discretion if deterministic and covers missing scenario bindings and missing step definitions. [VERIFIED: CONTEXT.md]
   - What's unclear: Whether downstream tooling already expects a schema. [ASSUMED]
   - Recommendation: Use `type`, `feature`, `scenario`, `keyword`, `text`, `line`, and `step_type` fields, then lock in tests. [ASSUMED]
   - RESOLVED: Phase 21 plans lock the schema through `events.py` and integration/E2E tests using deterministic fields for missing scenario bindings and missing step definitions. Implementers should use the recommended fields unless code inspection finds an existing internal field name that avoids duplication.

3. **Tolerant ignored report path**
   - What we know: Existing reporters mark failed steps through `pytest_bdd_step_error`; successful steps through `pytest_bdd_after_step`. [VERIFIED: codebase grep]
   - What's unclear: Whether calling `pytest_bdd_step_error` while suppressing final exception has secondary effects in all formatter plugins. [ASSUMED]
   - Recommendation: Add integration tests for scenario report and Cucumber message output, not only pytest outcome. [VERIFIED: codebase grep]
   - RESOLVED: Phase 21 plans require both runtime integration coverage and Cucumber/message reporter coverage so tolerant ignored behavior preserves failed step evidence while allowing scenario pass behavior.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/21-codegen-step-binding-and-tolerant-steps/21-CONTEXT.md` - locked decisions and discretion areas.
- `docs/superpowers/specs/2026-06-03-codegen-step-binding-design.md` - CLI, decorator, status, and lifecycle design.
- `AGENTS.md` - project constraints, stack, and ATDD/BDD requirement.
- `.planning/codebase/ARCHITECTURE.md` - plugin architecture and runtime flow.
- `.planning/codebase/CONVENTIONS.md` - formatting, `attrs`, error handling, and test patterns.
- `.planning/codebase/STACK.md` - dependency and pytest plugin stack.
- `src/pytest_bdd/plugin/code_generator/*` - current CLI, collection, rendering, and missing-step behavior.
- `src/pytest_bdd/plugin/pickle_runner/*` - scenario/step lifecycle and caller hook placement.
- `src/pytest_bdd/steps/*` - current step definition registration and package layout.
- `src/pytest_bdd/scenario.py` - public `scenarios()` binding API.
- `src/pytest_bdd/__init__.py` - public lazy exports.
- `tests/cases/integration/generation/*`, `tests/cases/e2e/steps_code_generator.py`, `features/13 Code Generator/01 Code generation.feature.md` - existing codegen coverage.
- `.planning/phases/18-split-xdist-remote-tests-into-separate-parallel-gha-executor/18-VERIFICATION.md` - Phase 19 verified with one human GitHub Actions check remaining.

### Secondary (MEDIUM confidence)
- Command probes for `python`, `uv`, `ruff`, and graphify availability.

### Tertiary (LOW confidence)
- Assumptions in the Assumptions Log; no unverified web-only claims used.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new packages; verified from project docs and code.
- Architecture: HIGH - verified from code generator, runner, scenario, and step package sources.
- Pitfalls: HIGH - mock-run placement and reporter paths verified from runner/reporter code.
- Test strategy: MEDIUM - existing infrastructure verified; exact new file split is recommended.

**Research date:** 2026-06-03
**Valid until:** 2026-07-03
