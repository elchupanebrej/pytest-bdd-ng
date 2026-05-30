<!-- markdownlint-disable MD013 -->

# Tasks: Template-Driven Feature Documentation Ordering

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/`
**Prerequisites**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/plan.md` (required), `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/spec.md` (required), `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/research.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/data-model.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/contracts/feature-doc-ordering.openapi.yaml`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/quickstart.md`
**Language**: English (all task descriptions and notes)

**Tests**: Test tasks are included because the specification defines explicit independent test criteria and measurable validation outcomes, and the repository constitution requires executable validation for behavior changes.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare ordered-doc generation scaffolding, contract coverage, and template assets.

- [X] T001 Create ordered-doc contract regression scaffold in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_feature_doc_ordering_contract.py`
- [X] T002 Create ordered documentation regression scaffold in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/doc/test_doc.py`
- [X] T003 [P] Create generated-index wrapper template scaffold in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/template/features_index.rst.jinja2`
- [X] T004 [P] Extend ordered-doc template packaging coverage in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/generation/test_template_packaging.py`
- [X] T005 [P] Register the generated-index template asset in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/setup.cfg`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared ordering and template-rendering primitives required by all user stories.

**⚠️ CRITICAL**: No user story implementation should start before this phase is complete.

- [X] T006 Implement source-topic metadata extraction, numeric-prefix parsing, and prefix-stripped label preparation in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T007 Implement deterministic missing-prefix and duplicate-prefix validation in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T008 Integrate template-owned generated-index wrapper rendering in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T009 Align feature-ordering contract expectations with the approved schemas and paths in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_feature_doc_ordering_contract.py`
- [X] T010 Align ordered-doc template packaging expectations in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/generation/test_template_packaging.py`

**Checkpoint**: Ordered scope metadata, deterministic validation, and template-owned index rendering are ready for story work.

---

## Phase 3: User Story 1 - Read Topics in Learning Order (Priority: P1) 🎯 MVP

**Goal**: Make generated navigation present general topics before specialized ones for readers.

**Independent Test**: Generate documentation from prefixed fixture trees and verify top-level plus nested navigation appears in the curated order with reader-facing labels free of numeric prefixes.

### Tests for User Story 1

- [X] T011 [US1] Add top-level and nested ordered navigation regressions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/doc/test_doc.py`
- [X] T012 [US1] Add `/generation/index` and `NavigationScope` contract assertions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_feature_doc_ordering_contract.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement numeric-prefix sorting for sections and toctree entries in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T014 [P] [US1] Render prefix-free section headings and toctree labels in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/template/features_section.rst.jinja2`
- [X] T015 [P] [US1] Render prefix-free generated page titles in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/template/feature_include.rst.jinja2`
- [X] T016 [US1] Regenerate the top-level ordered feature navigation in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/docs/features/features.rst`

**Checkpoint**: Reader-facing feature documentation follows the curated general-to-specialized order and is independently testable.

---

## Phase 4: User Story 2 - Curate Order with Lightweight Markers (Priority: P2)

**Goal**: Let maintainers control order with numeric prefixes in source names while keeping reader-facing labels clean and generated paths stable.

**Independent Test**: Rename source siblings with numeric prefixes, regenerate docs, and verify labels hide the prefixes while generated page paths retain them.

### Tests for User Story 2

- [X] T017 [US2] Add prefix-hidden label and prefix-retained path regressions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/doc/test_doc.py`
- [X] T018 [US2] Add `/generation/page` and `DocumentationSourceTopic.generatedPagePath` contract assertions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_feature_doc_ordering_contract.py`

### Implementation for User Story 2

- [X] T019 [US2] Rename top-level feature-doc source directories under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/` to the curated order `01 Tutorial`, `02 Feature`, `03 Scenario`, `04 Step`, `05 Step definition`, `06 StructBDD`, and `07 Report`
- [X] T020 [P] [US2] Apply numeric prefixes to sibling topics inside `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/02 Feature/` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/02 Feature/09 Load/`
- [X] T021 [P] [US2] Apply numeric prefixes to sibling topics inside `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/03 Scenario/` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/03 Scenario/08 Outline/`
- [X] T022 [P] [US2] Apply numeric prefixes to sibling topics inside `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/04 Step/`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/05 Step definition/`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/05 Step definition/03 Parameters/`
- [X] T023 [P] [US2] Apply numeric prefixes to sibling topics inside `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/07 Report/` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/07 Report/06 Allure/`
- [X] T024 [US2] Regenerate prefix-retaining feature-doc pages under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/docs/features/`

**Checkpoint**: Maintainers can place topics by numeric prefixes, reader-facing labels stay clean, and generated paths remain source-derived.

---

## Phase 5: User Story 3 - Keep Regeneration Predictable (Priority: P3)

**Goal**: Keep ordered regeneration deterministic, preserve manual intro/suffix content, and fail clearly on invalid sibling prefixes.

**Independent Test**: Re-run generation on unchanged ordered sources, verify stable output, and confirm missing or duplicate prefixes fail with deterministic validation errors.

### Tests for User Story 3

- [X] T025 [US3] Add deterministic prefix-error, no-marker fallback, and idempotence regressions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/doc/test_doc.py`
- [X] T026 [US3] Add `/validation/ordering-prefixes` and `/conversion/markdown-headings` contract assertions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_feature_doc_ordering_contract.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement deterministic ordering-validation diagnostics for missing and duplicate sibling prefixes in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T028 [US3] Preserve manual intro/suffix extraction when rendering ordered index output in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T029 [US3] Keep markdown heading normalization on the preferred `pypandoc` path in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T030 [US3] Re-run ordered regeneration to align stable committed output under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/docs/features/`

**Checkpoint**: Ordered regeneration is deterministic, preserves manual content, and fails fast on invalid prefix states.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Capture validation evidence and delivery-readiness checks across all stories.

- [X] T031 Run ordered doc-generation pytest suites and record commands/results in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/quickstart.md`
- [X] T032 Run contract, strict docs build, and pre-commit validation commands and record commands/results in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/quickstart.md`
- [X] T033 Verify final task-to-story traceability notes in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2 and uses the ordering pipeline delivered for US1-ready output.
- **Phase 5 (US3)**: Depends on Phase 2 plus the ordered rendering and source-prefix conventions completed in US1 and US2.
- **Phase 6 (Polish)**: Depends on all desired user stories being complete.

### User Story Dependency Graph

- **US1 (P1)**: Can start after Foundational completion and is the MVP.
- **US2 (P2)**: Can start after Foundational completion, but committed repository renames should land after US1 ordering behavior is available.
- **US3 (P3)**: Depends on US1 and US2 because deterministic validation must cover the final ordered source tree and rendered output.

Graph: `Setup -> Foundational -> US1 -> US2 -> US3 -> Polish`

### Within Each User Story

- Story-specific regression tasks should be completed before implementation tasks for that story.
- Template changes and script changes must stay aligned with the contract assertions for the same story.
- Regenerated docs should be updated only after the story’s code path is complete.

---

## Parallel Execution Examples

### User Story 1

```bash
Task T014 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/template/features_section.rst.jinja2
Task T015 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/template/feature_include.rst.jinja2
```

### User Story 2

```bash
Task T020 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/02 Feature/
Task T021 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/03 Scenario/
Task T022 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/04 Step/
Task T023 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/07 Report/
```

### Setup / Foundational

```bash
Task T003 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/template/features_index.rst.jinja2
Task T004 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/generation/test_template_packaging.py
Task T005 in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/setup.cfg
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate ordered reader-facing navigation before changing the committed feature source tree.

### Incremental Delivery

1. Deliver US1 to prove ordered rendering and prefix-free labels.
2. Deliver US2 to apply numeric prefixes across the committed feature source tree and regenerate docs.
3. Deliver US3 to harden deterministic validation, idempotence, and manual-content preservation.
4. Finish with Phase 6 validation evidence and contributor workflow checks.

### Parallel Team Strategy

1. Complete Setup and Foundational work together.
2. Split template work (US1) and source-tree renaming preparation (US2) once the ordering model is stable.
3. Merge ordered source-tree changes, then finish deterministic validation and final regeneration in US3.

---

## Notes

- `[P]` tasks touch different files or disjoint directories and can run in parallel.
- `[US1]`, `[US2]`, and `[US3]` labels map tasks directly to spec user stories.
- Every task includes an explicit absolute file or directory path for direct execution.
- Outside pytest hook implementations, implementation tasks must avoid introducing `None` return contracts; use explicit values or deterministic exceptions instead.
- Commit with task IDs in commit messages and run pre-commit before every commit per constitution requirements.
- Validation evidence for T031 and T032 is recorded in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/quickstart.md`.
- Repository-wide `pre-commit --all-files` is still blocked by unrelated existing lint issues outside feature `010-order-rst-docs`; feature-scope lint and validation checks passed.
