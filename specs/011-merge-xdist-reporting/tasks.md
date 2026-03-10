<!-- markdownlint-disable MD013 -->

# Tasks: Distributed Reporting Stream

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/`
**Prerequisites**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/plan.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/spec.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/research.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/data-model.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/contracts/xdist-worker-controller-boundary.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/contracts/xdist-consolidated-stream.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/quickstart.md`
**Tests**: Included. The specification requires executable validation for local and remote xdist modes, and the constitution requires validation-first delivery for compatibility changes.
**Organization**: Tasks are grouped by user story so each story remains independently implementable and testable after the shared setup and foundational work.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Task can run in parallel with other `[P]` tasks when file ownership does not overlap.
- **[Story]**: User story label used only inside story phases (`[US1]`, `[US2]`, `[US3]`).
- Every task includes exact file paths for immediate execution.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare dependency, CI, and reusable remote-topology scaffolding shared by every story.

- [X] T001 Update distributed-reporting dependency floors for `pytest-xdist` and `execnet` in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/pyproject.toml`
- [X] T002 [P] Add Linux remote-topology tox entrypoints for `socket`, `via`, and `ssh` coverage in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tox.ini`
- [X] T003 [P] Add GitHub CI execution for the new remote tox coverage (using dockerized tests for xdist) in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.github/workflows/main.yml`
- [X] T004 [P] Prepare reusable remote-topology fixture assets and Python report verification (reducing bash dependencies) in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/docker-compose.yml`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/controller.Dockerfile`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/worker.Dockerfile`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/verify_report.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the xdist-native transport primitives and hook integration required by all user stories.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [X] T005 Create the project-local xdist remote-module adapter in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/xdist_remote.py`
- [X] T006 [P] Replace TCP-side transport models with execnet channel batch and worker-manifest models in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_transport.py`
- [X] T007 [P] Add reporter hook declarations and remote-module registration plumbing in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/hook.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`
- [X] T008 Implement controller-side compatibility detection, channel-event ingestion, and worker lifecycle plumbing in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T009 Implement execnet-serializable payload validation and fail-fast diagnostic helpers in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_validation.py`

**Checkpoint**: Shared xdist-native transport primitives are ready and story work can proceed.

---

## Phase 3: User Story 1 - Produce One Consolidated Run Stream (Priority: P1) 🎯 MVP

**Goal**: Deliver one controller-owned NDJSON stream for distributed runs over the existing xdist/execnet path across every supported gateway mode.

**Independent Test**: Run `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_message_aggregation.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py` and verify one final NDJSON stream for local `popen`, remote `socket`, proxy `via`, and remote `ssh` topologies without reading worker-local files.

### Tests for User Story 1

- [X] T010 [P] [US1] Add worker/controller boundary contract coverage for xdist-native channel transport, no side-channel fallback, and fail-fast compatibility in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_worker_controller_boundary_contract.py`
- [X] T011 [P] [US1] Add transport regressions for channel events, `workeroutput` manifests, and compatibility aborts in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py`
- [X] T012 [P] [US1] Add local and remote consolidated-stream end-to-end coverage in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_message_aggregation.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement worker-side reporting chunk publication and completion-manifest emission in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/xdist_remote.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_transport.py`
- [X] T014 [US1] Implement controller-side channel collection and final consolidated NDJSON emission in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T015 [US1] Implement Python-first remote acceptance orchestration and report verification (Python preferred over Bash) in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/verify_report.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/project/test_remote_aggregation.py`
- [X] T016 [US1] Keep remote socket, proxy `via`, and SSH shell wrappers strictly thin in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/controller-entrypoint.sh` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/worker-entrypoint.sh`

**Checkpoint**: Distributed runs produce one controller-owned NDJSON stream that is consumable without manual worker artifact merging.

---

## Phase 4: User Story 2 - Suppress Duplicated Collection Messages (Priority: P2)

**Goal**: Keep collection-time scenario and step structure singular across controller and workers in the final consolidated stream.

**Independent Test**: Run `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_message_consolidation.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_validation.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_messages_feature_suite.py` and verify one structural record per scenario and step.

### Tests for User Story 2

- [X] T017 [P] [US2] Add consolidated-stream contract coverage for structural payload classes, canonical IDs, and duplicate suppression rules in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_consolidated_stream_contract.py`
- [X] T018 [P] [US2] Add structural deduplication regressions for controller and worker collection payloads in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_message_consolidation.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py`
- [X] T019 [P] [US2] Add validation and report regressions for singular scenario and step counts in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_validation.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_messages_feature_suite.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement semantic structural identity derivation and canonical ID allocation in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_consolidation.py`
- [X] T021 [US2] Implement structural ID remap and runtime reference rewriting in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/execution_message_adapter.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_extension.py`
- [X] T022 [US2] Implement controller-side suppression of duplicate collection payloads during xdist consolidation in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/scenario_test_collector/plugin.py`
- [X] T023 [US2] Align validation rules with canonical structural counts and rewritten references in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_validation.py`

**Checkpoint**: The final stream contains one canonical structural view of the collected suite regardless of how many controller or worker participants observed it.

---

## Phase 5: User Story 3 - Keep Execution Messages Distinct and Traceable (Priority: P3)

**Goal**: Preserve every valid runtime event, keep execution attempts traceable after canonical remap, and surface partial-run diagnostics deterministically.

**Independent Test**: Run `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_message_consolidation.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_attachments.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py -k partial` and verify mixed outcomes, retries, attachments, and interrupted workers remain traceable in the final stream.

### Tests for User Story 3

- [X] T024 [P] [US3] Add consolidated-stream ordering and execution-preservation regressions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_consolidated_stream_contract.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_validation.py`
- [X] T025 [P] [US3] Add mixed-outcome, retry, and interrupted-worker regressions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_message_consolidation.py`
- [X] T026 [P] [US3] Add attachment traceability and partial-run acceptance regressions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_attachments.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement per-worker ordering and `ScenarioAttemptRecord` tracking in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_consolidation.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/scenario_run.py`
- [X] T028 [US3] Preserve execution envelopes, attachments, and worker or gateway traceability through canonical remap in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/execution_message_adapter.py`
- [X] T029 [US3] Implement partial-stream, interrupted-worker, and missing-manifest diagnostics in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_transport.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_validation.py`
- [X] T030 [US3] Update runtime traceability and outcome assertions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/message_stream_assertions.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_outcome_mapping.py`

**Checkpoint**: Execution events remain complete, ordered, traceable, and diagnostically useful after distributed consolidation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize documentation, validation evidence, and cross-story regression coverage.

- [X] T031 [P] Refresh feature documentation for GitHub CI validation and Python-first helper guidance in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/research.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/data-model.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/contracts/xdist-worker-controller-boundary.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/contracts/xdist-consolidated-stream.md`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/quickstart.md`
- [X] T032 Run focused pytest validation from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/011-merge-xdist-reporting/quickstart.md`
- [X] T033 Run tox remote matrix validation from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tox.ini` and pre-commit validation from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.pre-commit-config.yaml`
- [X] T034 Add an e2e test defined in `.feature` files presenting actual usage with pytest-xdist and HTML reporting from consolidated messages in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/xdist_html_reporting.feature` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_html_reporting.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 and delivers the MVP consolidated stream over xdist/execnet.
- **Phase 4 (US2)**: Depends on US1 because structural deduplication builds on the controller-owned consolidated stream.
- **Phase 5 (US3)**: Depends on US2 because runtime traceability and partial diagnostics rely on canonical structural remap behavior.
- **Phase 6 (Polish)**: Depends on all implemented stories.

### User Story Dependency Graph

```text
Setup -> Foundational -> US1 -> US2 -> US3 -> Polish
```

- **US1 (P1)**: Suggested MVP and first externally valuable increment.
- **US2 (P2)**: Adds structural correctness to the consolidated stream delivered by US1.
- **US3 (P3)**: Hardens runtime traceability, retries, attachments, and partial-run diagnostics on top of US1 and US2.

### Within Each User Story

- Test tasks should be written and observed failing before story implementation tasks.
- Shared model or transport changes land before plugin integration that depends on them.
- Story-level validation should pass before work advances to the next priority.

---

## Parallel Execution Examples

### User Story 1

```bash
Task T010 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_worker_controller_boundary_contract.py
Task T011 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py
Task T012 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_message_aggregation.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py
```

### User Story 2

```bash
Task T017 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_consolidated_stream_contract.py
Task T018 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_message_consolidation.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py
Task T019 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_validation.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_messages_feature_suite.py
```

### User Story 3

```bash
Task T024 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_consolidated_stream_contract.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_validation.py
Task T025 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_message_consolidation.py
Task T026 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_attachments.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py
```

### Setup and Foundational Work

```bash
Task T002 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tox.ini
Task T003 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.github/workflows/main.yml
Task T004 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/docker-compose.yml, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/controller.Dockerfile, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/worker.Dockerfile, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/verify_report.py
Task T006 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_transport.py
Task T007 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/hook.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate US1 independently across local and remote gateway modes before proceeding.

### Incremental Delivery

1. Deliver US1 to replace worker-artifact merging with one xdist-native consolidated stream.
2. Deliver US2 to remove duplicated structural payloads from that stream.
3. Deliver US3 to preserve execution traceability, retries, attachments, and partial-run diagnostics.
4. Finish with Phase 6 validation and documentation refresh.

### Parallel Team Strategy

1. Complete Setup and Foundational tasks together.
2. After Phase 2:
   - Engineer A can drive US1 channel transport and remote harness work.
   - Engineer B can prepare US2 contract and regression tests in parallel with late US1 implementation.
   - Engineer C can prepare US3 regression coverage once US2 canonical remap behavior stabilizes.

---

## Notes

- All tasks use the required checklist format: checkbox, task ID, optional `[P]`, optional story label, and exact file paths.
- Story labels appear only in user-story phases.
- Tasks are intentionally specific enough for direct execution by an LLM or engineer without additional planning context.
- Outside pytest hook implementations, implementation tasks must avoid introducing `None` return contracts; use explicit values or deterministic exceptions instead.
