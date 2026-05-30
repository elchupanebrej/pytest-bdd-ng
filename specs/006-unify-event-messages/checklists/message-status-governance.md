<!-- markdownlint-disable MD013 -->

# Message Status Governance Checklist: Unify Event Message Reporting

**Purpose**: Validate whether requirements clearly and completely define implementation-status message taxonomy, hook-formation comments, downstream status consistency, and release-governance expectations.
**Created**: 2026-02-25
**Feature**: [spec.md](../spec.md)

**Note**: This checklist evaluates requirements quality only (completeness, clarity, consistency, measurability, and coverage), not implementation behavior.

## Requirement Completeness

- [X] CHK001 Are implementation-status categories fully defined (including `done`, `non-implementable`, `not-acceptable`), with explicit extensibility and fallback rules? [Completeness, Spec §FR-002, Gap]
- [X] CHK002 Are status-bearing message types enumerated for all relevant lifecycle envelopes and diagnostics? [Completeness, Spec §FR-001, Spec §FR-005, Contract §components.schemas.EventEnvelope]
- [X] CHK003 Are requirements explicit about which hook formation points must attach implementation comments to status-bearing messages? [Completeness, Spec §FR-006, Tasks §T020/T036, Gap]
- [X] CHK004 Are comment-presence rules defined per status class (for example, mandatory rationale for `non-implementable`/`not-acceptable`)? [Completeness, Spec §FR-013, Gap]
- [X] CHK005 Are downstream representation requirements defined for status/comment data in scenario, terminal, and JSON outputs? [Completeness, Spec §FR-011, Spec §FR-014, Contract §/reporting/reports/derive]

## Requirement Clarity

- [X] CHK006 Is the distinction between `non-implementable` and `not-acceptable` defined with objective decision criteria? [Clarity, Ambiguity, Gap]
- [X] CHK007 Are fallback-status trigger conditions explicit for unknown, conflicting, or unmapped statuses? [Clarity, Spec §FR-002, Spec §FR-008, Gap]
- [X] CHK008 Is “implementation comment” specified as structured requirement content (fields/semantics) rather than unconstrained free text? [Clarity, Ambiguity, Gap]
- [X] CHK009 Are hook-formation locations named using stable hook/event identifiers instead of informal wording? [Clarity, Spec §FR-006, Tasks §T020/T036]
- [X] CHK010 Are requirement verbs for status operations (“set”, “derive”, “override”, “fallback”) defined consistently and unambiguously? [Clarity, Spec §FR-007, Ambiguity]

## Requirement Consistency

- [X] CHK011 Do status-taxonomy requirements align with contract schemas without contradiction between extensible statuses and validation constraints? [Consistency, Conflict, Spec §FR-002, Contract §components.schemas]
- [X] CHK012 Are emission-failure requirements consistent with status/comment requirements when reporting is enabled versus disabled? [Consistency, Spec §FR-013, Spec §FR-014]
- [X] CHK013 Do canonical-source requirements remain consistent with derived-output requirements (no parallel status-construction path)? [Consistency, Spec §FR-011, Spec §FR-014]
- [X] CHK014 Is spec-prefix governance terminology consistent with message-status terminology so “status” semantics are not overloaded? [Consistency, Spec §FR-016, Spec §FR-017, Contract §/governance/spec-prefix/audit]

## Acceptance Criteria Quality

- [X] CHK015 Are acceptance criteria measurable for status coverage across run/scenario/step lifecycle scopes? [Acceptance Criteria, Spec §SC-001, Spec §SC-002]
- [X] CHK016 Are measurable criteria defined for missing-required-comment defects in status-bearing messages? [Measurability, Spec §SC-003, Gap]
- [X] CHK017 Are measurable criteria defined for fallback-status usage and acceptable thresholds? [Measurability, Gap]
- [X] CHK018 Are release-gate requirements measurable for blocking/promoting artifacts when `not-acceptable` statuses are present? [Acceptance Criteria, Gap, Audience]

## Scenario Coverage

- [X] CHK019 Are primary-flow requirements defined for `done` statuses from hook formation to derived outputs? [Coverage, Spec §US1, Spec §US2]
- [X] CHK020 Are alternate-flow requirements defined for extensible custom statuses that still resolve through canonical/fallback mapping? [Coverage, Spec §FR-002, Spec §FR-015]
- [X] CHK021 Are exception-flow requirements defined for contradictory statuses emitted for a single scenario attempt? [Coverage, Exception Flow, Spec §FR-008, Gap]
- [X] CHK022 Are recovery-flow requirements defined for retry/re-execution status reclassification while preserving auditability? [Coverage, Recovery Flow, Spec §FR-012, Edge Case]
- [X] CHK023 Are non-functional scenario requirements defined for parallel-worker ordering integrity of status/comment records? [Coverage, Non-Functional, Spec §FR-007, Spec §FR-012]

## Edge Case Coverage

- [X] CHK024 Are boundary requirements defined for absent or empty implementation comments on failure-class statuses? [Edge Case, Gap, Spec §FR-006]
- [X] CHK025 Are requirements defined for oversized, multi-line, or sensitive implementation comments (including truncation/redaction expectations)? [Edge Case, Non-Functional, Gap]
- [X] CHK026 Are requirements defined for attachment/diagnostic messages that have status context but incomplete step correlation? [Edge Case, Spec §FR-006, Spec §FR-008]
- [X] CHK027 Are requirements defined for multi-conflict prefix remediation when more than one numeric prefix collision exists simultaneously? [Edge Case, Spec §FR-016, Contract §SpecPrefixConflict]

## Non-Functional Requirements

- [X] CHK028 Are observability requirements specified for status/comment lifecycle records (audit fields, identifiers, and traceability expectations)? [Non-Functional, Spec §FR-012, Spec §SC-003, Gap]
- [X] CHK029 Are reliability requirements specified for preserving status/comment integrity across async queue/thread boundaries? [Non-Functional, Spec §FR-007, Plan §Technical Context]
- [X] CHK030 Are security/privacy requirements specified for implementation comments that may contain internal-sensitive reasoning? [Non-Functional, Gap, Assumption]

## Dependencies & Assumptions

- [X] CHK031 Are dependencies on latest protocol fields for status/comment representation explicitly documented and bounded? [Dependency, Spec §FR-015, Assumption]
- [X] CHK032 Are assumptions about hook availability/ordering across pytest/pluggy versions documented with validation expectations? [Assumption, Plan §Technical Context, Gap]
- [X] CHK033 Are script-governance dependencies (`common.sh`, `check-prerequisites.sh`, `create-new-feature.sh`) traced to acceptance outcomes? [Dependency, Tasks §T010-T012, Spec §SC-008]

## Ambiguities & Conflicts

- [X] CHK034 Is ownership of status assignment versus comment authoring at hook formation explicitly defined? [Ambiguity, Gap]
- [X] CHK035 Do requirements resolve potential conflict between extensible statuses and deterministic consumer expectations? [Conflict, Spec §FR-002, Spec §SC-005]
- [X] CHK036 Is a canonical glossary for status names/severity levels defined to prevent synonym drift across spec/plan/tasks/contracts? [Traceability, Gap, Consistency]

## Message Inventory (Implementation Coverage)

- [X] `meta` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `source` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `gherkin_document` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `pickle` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `step_definition` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `parameter_type` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_parameter_type_messages`.
- [X] `hook` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_hook_type_messages`.
- [X] `test_run_started` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `test_case` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `test_case_started` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `test_step_started` (`not applicable`) mapped in `src/pytest_bdd/model/message_extension.py` and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `test_step_finished` (`required`) mapped in `src/pytest_bdd/model/message_extension.py`, validated in `src/pytest_bdd/model/message_validation.py`, and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `test_case_finished` (`required`) mapped in `src/pytest_bdd/model/message_extension.py`, validated in `src/pytest_bdd/model/message_validation.py`, and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `test_run_finished` (`optional`) mapped in `src/pytest_bdd/model/message_extension.py`, validated in `src/pytest_bdd/model/message_validation.py`, and covered by `tests/messages/test_messages.py::test_minimal_scenario_messages`.
- [X] `attachment` (`optional`) mapped in `src/pytest_bdd/model/message_extension.py`, validated in `src/pytest_bdd/model/message_validation.py`, and covered by `tests/messages/test_message_attachments.py::test_attachment_messages_are_correlated_to_active_step`.
