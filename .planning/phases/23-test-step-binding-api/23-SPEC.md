# Phase 23: Test/Step binding API - Specification

**Created:** 2026-06-05
**Ambiguity score:** 0.15 (gate: <= 0.20)
**Requirements:** 8 locked

## Goal

`--mock-run --messages-ndjson` becomes a reliable IDE bootstrap contract for launching exact pytest items and resolving exact feature-step-to-Python-step bindings without executing scenario hooks, step hooks, or step bodies.

## Background

Phase 19 introduced mock-run and code-generation flows. The current runtime already emits cucumber-messages such as `Source`, `GherkinDocument`, `Pickle`, `StepDefinition`, and `TestCase`; `StepDefinition` messages include `sourceReference`, and `TestCase.testSteps` can link matched pickle steps to step definition IDs. The current mock-run verifies step bindings without executing lifecycle code. Missing pieces for IDE integration are a stable launch mapping from each `Pickle`/Examples row to the exact pytest `nodeid`, framework-owned binding cardinality diagnostics for feature/scenario hookups, and richer scoped step binding diagnostics for missing and ambiguous steps.

## Requirements

1. **Mock-run message contract**: `--mock-run --messages-ndjson <path>` MUST be the supported dry-run synchronization command for IDE startup.
   - Current: `--mock-run` exists and message reporting exists, but their combined IDE-sync contract is not locked by a dedicated requirement.
   - Target: The combined command emits real collection/runtime message graph data needed by IDE indexing while still avoiding scenario hook, step hook, and step body execution.
   - Acceptance: An integration test runs `pytest --mock-run --messages-ndjson report.ndjson` and verifies `Source`, `GherkinDocument`, `Pickle`, `StepDefinition`, and `TestCase` payloads exist, while hook/body probe files are not created.

2. **Runnable launch mapping**: Framework MUST expose a reliable launch handle that maps each collected `Pickle` to the exact pytest `nodeid` that runs it.
   - Current: `Pickle` and `TestCase` messages identify Cucumber runtime objects, but no message contract exposes a pytest command target for `pytest <nodeid>`.
   - Target: IDE can resolve every runnable `Pickle` to a pytest `nodeid` from the message stream without re-collecting or guessing.
   - Acceptance: A test project with one bound scenario produces a message-stream mapping where the scenario `Pickle` resolves to the pytest item nodeid, and `pytest <nodeid>` runs exactly that item.

3. **Examples-row launch mapping**: Scenario Outline / Examples rows MUST produce row-specific runnable handles.
   - Current: Pickles exist for generated Examples rows, but the launch mapping contract for row-specific pytest nodeids is unspecified.
   - Target: Each Examples row represented as a `Pickle` resolves to the exact pytest item nodeid for that row, not only to the outline scenario.
   - Acceptance: A scenario outline with at least two example rows emits two distinct runnable mappings, and each mapped `pytest <nodeid>` command runs only the corresponding row.

4. **Framework-owned binding cardinality diagnostics**: Framework MUST diagnose source Feature/Scenario binding cardinality for IDE consumers.
   - Current: Missing scenario bindings can be discovered by code-generation tooling, but IDE-oriented cardinality diagnostics are not part of the message contract.
   - Target: Framework emits diagnostics for source Feature/Scenario bindings: zero runnable bindings, exactly one runnable binding, or multiple source-level bindings.
   - Acceptance: Tests cover 0, 1, and >1 source Feature/Scenario hookups; the message stream marks 0 and >1 as warning conditions and leaves exactly 1 unreported or explicitly normal.

5. **Multiple hookup warning despite distinct runtime Pickles**: Framework MUST warn when the same source Feature/Scenario is connected multiple times, even if runtime collection represents those connections as distinct `Pickle`/pytest item instances.
   - Current: Runtime objects can differ across duplicate hookups, so counting only runtime `Pickle.id` values can miss source-level duplication.
   - Target: Binding diagnostics are keyed by stable source identity such as feature URI plus scenario / Examples AST identity, not only by runtime `Pickle.id`.
   - Acceptance: A test project connects the same source scenario from two pytest modules; the stream contains a multiple-binding warning for the source scenario while preserving both runnable handles.

6. **System launch metadata isolation**: Any launch metadata embedded in cucumber-messages MUST NOT affect normal user filtering, tag hooks, or pytest marker selection.
   - Current: Feature tags are converted to pytest marks by default; using synthetic tags for launch handles would risk changing selection behavior.
   - Target: If launch metadata uses tags or tag-like fields, system metadata is ignored by tag-to-mark conversion, tag expressions, and hook selection. If another carrier is selected, equivalent isolation is still required.
   - Acceptance: A test with launch metadata and user tags proves `-m`, tag hooks, and Cucumber tag behavior are identical with and without launch metadata.

7. **Exact matched step binding messages**: Framework MUST provide exact matcher-derived links from `PickleStep` to the Python `StepDefinition.sourceReference` available to that Feature file.
   - Current: Runtime message reporter can emit `StepDefinition` messages and `TestCase.testSteps[].stepDefinitionIds`, but the IDE contract for mock-run exact matching is not locked.
   - Target: IDE can implement go-to-definition by following message graph links from feature step to matched step definition, using framework matcher results rather than reimplementing matching.
   - Acceptance: Tests cover string, parse, regex, and cfparse-style step patterns where applicable; each matched feature step resolves through `TestCase.testSteps[].stepDefinitionIds` to the expected Python file URI and line.

8. **Scoped missing and ambiguous step diagnostics**: Framework MUST report missing and ambiguous step states with the Feature-file scoped set of available step definitions.
   - Current: Missing steps can produce suggestions, and ambiguity currently surfaces as warnings/errors, but IDE-oriented scoped availability diagnostics are not specified.
   - Target: When no step matches, IDE receives enough scoped information to offer stub generation and help the user see which step definitions were available for that Feature. When multiple definitions match, IDE receives a warning with candidate definitions. Future alternative-step parametrization remains separate.
   - Acceptance: Tests cover a missing step and an ambiguous step; missing-step output includes the unmatched `PickleStep` and scoped available step definitions, and ambiguous-step output includes candidate `StepDefinition` source references.

## Boundaries

**In scope:**
- Lock `--mock-run --messages-ndjson` as the IDE startup synchronization contract.
- Expose a reliable `Pickle` / Examples row to pytest `nodeid` launch mapping.
- Emit framework-owned binding cardinality diagnostics for source Feature/Scenario hookups.
- Preserve exact matcher-derived `PickleStep` to `StepDefinition.sourceReference` links for go-to-definition.
- Emit scoped missing-step and ambiguous-step diagnostics suitable for IDE warnings and stub generation.
- Add tests proving mock-run emits real messages without executing hooks or bodies.

**Out of scope:**
- A new `--cucumber-ide-sync` CLI option - existing `--mock-run` is the dry-run command.
- Implementing IntelliJ IDEA or VS Code plugins - this phase only defines and emits framework-side data.
- LSP registry maintenance after Python edits - IDE owns incremental registry updates after startup.
- Implementing step-stub insertion in user files - IDE/codegen may consume diagnostics, but this phase only emits data.
- Alternative-step parametrization for ambiguous matches - planned as a later separate mode.
- Choosing UI presentation for warnings - IDE decides how to display framework diagnostics.

## Constraints

- Message transport MUST remain cucumber-messages NDJSON through existing `--messages-ndjson` stdout/file-compatible reporting paths.
- Mock-run MUST NOT execute scenario hooks, step hooks, or step bodies.
- Runnable handles MUST be safe for pytest command execution and stable enough for IDE session indexing.
- System metadata MUST be isolated from user tags, pytest marks, tag expressions, and hook selection.
- Binding diagnostics MUST be computed by framework collection/runtime state, not by IDE-side inference.
- Go-to-definition links MUST reflect the framework matcher result, including parser behavior and scoped registries.

## Acceptance Criteria

- [ ] `pytest --mock-run --messages-ndjson report.ndjson` emits `Source`, `GherkinDocument`, `Pickle`, `StepDefinition`, and `TestCase` messages without executing hook/body probes.
- [ ] Every runnable `Pickle` in a simple scenario maps to exactly one pytest `nodeid`, and `pytest <nodeid>` runs that item.
- [ ] Every Examples row `Pickle` maps to a row-specific pytest `nodeid`, and each nodeid runs only that row.
- [ ] Source Feature/Scenario binding diagnostics distinguish 0, 1, and >1 hookups, with warnings for 0 and >1.
- [ ] Duplicate source scenario hookups warn even when runtime Pickles/items are distinct.
- [ ] Launch metadata does not affect pytest marker selection, Cucumber tag expressions, or tag hooks.
- [ ] Matched feature steps resolve through message graph links to exact Python step definition file URI and line.
- [ ] Missing-step diagnostics include unmatched step identity and scoped available step definitions for that Feature.
- [ ] Ambiguous-step diagnostics include candidate step definitions and source references.

## Ambiguity Report

| Dimension           | Score | Min   | Status | Notes |
|---------------------|-------|-------|--------|-------|
| Goal Clarity        | 0.92  | 0.75  | met    | Mock-run plus messages is the IDE startup contract; no new CLI option. |
| Boundary Clarity    | 0.87  | 0.70  | met    | IDE/plugin work, LSP registry updates, and alternative-step parametrization excluded. |
| Constraint Clarity  | 0.76  | 0.65  | met    | Transport, no-execution, metadata isolation, and framework-owned diagnostics locked. |
| Acceptance Criteria | 0.84  | 0.70  | met    | Requirements map to concrete message-stream and behavior tests. |
| **Ambiguity**       | 0.15  | <=0.20 | met    | Remaining carrier/key details are for spike/discuss, not spec. |

Status: met = dimension meets minimum; below minimum = planner treats as assumption.

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|-------|-------------|------------------|-----------------|
| 1 | Researcher | Does step generation discover missing steps the same way as reporter snippets? | Both use core matcher paths, but codegen is collection/static-ish and reporter is runtime/failure-driven. |
| 1 | Researcher | Is a new IDE sync command needed? | No new `--cucumber-ide-sync`; `--mock-run --messages-ndjson` is the dry-run synchronization basis. |
| 2 | Simplifier | What is the minimum reliable launch API? | Framework must expose a reliable way to run a concrete pytest item for each `Pickle`, including Examples rows. |
| 2 | Simplifier | Where should nodeid be carried? | Exact carrier/key remains open for spike; requirement is reliable message-stream launch mapping and metadata isolation. |
| 3 | Boundary Keeper | Who computes binding counts? | Framework computes binding cardinality; IDE consumes warnings and mappings. |
| 3 | Boundary Keeper | What is out of scope for registry? | IDE owns its registry/LSP updates after startup, but framework owns startup matcher-derived data and diagnostics. |
| 4 | Failure Analyst | How should duplicate scenario hookups be handled? | Warn when source Feature/Scenario is connected multiple times, even if runtime `Pickle` objects differ. |
| 4 | Failure Analyst | What should happen for missing/ambiguous steps? | Missing steps enable stub generation; ambiguous steps produce warnings, with future alternative-step parametrization left out of this phase. |

---

*Phase: 22-test-step-binding-api*
*Spec created: 2026-06-05*
*Next step: $gsd-discuss-phase 23 - implementation decisions (message carrier, stable keys, diagnostics payload shape)*
