<!-- markdownlint-disable MD013 -->

# Tasks: Unify Event Message Reporting

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/event-message-reporting.openapi.yaml`, `quickstart.md`
**Language**: English (all task descriptions and notes)

**Tests**: Test tasks are included because the specification defines explicit independent test criteria and measurable validation outcomes for each user story.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare reusable validation scaffolding for message/reporting and prefix-governance work.

- [X] T001 Create shared message stream assertion helpers in `tests/messages/message_stream_assertions.py`
- [X] T002 [P] Create contract test scaffold for reporting operations in `tests/contract/test_event_message_reporting_contract.py`
- [X] T003 [P] Create prerequisite prefix-resolution regression test scaffold in `tests/scripts/test_spec_prefix_resolution.py`
- [X] T004 [P] Create MyPy regression fixture module for invalid envelope assignments in `tests/messages/test_message_typing_regression.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared primitives required by all user stories.

**⚠️ CRITICAL**: No user story implementation should start before this phase is complete.

- [X] T005 Implement typed `EventEnvelope` and lifecycle correlation helpers in `src/pytest_bdd/model/message_extension.py`
- [X] T006 [P] Implement stream consistency validator primitives in `src/pytest_bdd/model/message_validation.py`
- [X] T007 [P] Export message validation utilities in `src/pytest_bdd/model/__init__.py`
- [X] T008 Implement canonical envelope emission helpers (`_emit_envelope`, `_emit_lifecycle`) in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T009 Implement attempt-level correlation state (`scenario_attempt_id`, `attempt_index`, `worker_id`) in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T010 Implement deterministic prefix-conflict discovery helpers in `.specify/scripts/bash/common.sh`
- [X] T011 Implement monotonic-prefix guard for new feature creation in `.specify/scripts/bash/create-new-feature.sh`
- [X] T012 Implement conflict-audit JSON payload support in `.specify/scripts/bash/check-prerequisites.sh`

**Checkpoint**: Canonical message primitives, correlation state, and prefix-governance foundations are ready.

---

## Phase 3: User Story 1 - Emit Canonical Lifecycle Messages (Priority: P1) 🎯 MVP

**Goal**: Emit complete, correlated run/scenario/step lifecycle events with canonical envelopes.

**Independent Test**: Run one passing and one failing scenario with message output enabled and verify complete lifecycle coverage with valid references.

### Tests for User Story 1

- [X] T013 [P] [US1] Add failing lifecycle count/order assertions for pass/fail runs in `tests/messages/test_messages.py`
- [X] T014 [P] [US1] Add failing missing-step and failed-step completion assertions in `tests/feature/test_report.py`
- [X] T015 [P] [US1] Add failing attachment correlation assertions in `tests/messages/test_message_attachments.py`

### Implementation for User Story 1

- [X] T016 [US1] Refactor lifecycle emission to canonical helper flow in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T017 [US1] Enforce single-payload envelope construction guards in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T018 [US1] Implement attachment-to-active-scope correlation mapping in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T019 [US1] Implement emission failure policy switch based on reporting-enabled options in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T020 [US1] Tighten message hook payload typing for canonical envelope emission in `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py`
- [X] T021 [US1] Align parse/serialize validation with canonical envelope checks in `src/pytest_bdd/model/message_converter.py`

**Checkpoint**: US1 lifecycle emission is complete and independently testable.

---

## Phase 4: User Story 2 - Eliminate Inconsistent Event Shapes and Ordering (Priority: P2)

**Goal**: Guarantee deterministic stream shape/order and ensure legacy/user-facing outputs derive from canonical events.

**Independent Test**: Validate pass/fail/missing-step streams for zero orphan/duplicate lifecycle references and verify rendered outputs match canonical stream outcomes.

### Tests for User Story 2

- [X] T022 [P] [US2] Add failing stream-validation contract assertions for `/reporting/messages/validate` in `tests/contract/test_event_message_reporting_contract.py`
- [X] T023 [P] [US2] Add failing derived-output consistency assertions for terminal rendering in `tests/feature/test_gherkin_terminal_reporter.py`
- [X] T024 [P] [US2] Add failing duplicate-prefix prerequisite regression tests in `tests/scripts/test_spec_prefix_resolution.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement canonical-to-legacy scenario report derivation path in `src/pytest_bdd/plugin/scenario_reporter/plugin.py`
- [X] T026 [US2] Update scenario serialization to consume canonical lifecycle status/duration mappings in `src/pytest_bdd/plugin/scenario_reporter/report.py`
- [X] T027 [US2] Update terminal reporter rendering to consume canonical-derived statuses in `src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py`
- [X] T028 [US2] Implement orphan/duplicate/out-of-order lifecycle checks in `src/pytest_bdd/model/message_validation.py`
- [X] T029 [US2] Integrate stream validation and derived-output consistency checks in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T030 [US2] Add `/governance/spec-prefix/audit` contract verification coverage in `tests/contract/test_event_message_reporting_contract.py`
- [X] T031 [US2] Document prefix-conflict remediation workflow in `specs/006-unify-event-messages/quickstart.md`

**Checkpoint**: US2 stream consistency and output derivation are complete and independently testable.

---

## Phase 5: User Story 3 - Enforce Type-Validated Message Construction (Priority: P3)

**Goal**: Ensure message-construction paths fail static typing when invalid fields or incompatible payload shapes are introduced.

**Independent Test**: Run MyPy workflow and verify message-construction modules pass; seeded invalid assignments must fail.

### Tests for User Story 3

- [X] T032 [P] [US3] Add failing MyPy regression case for invalid envelope field assignment in `tests/messages/test_message_typing_regression.py`
- [X] T033 [P] [US3] Add failing typing guard assertions for message hook signatures in `tests/hook/test_hook.py`

### Implementation for User Story 3

- [X] T034 [US3] Remove message-construction `type: ignore` suppressions that mask invalid fields in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T035 [US3] Add strict typed aliases for envelope/lifecycle payloads in `src/pytest_bdd/model/message_extension.py`
- [X] T036 [US3] Tighten message hook spec typing for `pytest_bdd_message` payloads in `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py`
- [X] T037 [US3] Update MyPy coverage for message-reporter modules in `pyproject.toml`
- [X] T038 [US3] Add explicit MyPy tox invocation for message-reporter scope in `tox.ini`
- [X] T039 [US3] Update message parsing tests for stricter type expectations in `tests/messages/test_messages.py`

**Checkpoint**: US3 static type validation is complete and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation evidence, documentation updates, and traceability checks across all stories.

- [X] T040 [P] Run targeted message/reporting pytest suites and record command results in `specs/006-unify-event-messages/quickstart.md`
- [X] T041 [P] Run `conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-mypy` and record results in `specs/006-unify-event-messages/quickstart.md`
- [X] T042 [P] Run `conda run -n pytest-bdd-ng-py314 pre-commit run --all-files` and record results in `specs/006-unify-event-messages/quickstart.md`

> Current workflow:
> T041 equivalent: run `uvx --with tox-uv tox -e py314-pytestlatest-mypy` and record results in `specs/006-unify-event-messages/quickstart.md`.
> T042 equivalent: run `uvx pre-commit run --all-files` and record results in `specs/006-unify-event-messages/quickstart.md`.

- [X] T043 [P] Update canonical-event derivation behavior docs in `docs/features/Report/Gherkin terminal reporter.feature.rst`
- [X] T044 [P] Update canonical-event derivation behavior docs in `docs/features/Report/Cucumber JSON reporter.feature.rst`
- [X] T045 Verify task-to-requirement traceability notes in `specs/006-unify-event-messages/tasks.md`
- [X] T046 [P] Add canonical-vs-derived JSON status/outcome parity assertions in `tests/feature/test_cucumber_json.py`
- [X] T047 [P] Add unsupported protocol version rejection coverage in `tests/contract/test_event_message_reporting_contract.py`
- [X] T048 [P] Add protocol-version rejection validator coverage in `src/pytest_bdd/model/message_validation.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2 and canonical emission baseline from US1.
- **Phase 5 (US3)**: Depends on Phase 3 and Phase 4.
- **Phase 6 (Polish)**: Depends on all user stories being complete.

### User Story Dependency Graph

- **US1 (P1)**: Starts after Foundational phase.
- **US2 (P2)**: Starts after Foundational phase and stabilizes against US1 canonical stream.
- **US3 (P3)**: Starts after US1+US2 integration points are in place.

Graph: `Foundational -> US1 -> US2 -> US3`

### Within Each User Story

- Test tasks are written first and should fail before implementation.
- Canonical model/validation updates precede reporter integration wiring.
- Story-level validation passes before moving to next priority scope.

---

## Parallel Execution Examples

### User Story 1

```bash
Task T013 in tests/messages/test_messages.py
Task T014 in tests/feature/test_report.py
Task T015 in tests/messages/test_message_attachments.py
```

### User Story 2

```bash
Task T022 in tests/contract/test_event_message_reporting_contract.py
Task T023 in tests/feature/test_gherkin_terminal_reporter.py
Task T024 in tests/scripts/test_spec_prefix_resolution.py
```

### User Story 3

```bash
Task T032 in tests/messages/test_message_typing_regression.py
Task T033 in tests/hook/test_hook.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate canonical lifecycle emission independently before expanding scope.

### Incremental Delivery

1. Deliver US1 (canonical lifecycle emission).
2. Deliver US2 (shape/order consistency + derived outputs + prefix governance checks).
3. Deliver US3 (MyPy-enforced message construction).
4. Complete Phase 6 cross-cutting verification and documentation updates.

### Parallel Team Strategy

1. Complete Setup + Foundational together.
2. Execute US1 test/implementation while another contributor starts US2 contract/prefix tests.
3. Integrate US2 after canonical US1 baseline is stable, then complete US3 typing hardening.

---

## Notes

- `[P]` tasks touch separate files and can run in parallel.
- `[US1]`, `[US2]`, `[US3]` labels map tasks directly to user stories.
- Every task includes an explicit file path for immediate execution.
- Commit with task IDs in commit messages per constitution requirements.
- Run pre-commit and resolve all issues before each commit.
- For non-native platform test environments, use the Docker skill (Windows targets are exempt).
- Traceability:
  FR-001..FR-014 are primarily covered by T005-T031 and T040.
  FR-015/FR-020 protocol and status-governance constraints are covered by T022, T032, T039, T047, T048.
  FR-016..FR-017 spec-prefix governance is covered by T010-T012, T024, T030, T031.
  SC-001..SC-016 validation outcomes are captured by T040-T042 and targeted test additions in T013-T039, T046-T048.
