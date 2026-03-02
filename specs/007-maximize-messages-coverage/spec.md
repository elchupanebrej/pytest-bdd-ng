# Feature Specification: Maximize Messages Capability Coverage

**Feature Branch**: `[007-maximize-messages-coverage]`
**Created**: 2026-02-25
**Status**: Draft
**Language**: English
**Input**: User description: "мне нужно чтоб возможности библиотеки messages использовались в pytest-bdd-ng максимально полно, по возможности без белых пятен."

## Clarifications

### Session 2026-02-28

- Q: How should paths between package artifacts (like the JSON schema) be resolved? → A: Package Resources (Relative path resolution based on module location is prohibited. Use `importlib.resources` for package artifacts, or `git` for test-only paths. Patterns like `PLUGIN_PATH` must be avoided).
- Q: When the validation process exhaustively checks payload fields, how should the system handle the failure? → A: Hard failure (Any missing coverage or structurally invalid field immediately fails the test suite).
- Q: Will dynamic traceability be active for all test runs by default, or enabled via a specific flag? → A: Opt-in via flag (Tracing only runs when explicitly requested, preserving fast normal test execution).

### Session 2026-02-27

- Q: How should coverage verification be implemented to ensure no "white spots" are missed? → A: Schema-oriented (Automatically derive inventory from messages JSON Schema/Protobuf).
- Q: What is the required validation depth for each message payload? → A: Exhaustive (Validate every field defined in the schema).
- Q: How should the system determine if a field is "covered" during runtime tests? → A: Dynamic Traceability (Count as covered ONLY when runtime execution populates the field).
- Q: How should the coverage report treat optional fields that are never populated? → A: Scenario-Specific (Require specific "Evidence Scenarios" for each field, e.g., error fields require failing tests).
- Q: How should complex nested fields like step arguments be validated? → A: Structural Integrity (Validate full nesting and exact character offsets).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete capability inventory (Priority: P1)

As a maintainer, I need a complete and explicit inventory of relevant `messages` capabilities so no coverage gaps remain hidden.

**Why this priority**: Without a complete inventory, gaps cannot be identified or managed, and all other reporting improvements become unreliable.

**Independent Test**: Review the capability inventory and confirm every relevant capability is listed exactly once with a defined support status and rationale when not implemented.

**Acceptance Scenarios**:

1. **Given** a baseline upstream `messages` release, **When** the maintainer reviews the capability inventory, **Then** every relevant capability is present with exactly one support status.
2. **Given** a capability marked as not implemented, **When** a reviewer inspects the inventory, **Then** the capability includes a clear rationale and decision ownership.

---

### User Story 2 - Consistent event coverage (Priority: P2)

As a report consumer, I need runtime outcomes to map consistently to `messages` capabilities so event outputs are predictable and comparable.

**Why this priority**: Consistent mapping prevents contradictory reporting behavior and reduces integration risk for downstream consumers.

**Independent Test**: Run a fixed release-readiness matrix containing pass, fail, skipped, undefined, and interrupted outcomes, plus at least one retry and one parallel-worker scenario, and verify each reported outcome is traceable to an approved capability entry.

**Acceptance Scenarios**:

1. **Given** the fixed release-readiness matrix (pass, fail, skipped, undefined, interrupted, plus one retry and one parallel-worker scenario), **When** reporting data is produced, **Then** each outcome maps to a defined capability and approved status vocabulary.
2. **Given** the same outcome from different reporting entry points, **When** outputs are compared, **Then** they use the same capability mapping and status terminology.

---

### User Story 3 - Governance for release decisions (Priority: P3)

As a release reviewer, I need a governance checklist that shows coverage decisions for all capabilities so readiness can be evaluated without manual discovery.

**Why this priority**: Formal governance prevents silent regressions and ensures every unsupported area is visible before release.

**Independent Test**: Use only the governance checklist to identify implemented capabilities, intentional exclusions, and unresolved items for release sign-off.

**Acceptance Scenarios**:

1. **Given** a release candidate, **When** a reviewer opens the governance checklist, **Then** they can see implemented, non-implementable, not-acceptable, not-applicable, and pending capabilities with no missing entries.
2. **Given** unresolved or unreviewed capabilities, **When** release readiness is evaluated, **Then** those items are explicitly flagged as blockers or deferred scope by policy.

### Edge Cases

- A capability exists upstream but cannot be represented from available runtime information.
- A single runtime outcome could map to multiple capabilities with different interpretations.
- Execution stops mid-run and produces partial reporting data.
- Upstream capabilities change between release planning and release approval.
- Terminology drift introduces equivalent but differently named statuses across artifacts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST automatically maintain a canonical inventory of all upstream `messages` capabilities derived from the official JSON Schema/Protobuf definitions to ensure 100% field coverage.
- **FR-002**: Each capability in the inventory MUST have exactly one status from the controlled vocabulary: Implemented, Non-Implementable, Not-Acceptable, Not-Applicable, or Pending.
- **FR-003**: Any capability not marked Implemented MUST include `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at`.
- **FR-004**: The system MUST define mapping rules from supported runtime outcomes to capability entries in the inventory.
- **FR-005**: The same runtime outcome MUST use consistent status terminology and capability mapping across all reporting entry points.
- **FR-006**: The system MUST publish a governance artifact that lists all capability entries and their current status.
- **FR-007**: The governance artifact MUST explicitly flag unresolved or unreviewed capability entries for release decision-making.
- **FR-008**: The system MUST run baseline comparison on a fixed weekly schedule and surface newly added, changed, or removed capabilities for review.
- **FR-009**: The specification MUST define and enforce the mandatory evidence field set for Non-Implementable, Not-Acceptable, or Not-Applicable statuses as `rationale`, `decision_owner`, `evidence_refs`, and `reviewed_at`.
- **FR-010**: The specification MUST declare explicit out-of-scope boundaries for capabilities intentionally excluded from the current release scope.
- **FR-011**: Stakeholders MUST be able to trace each reported message outcome in sample runs back to a capability entry in the governance artifact.
- **FR-012**: Status terminology MUST remain consistent across specification, planning, and governance artifacts.
- **FR-013**: The validation process MUST exhaustively check every field defined in the `messages` schema for each emitted payload to ensure no data is omitted. Any missing coverage or structurally invalid field MUST result in a hard failure of the test suite.
- **FR-014**: The system MUST require specific "Evidence Scenarios" to prove coverage for state-dependent fields (e.g., ensuring `exception` fields are populated during failing test scenarios). Dynamic traceability MUST be opt-in via a specific CLI flag (e.g., `--messages-coverage`) to preserve performance during normal test executions.
- **FR-015**: For complex nested fields (e.g., `step_match_arguments_lists`), the validation MUST verify structural integrity, including all nested groups, children, and exact character offsets.

### Key Entities *(include if feature involves data)*

- **Message Capability**: A single upstream capability entry with identifier, description, relevance flag, and baseline release reference.
- **Capability Decision**: The assigned support status and mandatory evidence field set (`rationale`, `decision_owner`, `evidence_refs`, `reviewed_at`) for one capability.
- **Outcome Mapping Rule**: A rule that links a runtime outcome class to one or more capability identifiers and required reporting semantics.
- **Governance Checklist Entry**: A release-facing record that summarizes capability status, unresolved risks, and disposition (approved, blocked, deferred).

## Assumptions

- The upstream baseline release for comparison is fixed at planning time for each delivery cycle.
- A capability is considered relevant if it can affect emitted envelope payload, lifecycle linkage, status mapping, or governance checklist output.
- Non-Implementable and Not-Acceptable decisions require explicit reviewer accountability.
- Consumers accept explicit unsupported/deferred status visibility as preferable to silent omission.

## Out of Scope

- Redesigning unrelated pytest-bdd-ng execution behavior outside reporting coverage decisions.
- Inventing capability types that do not exist in the upstream `messages` baseline.
- Backfilling historical release governance data prior to this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of fields in relevant upstream `messages` payloads are verified via dynamic traceability (observed in runtime output) or documented with explicit non-implementation rationale.
- **SC-002**: 100% of non-implemented capability entries include rationale and decision owner metadata.
- **SC-003**: In the fixed release-readiness matrix (pass, fail, skipped, undefined, interrupted, plus one retry and one parallel-worker scenario), at least 95% of observed reporting outcomes map to approved capability entries with no ambiguous status terms.
- **SC-004**: Release reviewers can determine unresolved coverage gaps using only the governance artifact in under 10 minutes.
- **SC-005**: Zero undocumented capability gaps are discovered during pre-release review after governance sign-off.
