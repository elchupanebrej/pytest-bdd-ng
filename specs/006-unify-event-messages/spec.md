# Feature Specification: Unify Event Message Reporting

**Feature Branch**: `006-unify-event-messages`  
**Created**: 2026-02-25  
**Status**: Draft  
**Language**: English  
**Input**: User description: "This library must report events using messages approach (investigate messages dir). Now it somehow outdated and report in-non consistent way. Build of event messages must be validated by MyPy"

## Clarifications

### Session 2026-02-25

- Q: What is the scope boundary for legacy reporting outputs? → A: Keep legacy scenario report, but require it to be derived from the same canonical message events (no separate reporting logic).
- Q: What correlation ID uniqueness rule should apply? → A: Correlation IDs are unique per scenario execution attempt, including retries and parallel workers.
- Q: What is the failure policy for message emission errors? → A: Fail the run only when message reporting is enabled/requested; otherwise continue without enforcing message output.
- Q: Should user-facing report formatting changes be included in this feature scope? → A: Include user-facing output formatting changes in this same feature.
- Q: What protocol version compatibility target should this feature enforce? → A: Support only the latest message protocol version.
- Q: How should non-incremental or duplicate spec prefixes be fixed? → A: Keep historical numbering as-is except conflicts; rename duplicate prefixes to the next available number and enforce unique monotonic numbering for all new specs.
- Q: What message scope should be explicitly listed for status governance? → A: Define an exhaustive list for all in-scope envelope message types, including metadata/source/discovery messages.
- Q: What status model and fallback behavior should apply? → A: Only `done`, `non-implementable`, and `not-acceptable` are allowed; unknown or custom statuses are rejected as errors.
- Q: How should `non-implementable` and `not-acceptable` be distinguished? → A: `non-implementable` means technically impossible in the current context; `not-acceptable` means policy or quality rejection.
- Q: When are implementation comments mandatory? → A: Comments are required for `non-implementable` and `not-acceptable`; comments are optional for `done`.
- Q: Where must status/comment be attached? → A: Status/comment must be attached for every in-scope envelope message type that is classified as status-capable.
- Q: How should sensitive implementation comments be handled? → A: No automatic redaction or truncation is applied by this feature.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Emit Canonical Lifecycle Messages (Priority: P1)

As an integration consumer, I want every test-run, scenario, and step lifecycle event to be emitted as structured messages so downstream tools receive a complete and reliable event stream.

**Why this priority**: Event emission is the core contract for reporting and external integrations; incomplete or inconsistent lifecycle events break downstream analysis.

**Independent Test**: Run one passing scenario and one failing scenario with message output enabled, then validate that each lifecycle stage is present exactly once where applicable and references are consistent.

**Acceptance Scenarios**:

1. **Given** a test run with one passing scenario, **When** reporting messages are produced, **Then** the stream includes run start/finish, scenario start/finish, and step start/finish events with valid references.
2. **Given** a test run where a step fails, **When** reporting messages are produced, **Then** failure status and timing are represented in lifecycle messages without missing finish events.
3. **Given** multiple scenarios in one run, **When** reporting messages are produced, **Then** each scenario lifecycle is isolated and correlated to the same run context.

---

### User Story 2 - Eliminate Inconsistent Event Shapes and Ordering (Priority: P2)

As a maintainer, I want reporting events to follow one consistent message schema and ordering model so consumers no longer need custom normalization for edge cases.

**Why this priority**: Inconsistent shape and ordering creates fragile tooling and increases maintenance/support overhead.

**Independent Test**: Validate message streams for pass, fail, and missing-step scenarios against a consistency checker that verifies event shape, ordering, and identifier linkage.

**Acceptance Scenarios**:

1. **Given** any scenario outcome (pass/fail/missing step), **When** message stream validation runs, **Then** no orphan identifiers or duplicate lifecycle identifiers are detected.
2. **Given** attachments or diagnostics emitted during execution, **When** messages are generated, **Then** those events are linked to the correct active scenario or step context.
3. **Given** event consumers that process the stream in order, **When** they read emitted messages, **Then** parent lifecycle events bracket child lifecycle events consistently.
4. **Given** user-facing report outputs generated from the same run, **When** rendering occurs, **Then** formatting and displayed statuses are consistent with the canonical emitted event stream.

---

### User Story 3 - Enforce Type-Validated Message Construction (Priority: P3)

As a maintainer, I want message-building paths to pass static type validation so invalid event construction is caught before release.

**Why this priority**: Type validation reduces regressions in message contracts and prevents silent runtime inconsistencies.

**Independent Test**: Run the repository type-validation workflow and confirm event-construction paths pass without suppressed type failures in scope.

**Acceptance Scenarios**:

1. **Given** a valid implementation, **When** static type validation runs, **Then** message construction paths pass without type errors.
2. **Given** an intentionally invalid message field assignment, **When** static type validation runs, **Then** validation fails before merge.

### Edge Cases

- Scenario setup fails before the first step executes.
- Step definition is missing, producing an error path without normal step completion.
- Scenario is retried or re-executed, requiring distinct lifecycle identities per attempt.
- Binary and text attachments are emitted in the same run.
- Parallel workers emit events concurrently for different scenarios.
- A message carries `non-implementable` or `not-acceptable` status with an empty comment.
- A scenario attempt receives contradictory terminal statuses from different hook paths.
- A status/comment is attached to a message type classified as not applicable.
- A comment contains multiple lines or large payload content and must remain parseable.

### Assumptions

- The reporting contract remains message-first, and non-message outputs are downstream representations of the same event truth.
- Existing external consumers depend on stable lifecycle semantics and identifier correlations.
- Static type validation is part of regular contributor and CI quality gates.
- Backward compatibility for older message protocol versions is out of scope for this feature.
- Producers of implementation comments avoid embedding secrets; this feature does not redact comment content.
- Supported pytest/pluggy version combinations preserve required hook availability and ordering for status assignment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST emit reporting events using a canonical message envelope model for run, scenario, step, and attachment/diagnostic events.
- **FR-002**: The system MUST ensure each emitted message contains exactly one event payload and all required attributes for that payload type.
- **FR-003**: The system MUST emit exactly one run-start and one run-finish event per test run.
- **FR-004**: The system MUST emit scenario lifecycle start/finish events for every executed scenario and correlate them to the owning run.
- **FR-005**: The system MUST emit step lifecycle start/finish events for every executed step and reflect the final step outcome accurately.
- **FR-006**: The system MUST link attachment and diagnostic events to the active scenario or step lifecycle context.
- **FR-007**: The system MUST preserve lifecycle ordering rules within each scenario (start before finish for each lifecycle level, parent boundaries around child events).
- **FR-008**: The system MUST prevent inconsistent streams by disallowing duplicate lifecycle identifiers and orphan references.
- **FR-009**: The system MUST ensure message-construction code paths are statically type-validated in the project quality gate.
- **FR-010**: The system MUST include regression validation covering representative pass, fail, and error-path runs for message completeness and consistency.
- **FR-011**: The system MUST generate legacy scenario-report outputs from the same canonical message event stream and MUST NOT maintain independent event-construction logic for those outputs.
- **FR-012**: The system MUST assign correlation identifiers uniquely per scenario execution attempt, including retried attempts and parallel-worker executions.
- **FR-013**: The system MUST fail execution on message emission or serialization errors when message reporting output is explicitly enabled. When message reporting is not enabled, execution MUST continue and MUST emit exactly one deterministic warning diagnostic per run indicating that message-output guarantees were skipped.
- **FR-014**: The system MUST include user-facing reporting output formatting updates in scope and MUST ensure scenario report, gherkin terminal output, and cucumber JSON output are derived consistently from canonical message events.
- **FR-015**: The system MUST target only the latest supported message protocol version for event emission and validation in this feature scope.
- **FR-016**: The repository specification catalog MUST avoid duplicate numeric prefixes; when duplicates exist, conflicting directories MUST be renamed to the next available number while non-conflicting historical prefixes remain unchanged.
- **FR-017**: New feature specifications MUST use unique monotonic numeric prefixes so prerequisite checks identify exactly one active specification per prefix.
- **FR-018**: The system MUST maintain an explicit exhaustive in-scope envelope message-type list for governance checks, including `meta`, `source`, `gherkin_document`, `pickle`, `step_definition`, `parameter_type`, `hook`, `test_run_started`, `test_case`, `test_case_started`, `test_step_started`, `test_step_finished`, `test_case_finished`, `test_run_finished`, and `attachment`.
- **FR-019**: For every message type in the governance list, the system MUST define implementation-status/comment applicability as one of required, optional, or not applicable.
- **FR-020**: The only valid implementation-status values are `done`, `non-implementable`, and `not-acceptable`; any unknown or custom value MUST be rejected as a validation error without fallback remapping.
- **FR-021**: The system MUST apply objective status semantics: `non-implementable` for technical impossibility in the current execution context, and `not-acceptable` for policy or quality rejection when implementation remains technically possible.
- **FR-022**: The system MUST require a non-empty implementation comment for `non-implementable` and `not-acceptable` statuses, and MAY allow an optional comment for `done`.
- **FR-023**: The system MUST assign status and comment ownership at message-formation time in the responsible hook path and MUST preserve that ownership in the emitted canonical message.
- **FR-024**: The governance matrix MUST classify message-type applicability exactly as follows: `test_step_finished` and `test_case_finished` = required, `test_run_finished` and `attachment` = optional, all other in-scope message types = not applicable.
- **FR-025**: The system MUST treat conflicting terminal statuses for the same scenario attempt as an invalid state and MUST fail message validation for that attempt.
- **FR-026**: For retries or re-executions, the system MUST keep prior attempt statuses/comments immutable and MUST emit a new independently correlated status/comment record for each new attempt.
- **FR-027**: The system MUST ensure scenario report, gherkin terminal output, and cucumber JSON output expose the same status/comment semantics as the canonical message stream for all status-capable message types.
- **FR-028**: The system MUST emit status/comment observability fields at minimum for `scenario_attempt_id`, `payload_kind`, `implementation_status`, `comment_present`, and `hook_origin`.
- **FR-029**: The system MUST preserve status/comment integrity across async and parallel-worker boundaries so no status-capable message loses, duplicates, or cross-links comment/status fields outside its attempt scope.
- **FR-030**: The system MUST preserve implementation comments exactly as provided (including multi-line content) and MUST NOT perform automatic truncation or redaction in this feature scope.
- **FR-031**: Release-governance checks MUST block promotion artifacts when any `not-acceptable` status exists in the canonical stream for the validated run.

### Non-Functional Requirements

- **NFR-001**: With message reporting enabled, the targeted reporting validation suite MUST complete within <=10% wall-clock overhead compared to the same suite with reporting disabled in the same environment.

### Key Entities *(include if feature involves data)*

- **Event Envelope**: A single reporting message containing exactly one lifecycle or diagnostic payload.
- **Lifecycle Event**: A run-, scenario-, or step-level start/finish record with status and timing metadata.
- **Correlation Identifier**: A stable identifier linking related lifecycle events and attachments across one execution attempt.
- **Event Stream Validation Result**: Validation output describing completeness, ordering, and consistency of a produced message stream.
- **Implementation Status**: The governance status assigned to a status-capable message (`done`, `non-implementable`, `not-acceptable`).
- **Implementation Comment**: Structured rationale text attached to non-success statuses and optionally to `done`.
- **Status Applicability Matrix**: Canonical map that defines whether each in-scope message type requires, optionally allows, or forbids status/comment fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of validated reporting runs (pass, fail, and missing-step/error scenarios) produce parseable message streams with no schema violations.
- **SC-002**: For validated runs, 100% of scenarios have exactly one start and one finish lifecycle event, and 100% of executed steps have exactly one start and one finish lifecycle event.
- **SC-003**: Consistency validation reports 0 orphan references and 0 duplicate lifecycle identifiers across the supported validation matrix.
- **SC-004**: Static type validation reports 0 message-construction type errors in scope, and intentionally seeded invalid message assignments are detected as failures.
- **SC-005**: 100% of downstream compatibility checks in scope consume emitted message streams without requiring case-specific normalization for inconsistent event shape.
- **SC-006**: In validation runs, 100% of scenario report, gherkin terminal output, and cucumber JSON output entries match the canonical event stream for status, step outcome, and scenario identifier.
- **SC-007**: 100% of message-validation tests in scope pass against the latest supported message protocol version.
- **SC-008**: Prerequisite validation returns exactly one specification directory for the active feature prefix in 100% of verification runs after conflict cleanup.
- **SC-009**: In CI validation, targeted reporting suite runtime with reporting enabled remains within <=10% wall-clock overhead of reporting-disabled baseline.
- **SC-010**: 100% of in-scope envelope message types have documented governance classification (required/optional/not applicable) for implementation status/comment fields.
- **SC-011**: 100% of emitted status values in scope are one of `done`, `non-implementable`, or `not-acceptable`, and 100% of invalid/custom statuses are rejected by validation.
- **SC-012**: 100% of messages with `non-implementable` or `not-acceptable` statuses include a non-empty implementation comment.
- **SC-013**: 0 scenario attempts in the validation matrix contain conflicting terminal statuses after stream validation.
- **SC-014**: 100% of validated runs containing at least one `not-acceptable` status are marked as promotion-blocked by release governance checks.
- **SC-015**: 100% of required status-capable message types (`test_step_finished`, `test_case_finished`) include both status and applicable comment fields in validation runs.
- **SC-016**: 100% of status-capable message records in validation runs include required observability fields (`scenario_attempt_id`, `payload_kind`, `implementation_status`, `comment_present`, `hook_origin`).
