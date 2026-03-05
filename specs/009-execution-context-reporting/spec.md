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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Context-Driven Reporter State (Priority: P1)

As a plugin maintainer, I want reporting state to come from a shared execution context, so event emission is consistent and does not depend on duplicated mutable state in reporter internals.

**Why this priority**: This is the core stability requirement for reporting correctness and directly removes a class of drift bugs caused by duplicated "current" fields.

**Independent Test**: Run the reporting flow for a scenario with hooks and steps; verify emitted events use only context-derived active identifiers and no duplicated reporter state is required.

**Acceptance Scenarios**:

1. **Given** an active execution context with current run, case, and step bindings, **When** the reporter emits lifecycle envelopes, **Then** emitted identifiers are resolved from execution context state.
2. **Given** a reporter instance after migration, **When** the reporting suite introspects reporter runtime attributes, **Then** no `current_<item>` state fields are required for lifecycle tracking.
3. **Given** a reporter hook call without bound execution context, **When** reporting logic runs, **Then** the reporter does not call context bootstrap/mutation APIs and emits deterministic diagnostics for missing correlation state.

---

### User Story 2 - Centralized Gherkin Registry Ownership (Priority: P2)

As a model maintainer, I want object registry ownership moved out of the feature document object and into execution context, so document models remain representational and lookup concerns are centralized.

**Why this priority**: This enforces clean model boundaries and prevents model objects from carrying hidden mutable indexing state.

**Independent Test**: Build a feature document with nested nodes and verify registry-based lookups are served by execution context while the feature document remains a pure structural model.

**Acceptance Scenarios**:

1. **Given** a parsed feature document with backgrounds, rules, and scenarios, **When** an object lookup is requested, **Then** execution context provides the registry result.
2. **Given** feature model instances, **When** they are serialized or inspected, **Then** they do not expose or persist registry ownership state.

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

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST treat execution context as the single source of truth for active reporting lifecycle state.
- **FR-002**: The reporter MUST derive lifecycle identifiers from execution context at emission time.
- **FR-003**: The reporter MUST NOT require plugin-level `current_<item>` state fields for lifecycle or reference tracking.
- **FR-004**: Feature document model objects MUST NOT own the cross-object registry used for reporting lookup.
- **FR-005**: Execution context MUST own and expose the object registry required for reporting lookup and reference mapping.
- **FR-006**: Cross-object reference resolution for emitted messages MUST be performed through execution context lookups.
- **FR-007**: When required context data is missing, the system MUST produce deterministic diagnostics without synthetic state fabrication.
- **FR-008**: Reporting behavior for currently supported message outputs MUST remain externally compatible after the migration.
- **FR-009**: The system MUST isolate execution context state per test run/worker scope to prevent cross-run contamination.
- **FR-010**: Governance checks MUST verify that runtime-required fields are covered by real runtime events and that any non-implementable fields have explicit, hard-limitation rationale.
- **FR-011**: ExecutionContext lifecycle state MUST be created and mutated only by test-execution plugins; reporting plugins MUST treat ExecutionContext as read-only.
- **FR-012**: Reporting plugins MUST NOT call context bootstrap or mutation APIs (`initialize_session_root`, `get_or_create`, `set`, `pop`, `ensure_session_root_for_session`) under any runtime path.
- **FR-013**: If required context state is absent in a reporting hook, reporter behavior MUST be fail-safe and deterministic: emit diagnostics and skip only context-dependent correlation fields instead of creating or backfilling context state.
- **FR-014**: Any reporter-local context helper (including `_resolve_execution_context` or equivalent) MUST be read-only by contract: no fallback to context creation/bootstrap APIs and no side effects on context stores.
- **FR-015**: The system MUST provide a dedicated adapter layer between the runtime execution model and the cucumber message model.
- **FR-016**: Runtime execution flow MUST use execution-model objects; reporting flow MUST use message-model objects produced through the adapter layer.
- **FR-017**: The execution model MUST support deterministic serialization into the message model and deterministic deserialization from the message model.
- **FR-018**: Cross-object links reconstructed from message payloads MUST be resolved via message IDs and a registry owned by execution context.
- **FR-019**: Adapter conversion MUST preserve object identity relationships (feature/scenario/step/reference links) required for lifecycle reporting and governance validation.

### Key Entities *(include if feature involves data)*

- **ExecutionContext**: Runtime-scoped state container that owns active lifecycle bindings, object registry, and reference mappings used by reporting.
- **ReporterLifecycleEmission**: Event emission operation that reads active IDs and mappings from execution context and writes NDJSON-compatible envelopes.
- **GherkinDocumentModel**: Structural feature/rule/background/scenario representation without ownership of reporting registries.
- **ReferenceMapping**: Context-managed links between emitted message references and source entities.
- **GovernanceDecision**: Classification record for field capability (runtime-covered or explicitly non-implementable with hard technical reason).
- **ExecutionMessageAdapter**: Translation boundary that converts runtime execution-model objects to/from cucumber message-model objects with deterministic mapping rules.
- **MessageObjectRegistry**: ID-indexed registry used during deserialize/reference reconstruction to resolve object links declared in message payloads.

### Assumptions & Dependencies

- The existing runtime provides enough source signals for most fields once reporting uses execution context consistently.
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
