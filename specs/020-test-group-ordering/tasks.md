---
description: "Task list for feature: Test Group Ordering"
---

# Tasks: Test Group Ordering

**Input**: Design documents from `/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/`
**Prerequisites**: [plan.md](/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/plan.md), [spec.md](/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/spec.md), [research.md](/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/research.md), [data-model.md](/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/data-model.md), [contracts/group-config.md](/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/contracts/group-config.md), [quickstart.md](/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/quickstart.md)

**Tests**: Required by the feature's TDD Contract and Agentic Validation Constraints. Test tasks must be completed RED before related implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: User-story phase label only: `[US1]`, `[US2]`, `[US3]`.
- Every task includes exact absolute file paths.
- All implementation tasks must use `test-driven-development` with Red-Green-Refactor.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Remove stale implementation artifacts from earlier designs and prepare dependency/configuration files for pytest ini-style group configuration.

- [X] T001 Remove stale test-local grouping utility `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/_group_ordering.py` and update any imports that reference it in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/conftest.py` or `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`
- [X] T002 Update test dependency declarations in `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml` so `pytest-order` is available to the project test environment
- [X] T003 Update pytest marker registration and `addopts` in `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml` for configured example groups `instant`, `fast`, `medium`, `slow`, `external` plus the `order` marker
- [X] T004 Replace any stale `[tool.pytest-bdd-ng.test-groups]` configuration in `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml` with pytest ini-style options `test_group_order`, `test_group_default`, and `test_group_paths` under `[tool.pytest.ini_options]`
- [X] T005 [P] Create source utility module placeholder `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py` with import-safe structure and explicit placeholders needed for RED tests
- [X] T006 [P] Create or reset source-utility unit test file `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py` so it targets `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`

**Checkpoint**: Stale design artifacts are removed from implementation files, and project config targets pytest ini-style group options only.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the reusable group configuration utility and pytest adapter. No user story can be completed until this foundation exists.

**CRITICAL**: Complete this phase before Phase 3+ work.

### Tests First

- [X] T007 Write RED unit tests for pytest ini registration and parsing in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`, covering `test_group_order`, `test_group_default`, `test_group_paths`, arbitrary group names, ordered ordinals, malformed mapping lines, duplicate groups, empty groups, invalid default fallback, and unknown path mapping values
- [X] T008 Write RED unit tests for marker participation rules in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`, proving only names from `test_group_order` are group signals and unrelated pytest markers are ignored without hardcoded ignore lists
- [X] T009 Write RED unit tests for group assignment resolution in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`, covering directory naming convention, configured path mapping overriding convention, inherited directory marker, test-level marker, default fallback, duplicate group normalization, and same-level conflict resolved to latest configured group
- [X] T010 Write RED unit tests for order-marker application in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`, proving the helper applies `pytest.mark.order(N)` and never mutates or sorts a provided item list
- [X] T011 Write RED adapter tests in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`, proving `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/conftest.py` registers custom pytest ini options, imports the source utility, reads config through pytest APIs, applies order markers to collected items, and contains no direct `items.sort` or `items[:]` reordering logic

### Implementation

- [X] T012 Implement dataclasses and explicit return types for `GroupConfig`, `GroupAssignment`, `GroupPathMapping`, warning records, and runtime barrier observations in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`
- [X] T013 Implement pytest ini option registration helpers for `test_group_order`, `test_group_default`, and `test_group_paths` in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`
- [X] T014 Implement pytest ini configuration reading and validation in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`, emitting visible warnings for invalid group configuration while continuing collection
- [X] T015 Implement path mapping parsing, path matching, and directory naming resolution in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`, using repo-relative paths and last matching configured path mapping as the deterministic override rule
- [X] T016 Implement configured-marker extraction and cascade resolution in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`, ignoring all non-group pytest markers without any hardcoded ignore list
- [X] T017 Implement order-marker application helper in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`, applying `pytest.mark.order(assignment.ordinal)` only
- [X] T018 Refactor `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/conftest.py` into a thin pytest adapter that registers custom ini options, imports `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`, registers configured group markers, applies order markers, and never sorts collected items
- [X] T019 Run `uv run python -m pytest /mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py -q` from `/mnt/c/Users/bulky/Projects/pytest-bdd` and make all foundational tests pass

**Checkpoint**: Source utility and adapter are green, generic, pytest ini-style only, and free of direct item-ordering logic.

---

## Phase 3: User Story 1 - Define and Configure Test Groups (Priority: P1) MVP

**Goal**: The existing test suite can be assigned to configured groups through pytest ini path mappings, existing directory-name matches, and pytest markers without moving or renaming tests.

**Independent Test**: Define two or more groups in pytest ini configuration, assign tests through the cascade, and verify every collected item resolves to exactly one configured group with the expected precedence.

### Tests for User Story 1

- [X] T020 [US1] Write RED acceptance tests for US1 cascade scenarios in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`, covering configured path assignment, directory convention fallback, default group assignment, conftest marker override, test marker override, and conflicting cascade levels
- [X] T021 [US1] Write RED regression tests in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py` proving custom group names such as `alpha`, `beta`, `gamma` work so `instant`, `fast`, `medium`, `slow`, and `external` are examples only
- [X] T022 [US1] Write RED regression test in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py` proving ordinary pytest markers such as `skip`, `xfail`, `parametrize`, or project-specific non-group markers do not alter group resolution and do not require warning output

### Implementation for User Story 1

- [X] T023 [US1] Audit existing test directories and complete initial path classification in `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml` using `test_group_order`, `test_group_default`, and `test_group_paths` without moving or renaming any files under `/mnt/c/Users/bulky/Projects/pytest-bdd/tests`
- [X] T024 [US1] Remove or replace stale project-specific group references and stale tool-specific table usage in `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml`, `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/conftest.py`, and `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`
- [X] T025 [US1] Run `uv run python -m pytest /mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py -q` from `/mnt/c/Users/bulky/Projects/pytest-bdd` and make all US1 tests pass
- [X] T026 [US1] Run `uv run python -m pytest --collect-only -q` from `/mnt/c/Users/bulky/Projects/pytest-bdd` using `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml` and verify collection succeeds with every existing test assigned to exactly one configured group

**Checkpoint**: MVP complete. Group definitions and assignment cascade work independently of full-suite runtime ordering.

---

## Phase 4: User Story 2 - Run the Full Suite in Group Order (Priority: P2)

**Goal**: A normal full-suite pytest invocation executes configured groups in strict configured order while still running later groups after earlier failures or skips, including xdist runtime barriers.

**Independent Test**: Define at least three groups, run tests from each group, and verify no item from group N+1 starts before all items from group N complete.

### Tests for User Story 2

- [X] T027 [US2] Write RED acceptance tests for full-suite ordered execution in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`, covering at least three configured groups and asserting order marker ordinals produce strict group order through the selected ordering mechanism
- [X] T028 [US2] Write RED acceptance tests in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py` proving earlier-group failure and all-skipped groups do not prevent later groups from being collected and run
- [X] T029 [US2] Write RED acceptance test in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py` where a fixture calls `pytest.skip()` for an earlier-group test and later-group tests still run with the earlier test reported as a normal pytest skip
- [X] T030 [US2] Write RED xdist runtime-barrier acceptance test in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py` that records test start and finish events with monotonic timestamps and fails if any later-group start occurs before every earlier-group finish

### Implementation for User Story 2

- [X] T031 [US2] Verify and adjust `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml` so `--order-scope=session` and pytest ini group options are active in normal pytest invocation without requiring a wrapper command
- [X] T032 [US2] Implement any runtime barrier support required by the xdist acceptance test in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py` and `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/conftest.py` while preserving the rule that project code does not directly sort collected items
- [X] T033 [US2] Run `uv run python -m pytest /mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py -q` from `/mnt/c/Users/bulky/Projects/pytest-bdd` and make all US2 acceptance tests pass
- [X] T034 [US2] Validate xdist runtime behaviour by running `uv run python -m pytest -n auto /mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py -q` from `/mnt/c/Users/bulky/Projects/pytest-bdd` and confirm recorded start/finish events preserve runtime group barriers

**Checkpoint**: Full-suite ordering is delegated to pytest ordering/barrier mechanisms, fixture skips are normal pytest skips, and project code still performs no direct collected-item sorting.

---

## Phase 5: User Story 3 - Run a Single Group in Isolation (Priority: P3)

**Goal**: Developers can run any configured group through normal pytest marker selection, and non-selected groups are not collected.

**Independent Test**: Run pytest with one configured group marker and verify only that group's tests are collected and executed.

### Tests for User Story 3

- [X] T035 [US3] Write RED acceptance tests for per-group marker filtering in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`, covering one selected group, excluded groups not collected, and empty group selection exiting cleanly

### Implementation for User Story 3

- [X] T036 [US3] Run and validate `uv run python -m pytest -m instant --collect-only -q`, `uv run python -m pytest -m fast --collect-only -q`, `uv run python -m pytest -m medium --collect-only -q`, `uv run python -m pytest -m slow --collect-only -q`, and `uv run python -m pytest -m external --collect-only -q` from `/mnt/c/Users/bulky/Projects/pytest-bdd` using `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml`
- [X] T037 [US3] Update per-group invocation examples and any verified caveats in `/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/quickstart.md`

**Checkpoint**: Each configured group is independently selectable by marker filter.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete validation, update supporting docs, and ensure quality gates cover the source utility.

- [X] T038 [P] Update `/mnt/c/Users/bulky/Projects/pytest-bdd/AGENTS.md` to document the generic test-group ordering convention, pytest ini-style group options, and source utility location without implying fixed group names
- [X] T039 [P] Update `/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/research.md` with measured collection overhead and xdist runtime-barrier validation notes from implementation
- [X] T040 Measure collection-phase overhead by comparing `uv run python -m pytest --collect-only -q` with grouping disabled and enabled from `/mnt/c/Users/bulky/Projects/pytest-bdd`, and confirm the enabled run adds no more than 2 seconds using `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml`
- [X] T041 Run `uv run python -m pytest /mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py -q` from `/mnt/c/Users/bulky/Projects/pytest-bdd`
- [X] T042 Run `uv run python -m pytest --collect-only -q` from `/mnt/c/Users/bulky/Projects/pytest-bdd` using `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml` to validate quick collection across the existing suite
- [X] T043 Run `uvx --with tox-uv tox -l` from `/mnt/c/Users/bulky/Projects/pytest-bdd` and ensure `/mnt/c/Users/bulky/Projects/pytest-bdd/tox.ini` environments still resolve with `pytest-order`
- [ ] T044 Run `uvx pre-commit run --all-files` from `/mnt/c/Users/bulky/Projects/pytest-bdd` and fix any formatting, linting, or typing issues in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`, `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/conftest.py`, and `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py`
- [ ] T045 Run the commands documented in `/mnt/c/Users/bulky/Projects/pytest-bdd/specs/020-test-group-ordering/quickstart.md` end-to-end and update that file if observed behaviour differs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 3 because existing-suite group assignment must exist before full-suite order can be validated.
- **Phase 5 (US3)**: Depends on Phase 3 and can proceed independently of US2.
- **Phase 6 (Polish)**: Depends on desired story phases being complete.

### User Story Dependencies

- **US1 (P1)**: Independent after the foundational utility and adapter exist.
- **US2 (P2)**: Requires US1 group assignment, but is independently testable with a small configured test set.
- **US3 (P3)**: Requires US1 group assignment, but is independent of US2.

### Within Each User Story

- RED acceptance tests must be written and fail before implementation.
- Configuration changes precede existing-suite validation.
- Runtime xdist validation must execute tests and inspect start/finish events; collect-only is insufficient for US2.
- Story checkpoint validation must pass before marking the story complete.

---

## Parallel Execution Examples

### Phase 1

```text
T005: Create source utility placeholder in /mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py
T006: Reset utility tests in /mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py
```

### User Story 1

```text
No safe intra-story parallel split is marked [P] for US1 because RED tests share /mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py and implementation tasks share /mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml plus adapter files.
Run US1 sequentially: T020 -> T021 -> T022 -> T023 -> T024 -> T025 -> T026.
```

### User Story 2

```text
No safe intra-story parallel split is marked [P] for US2 because ordering, fixture-skip, and xdist runtime tests share /mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py and validation depends on /mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml.
Run US2 sequentially: T027 -> T028 -> T029 -> T030 -> T031 -> T032 -> T033 -> T034.
```

### User Story 3

```text
No safe intra-story parallel split is marked [P] for US3 because marker-filter tests and documentation validation depend on the same configured marker set in /mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml.
Run US3 sequentially: T035 -> T036 -> T037.
```

### Polish

```text
T038: AGENTS.md convention update
T039: research.md validation notes update
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 to remove stale artifacts and configure dependencies.
2. Complete Phase 2 to build the generic source utility and adapter.
3. Complete Phase 3 to prove configurable group assignment works with pytest ini-style configuration and the existing tree.
4. Stop and validate US1 independently with `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/unit/test_group_ordering.py` and `pytest --collect-only`.

### Incremental Delivery

1. Foundation: utility + adapter + pytest ini config validation.
2. US1: correct group assignment without test tree moves.
3. US2: full-suite ordered execution, fixture-skip semantics, and xdist runtime barriers.
4. US3: per-group isolated invocation.
5. Polish: quality gates, quickstart, overhead, and xdist notes.

### Subagent Dispatch Strategy

- **Subagent A**: Phase 2 source utility in `/mnt/c/Users/bulky/Projects/pytest-bdd/src/pytest_bdd/util/test_group_ordering.py`.
- **Subagent B**: Phase 2 adapter and pytest ini config in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/conftest.py` and `/mnt/c/Users/bulky/Projects/pytest-bdd/pyproject.toml`.
- **Subagent C**: Phase 3 existing-tree classification and acceptance validation.
- **Subagent D**: Phase 4 runtime validation for fixture skips and xdist group barriers.

## Notes

- Do not reintroduce `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/_group_ordering.py`.
- Do not add `[tool.pytest-bdd-ng.test-groups]` or any separate tool-specific group configuration table.
- Do not hardcode `instant`, `fast`, `medium`, `slow`, or `external` in resolver logic; they are example configuration values only.
- Do not use hardcoded ignore lists for non-group markers.
- Do not move or rename existing files under `/mnt/c/Users/bulky/Projects/pytest-bdd/tests`.
- Do not sort, slice-replace, or otherwise reorder `items` in `/mnt/c/Users/bulky/Projects/pytest-bdd/tests/conftest.py`; collection ordering belongs to pytest plugins, and runtime barriers must be validated separately.
