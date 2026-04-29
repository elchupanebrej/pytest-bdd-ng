# Tasks: 018-uv-workflow-migration

**Input**: Design documents from `/specs/018-uv-workflow-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure
*No overarching folder structures are created since this primarily shifts existing environment files.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Mandate explicitly shifting the `uv` toolchain dependency directly into `pyproject.toml` under `project.optional-dependencies.testenv` mitigating manual requisite installations outside isolated contexts.
- [x] T002 Add required `tox-uv` overrides directly inside `tox.ini` defining standard compatibility grids using native paths.

**Checkpoint**: Core test dependency mapping prepared securely - user stories and entrypoint refactoring can proceed.

---

## Phase 3: User Story 1 - Contributors set up the project through one primary workflow (Priority: P1)

**Goal**: Deliver a singular `uv` based setup integrating formal endpoints and removing deprecated environment-manager instructions.

**Independent Test**: Running `uv run python src/pytest_bdd/script/validate_feature_headings.py --root-path features` and `uvx --with tox-uv tox -l` successfully boots contexts without alternate environment bootstrapping.

### Implementation for User Story 1

- [x] T003 [US1] Remap existing local tooling files strictly into native application boundaries within `pyproject.toml` assigning `validate_feature_headings` and `message_capability_governance` as executable mapping keys under `[project.scripts]`.
- [x] T004 [P] [US1] Adjust the primary `README.rst` installation workflow to use a single `uv sync` setup path and remove competing setup instructions.
- [x] T005 [P] [US1] Convert `DOCUMENTATION.rst` testing and documentation steps into `uvx` executions natively tracking the dependencies.
- [x] T006 [P] [US1] Substitute legacy rigid structures inside `Makefile` referencing manual virtual components explicitly to `uv` execution grids.

**Checkpoint**: Environment initialization correctly locks packages natively and executes internal feature scripts smoothly as explicit shell endpoints.

---

## Phase 4: User Story 2 - Maintainers run the test matrix through the canonical test entrypoint (Priority: P1)

**Goal**: CI Actions exclusively rely on `tox-uv` across full operating matrices bypassing standard runners completely.

**Independent Test**: PR checks boot correctly executing exactly `astral-sh/setup-uv` configurations.

### Implementation for User Story 2

- [x] T007 [P] [US2] Rewrite `.github/workflows/main.yml` leveraging `astral-sh/setup-uv` caches replacing explicit standard pip blocks.
- [x] T008 [P] [US2] Migrate baseline drift testing structures inside `.github/workflows/messages-baseline-drift.yml` to rely formally on new structural commands natively tracking dependencies.
- [x] T009 [P] [US2] Update publication processes inside `.github/workflows/release.yaml` building correctly off the new architecture.

**Checkpoint**: Remote CI runners properly execute standard grids mapping explicitly back to native execution overrides.

---

## Phase 5: User Story 3 - Documentation matches the actual contributor workflow (Priority: P2)

**Goal**: Full coverage alignment guarantees zero instances of historical instruction workflows persisting globally.

**Independent Test**: Documentation sub-folders securely instruct natively and a search for the deprecated environment-manager token yields 0 tutorial matches.

### Implementation for User Story 3

- [x] T010 [P] [US3] Traverse `docs/internal/feature-heading-validation.rst` altering embedded codeblocks standardizing on the updated endpoint mapping via formal CLI `uv run` behavior natively bypassing complex python paths.

**Checkpoint**: Global instructional sets map securely against architecture modifications formally isolated from edge cases.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation and performance checks completing the full matrix block correctly.

- [ ] T011 Run `uvx tox -e py314-pytestlatest` local check resolving dependency loading locally.
- [ ] T012 Validate explicit target integration via executing `uv run python -m pytest_bdd.script.message_capability_governance report` and confirming endpoint constraints.
- [ ] T013 Check formatting natively across files via `uvx pre-commit run --all-files`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: N/A
- **Foundational (Phase 2)**: BLOCKS Phase 3 testing logic.
- **User Stories (Phase 3+)**: US1, US2, and US3 run functionally independent and can be validated isolated explicitly targeting local configuration, CI overrides, and standard docs formats.

### Parallel Opportunities

- All non-blocking workflow files (`.github/workflows/**/*.yml`) inside [US2] iterate completely in parallel.
- All non-blocking documentation files (`.rst`, `docs/**/**/*.rst`) inside [US1], [US3] operate seamlessly identically.
