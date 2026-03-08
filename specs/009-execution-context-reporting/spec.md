# Feature Specification: Execution Context Reporting Consistency

**Feature Branch**: `009-execution-context-reporting`
**Created**: 2026-03-03
**Status**: Draft
**Input**: User description: "Репортер плагин должен использовать при репортинге ExecutionContext. Полей в плагине с названием current_<item> не должно быть - они должны идти из контекста. Класс Feature в src/pytest_bdd/model/gherkin_document/core.py не должен нести реестр обьектов - он должен быть в ExecutionContext. Разрешение ссылок между обьектами тоже должно быть через ExecutionContext"

## Clarifications

### Session 2026-03-03

- Q: Which plugin layer owns `ExecutionContext` mutations versus consumption? → A: Test-execution plugins create and update `ExecutionContext`; reporting plugins only read from it.
- Q: May reporting plugins call context bootstrap APIs such as `initialize_session_root(...)`? → A: No. Reporting plugins must not initialize/create/mutate execution context; if context is missing they must emit deterministic diagnostics and skip correlation-dependent emission paths.
- Q: Is reporter helper `_resolve_execution_context` acceptable if it can fallback to `get_or_create(...)`? → A: No. Reporter-side context helpers may only perform lookup/read (`resolve_request_execution_context`) and must return missing-context diagnostics instead of creating context.

### Session 2026-03-05

- Q: How should runtime execution models and message models be separated and connected? → A: Introduce a dedicated adapter layer: execution model is used during runtime, message model is used for reporting, and execution model supports deterministic serialize/deserialize conversion to/from message model with ID+registry-based reference resolution.

### Session 2026-03-06

- Q: How must Scenario vs Pickle fixture semantics be aligned, and is a deprecation window required? → A: Remove `scenario` fixture, keep only `pickle` fixture for executable scenario data, and apply this as an immediate breaking API change without a deprecation period.
- Q: Should semantic normalization apply across hooks/context APIs beyond fixtures? → A: Yes. Use `pickle` for executable runtime scenario objects across fixtures, hooks, context fields, and adapter contracts; reserve `scenario` only for Gherkin AST `Scenario` nodes, with no compatibility aliases.

### Session 2026-03-07

- Q: What is the final boundary for `src/pytest_bdd/model/gherkin_document/core.py::Feature`? → A: Eliminate the `Feature` adapter from runtime/reporting semantics entirely: move all required registry, lookup, and feature-level execution data into `Run`/`ScenarioRun`, and do not expose or consume `Feature` in hooks, fixtures, or adapter APIs.

### Session 2026-03-08

- Q: Where must `pytest_bdd_id_generator` be stored and resolved from? → A: `pytest_bdd_id_generator` must be stored in `pytest config.stash` as session-shared runtime state and must not be carried on ad-hoc `config` attributes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Context-Driven Reporter State (Priority: P1)

As a plugin maintainer, I want reporting state to come from a shared execution context, so event emission is consistent and does not depend on duplicated mutable state in reporter internals.

**Why this priority**: This is the core stability requirement for reporting correctness and directly removes a class of drift bugs caused by duplicated "current" fields.

**Independent Test**: Run the reporting flow for a scenario with hooks and steps; verify emitted events use only context-derived active identifiers and no duplicated reporter state is required.

**Acceptance Scenarios**:

1. **Given** an active execution context with current run, case, and step bindings, **When** the reporter emits lifecycle envelopes, **Then** emitted identifiers are resolved from execution context state.
2. **Given** a reporter instance after migration, **When** the reporting suite introspects reporter runtime attributes, **Then** no `current_<item>` state fields are required for lifecycle tracking.
3. **Given** a reporter hook call without bound execution context, **When** reporting logic runs, **Then** the reporter does not call context bootstrap/mutation APIs and emits deterministic diagnostics for missing correlation state.
4. **Given** hook and context APIs after migration, **When** an executable runtime scenario object is referenced, **Then** the canonical name is `pickle`, while `scenario` names only the Gherkin AST node type.

---

### User Story 2 - Run-Owned Feature State (Priority: P2)

As a model maintainer, I want the `Feature` adapter removed from runtime/reporting flows and all feature-level registry and lookup state moved into `Run`/`ScenarioRun`, so execution APIs operate only on canonical runtime and message-model objects.

**Why this priority**: This enforces clean model boundaries, removes an unstable adapter layer, and prevents runtime/reporting code from depending on hidden mutable state attached to document wrappers.

**Independent Test**: Collect and execute features with nested nodes and verify hooks and fixtures expose only `Run`, `ScenarioRun`, `GherkinDocument`, `Pickle`, and `Source`, while all registry-based lookups are served from `Run`/`ScenarioRun` without constructing or consuming `Feature`.

**Acceptance Scenarios**:

1. **Given** parsed source, gherkin document, and pickles with backgrounds, rules, and scenarios, **When** feature-level runtime data is initialized, **Then** `Run`/`ScenarioRun` own the registry and lookup state required by execution and reporting.
2. **Given** hook and fixture APIs after migration, **When** plugin code accesses feature-level runtime data, **Then** it resolves through `Run`/`ScenarioRun` or message-model objects and never through `src/pytest_bdd/model/gherkin_document/core.py::Feature`.
3. **Given** collected gherkin message objects, **When** they are serialized or inspected, **Then** no runtime/reporting adapter object named `Feature` is required or exposed.
4. **Given** execution plugins initialize session-shared runtime services, **When** they provide `pytest_bdd_id_generator`, **Then** it is stored and resolved through `pytest config.stash` rather than through custom attributes on `config`.

---

### User Story 3 - Context-Based Reference Resolution (Priority: P3)

As an integrator of message generation, I want cross-object references resolved through execution context so all emitted references stay coherent across documents, pickles, and test execution artifacts.

**Why this priority**: Centralized reference resolution reduces orphan links, simplifies diagnostics, and keeps behavior deterministic.

**Independent Test**: Execute end-to-end message generation on features containing nested structures and verify references resolve through the context resolver with deterministic behavior for missing links.

**Acceptance Scenarios**:

1. **Given** linked gherkin and runtime entities, **When** the reporter emits messages with references, **Then** reference IDs are resolved through execution context mappings.
2. **Given** a missing reference mapping, **When** an event requiring that mapping is emitted, **Then** the system returns a deterministic diagnostic instead of silently fabricating data.

### Edge Cases

- Execution context is missing a required active binding at emission time.
- Multiple objects share a conflicting identifier and a deterministic conflict policy must be applied.
- Nested background/rule/scenario structures contain valid links but are created in non-linear order.
- Parallel test workers emit events concurrently and must not leak object bindings across worker scopes.
- A reference target exists in the document model but is absent from context registry due to partial parse or skipped setup.
- Legacy plugin or test code still requests `scenario` fixture after API switch and must fail with deterministic diagnostics.
- Legacy plugin or test code still expects `src/pytest_bdd/model/gherkin_document/core.py::Feature` in hooks or fixtures and must fail deterministically or be migrated to `Run`/`ScenarioRun` and message-model inputs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST treat execution context as the single source of truth for active reporting lifecycle state.
- **FR-002**: The reporter MUST derive lifecycle identifiers from execution context at emission time.
- **FR-003**: The reporter MUST NOT require plugin-level `current_<item>` state fields for lifecycle or reference tracking.
- **FR-004**: `src/pytest_bdd/model/gherkin_document/core.py::Feature` MUST NOT own the cross-object registry used for reporting lookup and MUST NOT remain as a runtime/reporting adapter layer.
- **FR-005**: `Run` and `ScenarioRun` MUST own and expose the object registry, lookup state, and feature-level runtime mappings required for reporting and execution lookup.
- **FR-006**: Cross-object reference resolution for emitted messages MUST be performed through `Run`/`ScenarioRun` context lookups rather than through `Feature`.
- **FR-007**: When required context data is missing, the system MUST produce deterministic diagnostics without synthetic state fabrication.
- **FR-008**: Reporting behavior for currently supported message outputs MUST remain externally compatible after the migration.
- **FR-009**: The system MUST isolate execution context state per test run/worker scope to prevent cross-run contamination.
- **FR-010**: Governance checks MUST verify that runtime-required fields are covered by real runtime events and that any non-implementable fields have explicit, hard-limitation rationale.
- **FR-011**: ExecutionContext lifecycle state MUST be created and mutated only by test-execution plugins; reporting plugins MUST treat ExecutionContext as read-only.
- **FR-012**: Reporting plugins MUST NOT call context bootstrap or mutation APIs (`initialize_session_root`, `get_or_create`, `set`, `pop`, `ensure_session_root_for_session`) under any runtime path.
- **FR-013**: If required context state is absent in a reporting hook, reporter behavior MUST be fail-safe and deterministic: emit diagnostics and skip only context-dependent correlation fields instead of creating or backfilling context state.
- **FR-014**: Any reporter-local context helper (including `_resolve_execution_context` or equivalent) MUST be read-only by contract: no fallback to context creation/bootstrap APIs and no side effects on context stores.
- **FR-015**: The system MUST provide a dedicated adapter layer between the runtime execution model and the cucumber message model.
- **FR-016**: Runtime execution flow MUST use `Run`/`ScenarioRun` plus canonical message-model objects; reporting flow MUST use message-model objects produced through the adapter layer, with no `Feature` adapter in the boundary.
- **FR-017**: The execution model MUST support deterministic serialization into the message model and deterministic deserialization from the message model.
- **FR-018**: Cross-object links reconstructed from message payloads MUST be resolved via message IDs and a registry owned by `Run`/`ScenarioRun`.
- **FR-019**: Adapter conversion MUST preserve object identity relationships (feature/scenario/step/reference links) required for lifecycle reporting and governance validation.
- **FR-020**: Executable-scenario fixture semantics MUST be canonicalized to `pickle`; fixture `scenario` MUST NOT be exposed.
- **FR-021**: The fixture-semantic switch from `scenario` to `pickle` MUST be shipped as an immediate API change with no deprecation period, alias, or compatibility shim.
- **FR-022**: Hook parameter names, context field names, and adapter contract names MUST match object semantics: executable runtime scenario object is `pickle`, and Gherkin AST node is `scenario`.
- **FR-023**: The system MUST NOT expose compatibility aliases where a `Pickle`-typed value is surfaced under any `scenario`-named API parameter or field.
- **FR-024**: Hooks and fixtures MUST NOT expose `src/pytest_bdd/model/gherkin_document/core.py::Feature` instances; permitted feature-level inputs are `Run`, `ScenarioRun`, `GherkinDocument`, `Pickle`, `Source`, or values derived from them.
- **FR-025**: Any feature-level capability currently served by `Feature` MUST be migrated into `Run` or `ScenarioRun` before the `Feature` adapter is removed from runtime and reporting flows.
- **FR-026**: Feature discovery, collection, and parametrization flows MUST operate on canonical message-model objects directly and MUST NOT require constructing `Feature` as an intermediate adapter for hooks, fixtures, or reporting.
- **FR-027**: `pytest_bdd_id_generator` MUST be stored and resolved through `pytest config.stash` as session-shared runtime state; direct storage on ad-hoc `config` attributes MUST NOT remain in the runtime or reporting implementation.

### Key Entities *(include if feature involves data)*

- **ExecutionContext**: Runtime-scoped state container that owns active lifecycle bindings, object registry, and reference mappings used by reporting.
- **ReporterLifecycleEmission**: Event emission operation that reads active IDs and mappings from execution context and writes NDJSON-compatible envelopes.
- **GherkinDocumentMessage**: Canonical cucumber message-model representation of the feature document used for structural feature, rule, background, and scenario data.
- **ReferenceMapping**: Context-managed links between emitted message references and source entities.
- **GovernanceDecision**: Classification record for field capability (runtime-covered or explicitly non-implementable with hard technical reason).
- **ExecutionMessageAdapter**: Translation boundary that converts runtime execution-model objects to/from cucumber message-model objects with deterministic mapping rules.
- **RunOwnedObjectRegistry**: ID-indexed registry owned by `Run`/`ScenarioRun` and used during deserialize/reference reconstruction to resolve object links declared in message payloads.
- **PytestConfigStashBinding**: Canonical stash-backed location for session-shared runtime services such as `Run` and `pytest_bdd_id_generator`.

### Assumptions & Dependencies

- The existing runtime provides enough source signals for most fields once reporting uses execution context consistently.
- `GherkinDocument`, `Source`, and `Pickle` message objects provide sufficient structural data once feature-level registry and lookup state is stored in `Run`/`ScenarioRun` instead of `Feature`.
- Truly non-implementable fields are limited to cases where runtime cannot produce required domain data (for example, foreign-runtime-only exception models).
- Existing tests and governance artifacts can be extended to validate context-only reporting and capability classifications.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of reporter lifecycle emissions in the validation suite are resolved from execution context state.
- **SC-002**: 0 plugin fields matching `current_<item>` remain required for lifecycle or reference reporting behavior.
- **SC-003**: 100% of reference-bearing messages in end-to-end validation use context-based resolution paths.
- **SC-004**: 100% of runtime-required capability fields are covered by real test executions in CI gating.
- **SC-005**: 100% of remaining uncovered fields are explicitly classified with a documented hard technical limitation and no synthetic event fabrication.
- **SC-006**: 0 reporter code paths invoke execution-context bootstrap/mutation APIs during message emission lifecycle.
- **SC-007**: 100% of reporter context-helper code paths are lookup-only and return deterministic missing-context handling without creating context.
- **SC-008**: 100% of message-emission payloads in the adapter validation suite are produced via the adapter layer from execution-model objects.
- **SC-009**: Round-trip adapter tests (execution → message → execution) preserve required IDs and reference relationships for all runtime-required message entities.
- **SC-010**: 0 runtime fixtures named `scenario` remain in the executable-scenario API surface; `pickle` is the only executable-scenario fixture.
- **SC-011**: 0 hook/context/adapter API surfaces expose `Pickle` objects under `scenario` naming; 100% use `pickle` naming for executable runtime scenario objects.
- **SC-012**: 0 hook or fixture API surfaces expose `src/pytest_bdd/model/gherkin_document/core.py::Feature`.
- **SC-013**: 100% of feature-level registry and lookup operations exercised by the validation suite resolve through `Run`/`ScenarioRun` without constructing or consuming `Feature`.
- **SC-014**: 100% of runtime code paths that need `pytest_bdd_id_generator` resolve it from `pytest config.stash`, and 0 runtime/reporting code paths rely on ad-hoc `config.pytest_bdd_id_generator`-style attributes.
