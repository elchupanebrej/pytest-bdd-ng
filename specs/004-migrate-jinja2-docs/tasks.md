<!-- markdownlint-disable MD013 -->

# Tasks: Migrate Documentation Generation to Jinja2

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/jinja2-doc-generation.openapi.yaml`, `quickstart.md`
**Language**: English (all task descriptions and notes)

**Tests**: Test tasks are included because the specification defines explicit independent test criteria and measurable validation outcomes.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare migration scaffolding for Jinja2 rendering and validation coverage.

- [X] T001 Create migration contract test scaffold in `tests/contract/test_jinja2_doc_generation_contract.py`
- [X] T002 [P] Create template packaging test scaffold in `tests/generation/test_template_packaging.py`
- [X] T003 [P] Create documentation regeneration test scaffold in `tests/doc/test_doc.py`
- [X] T004 [P] Create Jinja2 code template scaffold in `src/pytest_bdd/template/test.py.jinja2`
- [X] T005 [P] Create Jinja2 documentation section template scaffold in `src/pytest_bdd/template/features_section.rst.jinja2`
- [X] T006 [P] Create Jinja2 documentation include template scaffold in `src/pytest_bdd/template/feature_include.rst.jinja2`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared migration primitives required by all user stories.

**⚠️ CRITICAL**: No user story implementation should start before this phase is complete.

- [X] T007 Implement shared Jinja2 environment initialization for code generation in `src/pytest_bdd/plugin/code_generator/plugin.py`
- [X] T008 Implement shared Jinja2 environment initialization for documentation generation in `src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T009 Update packaged template asset declarations for `.jinja2` resources in `setup.cfg`
- [X] T010 Update runtime dependency metadata for Jinja2 migration in `pyproject.toml`
- [X] T011 Add generated block marker boundaries to documentation index in `docs/features/features.rst`
- [X] T012 Add foundational generated-block boundary assertions in `tests/doc/test_doc.py`
- [X] T013 Remove legacy Mako code-generation template asset at `src/pytest_bdd/template/test.py.mak`

**Checkpoint**: Shared template loading, packaging, and marker boundaries are ready.

---

## Phase 3: User Story 1 - Preserve Generated Output Parity (Priority: P1) 🎯 MVP

**Goal**: Keep code-generation output behavior semantically compatible while moving rendering to Jinja2.

**Independent Test**: Run generation suites and verify semantic parity for baseline, quote-heavy, and unicode scenarios.

### Tests for User Story 1

- [X] T014 [P] [US1] Add contract checks for `/generation/render/code` and `/validation/parity` in `tests/contract/test_jinja2_doc_generation_contract.py`
- [X] T015 [P] [US1] Add semantic parity regression cases for quote/unicode content in `tests/generation/test_generate.py`
- [X] T016 [US1] Add semantic parity regression cases for missing-generation paths in `tests/generation/test_generate_missing.py`

### Implementation for User Story 1

- [X] T017 [US1] Switch code-generation renderer from Mako to Jinja2 in `src/pytest_bdd/plugin/code_generator/plugin.py`
- [X] T018 [US1] Port code template logic from Mako syntax to Jinja2 syntax in `src/pytest_bdd/template/test.py.jinja2`
- [X] T019 [US1] Ensure packaged template lookup resolves `.jinja2` assets in `src/pytest_bdd/plugin/code_generator/plugin.py`
- [X] T020 [US1] Remove obsolete Mako imports and dead branches in `src/pytest_bdd/plugin/code_generator/plugin.py`

**Checkpoint**: Code generation parity behavior is preserved on Jinja2.

---

## Phase 4: User Story 2 - Preserve Manual Documentation Content (Priority: P2)

**Goal**: Regeneration updates generated documentation blocks without overwriting manual sections.

**Independent Test**: Regenerate documentation against files with manual prefix/suffix content and verify preservation.

### Tests for User Story 2

- [X] T021 [P] [US2] Add contract checks for `/generation/render/docs` and `/docs/features/index` in `tests/contract/test_jinja2_doc_generation_contract.py`
- [X] T022 [P] [US2] Add manual prefix/suffix preservation regression case in `tests/doc/test_doc.py`
- [X] T023 [US2] Add no-marker fallback and idempotent regeneration regression cases in `tests/doc/test_doc.py`

### Implementation for User Story 2

- [X] T024 [US2] Implement generated-section extraction and replacement flow in `src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T025 [US2] Implement Jinja2 toctree section rendering in `src/pytest_bdd/template/features_section.rst.jinja2`
- [X] T026 [US2] Implement Jinja2 feature include rendering in `src/pytest_bdd/template/feature_include.rst.jinja2`
- [X] T027 [US2] Integrate documentation templates into regeneration pipeline in `src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T028 [US2] Regenerate marker-safe documentation index output in `docs/features/features.rst`

**Checkpoint**: Documentation regeneration updates generated blocks only and preserves manual content.

---

## Phase 5: User Story 3 - Keep Contributor Workflow Stable (Priority: P3)

**Goal**: Keep validation and packaging workflows explicit, reproducible, and pre-commit enforced.

**Independent Test**: Run migration quickstart validation commands, including pre-commit, and confirm stale docs are blocked.

### Tests for User Story 3

- [X] T029 [P] [US3] Add contract checks for `/generation/templates`, `/validation/packaging/templates`, and `/validation/doc-sync` in `tests/contract/test_jinja2_doc_generation_contract.py`
- [X] T030 [P] [US3] Add packaged template manifest validation tests in `tests/generation/test_template_packaging.py`
- [X] T031 [US3] Add stale-documentation pre-commit regression case in `tests/doc/test_doc.py`

### Implementation for User Story 3

- [X] T032 [US3] Enable documentation generation hook enforcement in `.pre-commit-config.yaml`
- [X] T033 [US3] Stabilize documentation generation command behavior for hook execution in `src/pytest_bdd/script/bdd_tree_to_rst.py`
- [X] T034 [US3] Update contributor regeneration workflow and expected outcomes in `specs/004-migrate-jinja2-docs/quickstart.md`
- [X] T035 [US3] Synchronize regenerated documentation output after hook enablement in `docs/features/features.rst`

**Checkpoint**: Contributor workflow and packaging validation remain stable after migration.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and evidence capture across all stories.

- [X] T036 [P] Run focused migration pytest suites and record command/results in `specs/004-migrate-jinja2-docs/quickstart.md`
- [X] T037 [P] Run `ruff` and pre-commit validation and record command/results in `specs/004-migrate-jinja2-docs/quickstart.md`
- [X] T038 Execute selected compatibility matrix checks (`py312-pytest625`, `py314-pytest90`) and record command/results in `specs/004-migrate-jinja2-docs/quickstart.md`
- [X] T039 Validate final task-to-story traceability notes in `specs/004-migrate-jinja2-docs/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2.
- **Phase 5 (US3)**: Depends on US1 and US2 completion plus Phase 2.
- **Phase 6 (Polish)**: Depends on completion of all user stories.

### User Story Dependency Graph

- **US1 (P1)** and **US2 (P2)** can start after Foundational completion.
- **US3 (P3)** depends on outputs from both US1 and US2.

Graph: `Foundational -> {US1, US2} -> US3`

### Within Each User Story

- Test tasks are implemented before implementation tasks for that story.
- Template and model-level changes precede integration wiring.
- Story-specific validation must pass before moving to next priority delivery.

---

## Parallel Execution Examples

### User Story 1

```bash
Task T014 in tests/contract/test_jinja2_doc_generation_contract.py
Task T015 in tests/generation/test_generate.py
```

### User Story 2

```bash
Task T021 in tests/contract/test_jinja2_doc_generation_contract.py
Task T022 in tests/doc/test_doc.py
```

### User Story 3

```bash
Task T029 in tests/contract/test_jinja2_doc_generation_contract.py
Task T030 in tests/generation/test_template_packaging.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate semantic parity before continuing.

### Incremental Delivery

1. Deliver US1 (semantic output parity).
2. Deliver US2 (manual-content-safe docs regeneration).
3. Deliver US3 (pre-commit enforcement and packaging/workflow stability).
4. Run Phase 6 cross-cutting validation and record evidence.

### Parallel Team Strategy

1. Complete Setup + Foundational as a shared baseline.
2. After Phase 2, split work: one engineer on US1 and one on US2.
3. Merge US1/US2, then complete US3 integration and final polish.

---

## Notes

- `[P]` tasks touch different files and can run in parallel.
- `[US1]`, `[US2]`, `[US3]` labels map tasks directly to user stories.
- Include task IDs in commit messages per constitution rules.
- Keep all planning/task artifacts in English.
- Traceability validation completed on 2026-02-24: all user-story phase tasks
  contain story labels and explicit file paths.
