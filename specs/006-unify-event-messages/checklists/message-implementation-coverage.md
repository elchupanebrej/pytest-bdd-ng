# Message Implementation Coverage Checklist: Unify Event Message Reporting

**Purpose**: Validate that requirements clearly define complete coverage for all in-scope message types and make "every message is implemented" objectively reviewable in PRs.
**Created**: 2026-02-25
**Feature**: [spec.md](../spec.md)

**Note**: This checklist validates requirement quality only (completeness, clarity, consistency, measurability, and coverage), not runtime behavior.

## Requirement Completeness

- [ ] CHK001 Are all 15 in-scope message types explicitly listed in one authoritative requirement without aliases? [Completeness, Spec §FR-018]
- [ ] CHK002 Are status/comment applicability rules defined for every listed type as required, optional, or not applicable? [Completeness, Spec §FR-019, Spec §FR-024]
- [ ] CHK003 Are required status/comment fields defined for each status-capable type rather than implied globally? [Completeness, Spec §FR-024, Spec §FR-028]
- [ ] CHK004 Are downstream representation requirements defined for status/comment semantics in scenario, terminal, and JSON outputs? [Completeness, Spec §FR-014, Spec §FR-027]
- [ ] CHK005 Are explicit exclusion requirements documented for not-applicable message types to avoid inferred status behavior? [Completeness, Spec §FR-024]

## Requirement Clarity

- [ ] CHK006 Is the term "in-scope envelope message type" defined consistently across spec, plan, and tasks? [Clarity, Spec §FR-018, Plan §Constraints, Tasks §T005-T009]
- [ ] CHK007 Are classification criteria for required/optional/not applicable objective and non-overlapping? [Clarity, Spec §FR-019, Spec §FR-024]
- [ ] CHK008 Is "every message implemented" translated into measurable requirement language rather than broad prose? [Clarity, Spec §SC-010, Spec §SC-015, Gap]
- [ ] CHK009 Are unknown or custom status rules explicitly defined as rejection behavior with no fallback remapping? [Clarity, Spec §FR-020, Contract §components.schemas.MessageValidationViolation]
- [ ] CHK010 Is "non-empty implementation comment" defined precisely enough to avoid whitespace-only ambiguity? [Clarity, Spec §FR-022, Gap]

## Requirement Consistency

- [ ] CHK011 Do message-type definitions align between spec requirements and contract enums with no missing or extra type names? [Consistency, Spec §FR-018, Contract §components.schemas.EventEnvelope]
- [ ] CHK012 Do status taxonomy constraints match between spec and contract without extensibility conflicts? [Consistency, Spec §FR-020, Contract §components.schemas.ImplementationStatus]
- [ ] CHK013 Do plan constraints about canonical-message ownership align with story tasks that implement coverage behavior? [Consistency, Plan §Constraints, Tasks §T016-T031]
- [ ] CHK014 Are optional status-capable types (`test_run_finished`, `attachment`) covered with equal requirement precision as required types? [Consistency, Spec §FR-024, Tasks §T018-T029, Gap]
- [ ] CHK015 Are release-governance blocking rules for `not-acceptable` status consistent between success criteria and contract outputs? [Consistency, Spec §FR-031, Spec §SC-014, Contract §components.schemas.MessageValidationResult]

## Acceptance Criteria Quality

- [ ] CHK016 Are success criteria measurable for 100% governance classification coverage across all in-scope message types? [Acceptance Criteria, Spec §SC-010]
- [ ] CHK017 Are success criteria measurable for required field presence on required status-capable message types? [Measurability, Spec §SC-015, Spec §SC-016]
- [ ] CHK018 Are success criteria measurable for invalid-status rejection and conflicting-status rejection outcomes? [Measurability, Spec §SC-011, Spec §SC-013]
- [ ] CHK019 Are acceptance outcomes traceable to specific requirement IDs instead of narrative-only wording? [Traceability, Spec §FR-018-FR-031, Gap]

## Scenario Coverage

- [ ] CHK020 Are primary-flow requirements defined for lifecycle message coverage from run start through run finish? [Coverage, Spec §US1, Spec §FR-003-FR-006]
- [ ] CHK021 Are alternate-flow requirements defined when optional status-capable message types include or omit comment/status fields? [Coverage, Spec §FR-024, Spec §FR-027]
- [ ] CHK022 Are exception-flow requirements defined for status/comment attached to a not-applicable message type? [Coverage, Spec §FR-025, Contract §components.schemas.MessageValidationViolation]
- [ ] CHK023 Are recovery-flow requirements defined for retries so each attempt has independently correlated status/comment records? [Coverage, Spec §FR-026, Spec §FR-012]

## Edge Case Coverage

- [ ] CHK024 Are boundary requirements defined for empty comments on failure-class statuses across all required status-capable types? [Edge Case, Spec §FR-022, Spec §FR-024]
- [ ] CHK025 Are multi-line comment handling requirements explicit without introducing hidden truncation/redaction behavior? [Edge Case, Spec §FR-030]
- [ ] CHK026 Are concurrency edge-case requirements explicit so parallel workers cannot break per-attempt message coverage integrity? [Edge Case, Spec §FR-029, Plan §Constraints]

## Non-Functional Requirements

- [ ] CHK027 Are observability requirements explicit for status-capable message records and their audit fields? [Non-Functional, Spec §FR-028, Spec §SC-016]
- [ ] CHK028 Are performance expectations quantified for message governance and coverage validation in PR review scope? [Non-Functional, Spec §NFR-001, Plan §Performance Goals]
- [ ] CHK029 Are comment-content privacy expectations explicitly captured as assumptions rather than implied behavior? [Non-Functional, Assumption, Spec §Assumptions, Spec §FR-030]

## Dependencies & Assumptions

- [ ] CHK030 Are latest-protocol-only dependencies explicitly bounded for all message-coverage requirements? [Dependency, Spec §FR-015, Contract §components.schemas.EmitMessagesRequest]
- [ ] CHK031 Are hook availability and ordering dependencies documented for each status/comment formation point? [Dependency, Spec §FR-023, Plan §Technical Context, Tasks §T020/T036]
- [ ] CHK032 Are spec-prefix governance assumptions separated from message-governance claims to avoid acceptance-scope drift? [Assumption, Spec §FR-016, Spec §FR-017, Spec §FR-018]

## Ambiguities & Conflicts

- [ ] CHK033 Is terminology consistent for "message type", "payload kind", and "envelope" across requirements and contract language? [Ambiguity, Spec §FR-018, Contract §components.schemas.EventEnvelope]
- [ ] CHK034 Do any requirements still imply fallback status mapping that conflicts with explicit rejection rules? [Conflict, Spec §FR-020, Spec §FR-025]
- [ ] CHK035 Are broad terms like "complete" and "consistent" tied to per-type measurable criteria? [Ambiguity, Spec §FR-010, Spec §SC-010, Gap]
- [ ] CHK036 Is ownership of status assignment and comment authorship unambiguous for each hook-formation path? [Clarity, Spec §FR-023, Tasks §T020/T036]

## Notes

- This checklist is for PR review of requirement quality.
- Mark items complete with `[x]` after requirement text is validated.
