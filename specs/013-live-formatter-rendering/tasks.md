# Tasks: Live Formatter Rendering

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/`
**Prerequisites**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/plan.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/spec.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/research.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/data-model.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/contracts/`

**Tests**: Validation-first delivery is required by the constitution and the feature specification. This task list includes contract, compatibility, hook, e2e, model, and documentation-backed regressions before implementation tasks.

**Organization**: Tasks are grouped by user story so each story remains independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when tasks touch different files and do not depend on incomplete work
- **[Story]**: Maps a task to a specific user story (`[US1]`, `[US2]`)
- Include exact file paths in every task description

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the architectural scaffolding, contract fixtures, and runtime asset layout required by the updated design

- [X] T001 Mirror the updated architecture contracts into repository-stable fixtures in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/fixtures/live_reporting_plugin_boundary.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/fixtures/xdist_live_reporting_boundary.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/fixtures/xdist_worker_controller_boundary.md`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/fixtures/standalone_rendering_boundary.md`
- [X] T002 [P] Create explicit reporter lifecycle and assembly scaffolding in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/runtime_contract.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T003 [P] Create standalone replay service scaffolding in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/render_cucumber_formatters.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_formatter_support/standalone.py`
- [X] T004 [P] Prepare formatter-owned runtime asset scaffolding in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_formatter_support/base.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/live_formatter_bridge.mjs.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatter_adapter_support.cjs.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatters/progress.cjs.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatters/progress_bar.cjs.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatters/pretty.cjs.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatters/junit.cjs.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatters/usage.cjs.j2`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/setup.cfg`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Put boundary tests, canonical discovery, and explicit lifecycle wiring in place before any story work begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Add contract coverage for the explicit lifecycle contract and standalone rendering boundary in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_cucumber_formatter_cli_contract.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_worker_controller_boundary_contract.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_consolidated_stream_contract.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_standalone_rendering_boundary_contract.py`
- [X] T006 [P] Add hook and runtime guardrails for the narrow coordination root and explicit collaborator wiring in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_gherkin_reporter_context_lifecycle.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_reporting_context_snapshot_unit.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_live_formatter_output_relay.py`
- [X] T007 [P] Add compatibility and model guardrails for formatter-owned behavior and canonical discovery policy in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_render_cucumber_formatters.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/model/test_cucumber_formatter_adapter.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_message_emission_points.py`
- [X] T008 [P] Establish canonical formatter discovery and option metadata surfaces in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/pyproject.toml`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_formatter_support/registry.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_formatter_support/standalone.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/util/cucumber_formatters.py`
- [X] T009 Wire the explicit reporter lifecycle contract between the pytest entrypoint and the coordination root in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/runtime_contract.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`

**Checkpoint**: Contract fixtures, discovery policy, and explicit lifecycle boundaries are ready for story implementation.

---

## Phase 3: User Story 1 - See live formatter updates during a run (Priority: P1) 🎯 MVP

**Goal**: Users see trustworthy live formatter output during standard runs through a narrow reporter root, explicit lifecycle contract, formatter-owned behavior, and a first-class standalone replay service.

**Independent Test**: Start a long-running standard run with a supported formatter and confirm visible formatter output appears before completion, the entrypoint uses only the public runtime lifecycle contract, standalone replay works without synthetic pytest runtime objects, and formatter-specific behavior is owned by formatter plugins rather than a monolithic support layer.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Add single-process contract and lifecycle regressions for the narrow coordination root in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_cucumber_formatter_cli_contract.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_gherkin_reporter_context_lifecycle.py`
- [X] T011 [P] [US1] Add standalone replay and compatibility regressions for the first-class rendering service in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_render_cucumber_formatters.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_standalone_rendering_boundary_contract.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/model/test_cucumber_formatter_adapter.py`
- [X] T012 [P] [US1] Add local live e2e and documentation-backed regressions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters_feature.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_report_doc_cucumber_formatters.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/doc/test_cucumber_formatter_report_doc_parse.py`

### Implementation for User Story 1

- [X] T013 [US1] Extract reporter assembly and formatter request resolution out of the coordination root in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/session.py`
- [X] T014 [US1] Shrink `plugin.py` to the public coordination surface and implement the explicit lifecycle contract in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/runtime_contract.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`
- [X] T015 [US1] Replace reporter-backed sibling service access with explicit collaborator wiring in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/service_base.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py`
- [X] T016 [US1] Implement the first-class standalone rendering service and CLI boundary in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/render_cucumber_formatters.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/cucumber_formatter_adapter.py`
- [X] T017 [US1] Move formatter-specific request-building and runtime-asset behavior into top-level formatter plugins in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_summary.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_progress.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_progress_bar.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_pretty.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_json_formatter.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_junit.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_usage.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_usage_json.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_snippets.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_formatter_support/base.py`
- [X] T018 [US1] Remove supported package-scan fallback and align runtime and replay discovery with canonical catalogs in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_formatter_support/registry.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_formatter_support/standalone.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/util/cucumber_formatters.py`
- [X] T019 [US1] Reconcile live bridge asset rendering with formatter-owned modules and restore the single-process acceptance sweep in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/live_formatter_bridge.mjs.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_e2e.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_e2e_inventory.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_e2e_no_duplicates.py`

**Checkpoint**: User Story 1 is complete when standard runs render through the narrowed runtime contract, standalone replay is a first-class service, formatter-specific behavior is owned by formatter plugins, and supported local paths no longer depend on package-scan discovery.

---

## Phase 4: User Story 2 - Keep distributed live reporting centralized (Priority: P2)

**Goal**: Distributed runs keep live formatter rendering centralized on the controller/main authority while preserving the same explicit runtime contract, narrow service boundaries, formatter-owned behavior, and canonical discovery policy.

**Independent Test**: Start a distributed multi-worker run with a live-capable formatter and confirm worker messages are relayed to one reporting authority, only that authority renders output, worker bootstrap does not require standalone-style synthetic pytest runtime emulation, and distributed rendering stays aligned with the explicit lifecycle contract.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T020 [P] [US2] Add xdist contract and transport regressions for the explicit lifecycle contract and controller-only rendering in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_worker_controller_boundary_contract.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_consolidated_stream_contract.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py`
- [X] T021 [P] [US2] Add distributed hook and e2e regressions for centralized live formatter ownership in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_live_formatter_output_relay.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_message_aggregation.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py`
- [X] T022 [P] [US2] Add xdist documentation and html-report coverage for the narrowed runtime architecture in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_html_reporting.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/_xdist_html_reporting.feature`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_e2e_classification.py`

### Implementation for User Story 2

- [X] T023 [US2] Route xdist controller and worker runtime through the explicit lifecycle contract in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd_worker_bootstrap/xdist_remote.py`
- [X] T024 [US2] Preserve controller-owned stream consolidation and duplicate-safe rendering in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_transport.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/message_consolidation.py`
- [X] T025 [US2] Align distributed formatter session and asset preparation with explicit collaborators in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/session.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py`
- [X] T026 [US2] Update remote acceptance fixtures and shared support for the standalone-free worker path in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/support/cucumber_formatters.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/support/templates/fake_node_runtime.py.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/support/templates/fake_npm_runtime.py.j2`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/cucumber_formatter_support.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/docker_support.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/controller_entrypoint.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/worker_entrypoint.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/fixtures/remote_xdist/verify_report.py`
- [X] T027 [US2] Restore distributed acceptance and inventory sweeps under the new runtime boundaries in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_e2e.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_e2e_inventory.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_html_reporting.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py`

**Checkpoint**: User Story 2 is complete when distributed runs forward live batches through the explicit runtime contract, render once on the controller/main authority, and keep workers free of standalone-style synthetic runtime emulation.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Align docs, planning evidence, and final validation with the narrowed runtime architecture

- [X] T028 [P] Update user-facing and internal docs for the explicit lifecycle and JS runtime architecture in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/07 Report/09 Cucumber formatter reports.feature.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/07 Report/07 xdist HTML reporting.feature.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/07 Report/08 xdist remote network reporting.feature.md`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/docs/internal/cucumber-formatter-runtime-architecture.rst`
- [X] T029 [P] Refresh feature planning evidence and boundary docs for `FR-016` through `FR-021` in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/research.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/data-model.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/quickstart.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/contracts/live-reporting-plugin-boundary.md`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/contracts/standalone-rendering-boundary.md`
- [X] T030 Run the quickstart and tox validation slices for the narrowed runtime architecture and record final evidence in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/013-live-formatter-rendering/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion and extends the runtime proven in User Story 1
- **Polish (Phase 5)**: Depends on both user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2 and delivers the MVP path for local live rendering, explicit lifecycle wiring, standalone replay boundary, formatter-owned behavior, and canonical discovery policy
- **User Story 2 (P2)**: Starts after Phase 2, but should land after User Story 1 because it extends the same runtime contract to distributed controller-owned execution

### Within User Story 1

- Tests in `T010`-`T012` must be written and failing before `T013`-`T019`
- `T013` depends on `T002`, `T008`, and `T009`
- `T014` depends on `T005`, `T009`, and `T013`
- `T015` depends on `T006` and `T014`
- `T016` depends on `T003`, `T005`, `T011`, and `T014`
- `T017` depends on `T004`, `T007`, and `T014`
- `T018` depends on `T008`, `T016`, and `T017`
- `T019` depends on `T012`, `T016`, `T017`, and `T018`

### Within User Story 2

- Tests in `T020`-`T022` must be written and failing before `T023`-`T027`
- `T023` depends on `T009`, `T014`, and `T020`
- `T024` depends on `T015`, `T020`, and `T023`
- `T025` depends on `T013`, `T017`, `T021`, and `T024`
- `T026` depends on `T003`, `T016`, `T021`, and `T024`
- `T027` depends on `T022`, `T024`, `T025`, and `T026`

### Parallel Opportunities

- `T002`, `T003`, and `T004` can run in parallel after `T001`
- `T006`, `T007`, and `T008` can run in parallel after `T005`
- `T010`, `T011`, and `T012` can run in parallel once Phase 2 completes
- `T020`, `T021`, and `T022` can run in parallel once User Story 1 is stable
- `T028` and `T029` can run in parallel after `T027`

---

## Parallel Example: User Story 1

```bash
# Launch the User Story 1 regression tasks together:
Task: "Add single-process contract and lifecycle regressions for the narrow coordination root in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_cucumber_formatter_cli_contract.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_gherkin_reporter_context_lifecycle.py"
Task: "Add standalone replay and compatibility regressions for the first-class rendering service in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_render_cucumber_formatters.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_standalone_rendering_boundary_contract.py, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/model/test_cucumber_formatter_adapter.py"
Task: "Add local live e2e and documentation-backed regressions in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters_feature.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_report_doc_cucumber_formatters.py, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/doc/test_cucumber_formatter_report_doc_parse.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch the User Story 2 regression tasks together:
Task: "Add xdist contract and transport regressions for the explicit lifecycle contract and controller-only rendering in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_worker_controller_boundary_contract.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_consolidated_stream_contract.py, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/messages/test_xdist_remote_transport.py"
Task: "Add distributed hook and e2e regressions for centralized live formatter ownership in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_live_formatter_output_relay.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_message_aggregation.py, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_remote_message_aggregation.py"
Task: "Add xdist documentation and html-report coverage for the narrowed runtime architecture in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_html_reporting.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/_xdist_html_reporting.feature, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_e2e_classification.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run the single-process contract, hook, replay, and documentation-backed slices for User Story 1
5. Only after User Story 1 passes, continue to distributed controller-owned rendering

### Incremental Delivery

1. Build the explicit lifecycle, assembly, standalone replay, and formatter-asset scaffolding
2. Deliver User Story 1 as the MVP path for local live rendering plus standalone replay under the narrowed architecture
3. Extend that runtime contract to controller-owned distributed rendering in User Story 2
4. Finish by aligning docs, planning evidence, and final regression notes with the new architecture

### Suggested MVP Scope

- `T001`-`T019` only
- This delivers the full P1 story plus the shared guardrails for `FR-016` through `FR-021`

---

## Notes

- `[P]` tasks touch disjoint files and can proceed concurrently
- `[US1]` and `[US2]` labels map tasks directly to independently testable story increments
- The task list explicitly enforces `FR-016`, `FR-017`, `FR-018`, `FR-019`, `FR-020`, and `FR-021`
- Contract, compatibility, hook, e2e, model, and documentation-backed validation are part of the delivery path, not optional cleanup
