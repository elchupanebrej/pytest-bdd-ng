# Tasks: Go Gherkin Parser

**Input**: Design documents from `/specs/023-go-gherkin-parser/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: REQUIRED — user requested TDD via `test-driven-development` superpower. All implementation tasks MUST follow Red-Green-Refactor cycle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **[Agent Requirement]**: ALL implementation tasks MUST be delegated to subagents armed with `test-driven-development` superpower. Subagents MUST write failing tests first, then implement, then verify green.
- Include exact file paths in descriptions

## Path Conventions

- **Go module**: `gherkin_go/` at repo root
- **Python package**: `src/pytest_bdd/_gherkin_go/`
- **Python integration**: `src/pytest_bdd/collector_batch.py` (modify)
- **Tests**: `tests/unit/`, `tests/feature/`, `tests/build/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Go module, vendor dependencies, create directory structure, configure build system registration

- [x] T001 Initialize Go module and vendor cucumber/gherkin dependencies in `gherkin_go/`
- [x] T002 [P] Create Python package directory structure `src/pytest_bdd/_gherkin_go/` with `__init__.py`, `_bridge.py`, `_types.py`, `_build.py` stubs
- [x] T003 [P] Register `build_go` setuptools command in `pyproject.toml` under `[tool.setuptools.cmdclass]` and add package-data globs for `*.so`, `*.dll`, `*.dylib`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Write Go bridge C-exported functions (`ParseGherkinDocument`, `ParseGherkinMarkdown`, `FreeCString`, `Version`) in `gherkin_go/bridge/bridge.go` using TDD — write Go tests first, compile and verify with `go test ./bridge/`
- [x] T005 [P] Implement `build_go` setuptools Command in `src/pytest_bdd/_gherkin_go/_build.py` with Go toolchain detection, compilation via `go build -buildmode=c-shared`, hash-based caching, and graceful skip when Go unavailable — using TDD
- [x] T006 [P] Implement Python exception types (`GherkinParseError`, `GherkinGoNotAvailable`) in `src/pytest_bdd/_gherkin_go/_types.py` — using TDD

**Checkpoint**: Foundation ready — Go bridge compiles, build command functional, exception types defined

---

## Phase 3: User Story 1 - Faster Feature Parsing with Automatic Fallback (Priority: P1) 🎯 MVP

**Goal**: Features parsed via Go parser in `auto` mode with transparent Python fallback. Identical parse results to Python parser.

**Independent Test**: Install with Go shared library, run test suite with `PYTEST_BDD_GHERKIN_BACKEND=auto`, verify collection succeeds. Remove Go library, verify Python fallback works with no errors.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] Write unit tests for ctypes bridge library loading and C function calls in `tests/unit/test_gherkin_go_bridge.py` — test `_load_library()` with valid/invalid/missing `.so`, test C call wrappers, test `FreeCString` memory cleanup
- [x] T008 [P] [US1] Write unit tests for `parse()` function with valid/invalid Gherkin input in `tests/unit/test_gherkin_go_parse.py` — test plain `.feature` and markdown `.feature.md`, test `GherkinParseError` on bad syntax

### Implementation for User Story 1

- [x] T009 [US1] Implement ctypes low-level bridge (`_load_library`, C function wrappers, memory management) in `src/pytest_bdd/_gherkin_go/_bridge.py` — using TDD: make T007 tests pass
- [x] T010 [US1] Implement public `parse()` API with mimetype dispatch, JSON parsing, error detection in `src/pytest_bdd/_gherkin_go/__init__.py` — using TDD: make T008 tests pass
- [x] T011 [US1] Integrate Go backend selection into `_parse_feature_file()` in `src/pytest_bdd/collector_batch.py` — add lazy import of `_gherkin_go`, auto-fallback logic, logging (INFO on first success, WARNING on fallback, DEBUG on each call)
- [x] T012 [US1] Write integration test for full collection with Go backend active in `tests/feature/test_gherkin_go_collection.py` — test with real `.feature` files, verify parsed results, verify Python fallback when Go unavailable

**Checkpoint**: User Story 1 fully functional — Go parser parses features, falls back to Python when unavailable, logging works

---

## Phase 4: User Story 2 - Explicit Backend Selection via Environment Variable (Priority: P2)

- [x] T013 [P] [US2] Write unit tests for backend selection logic and fallback paths in `tests/unit/test_gherkin_go_fallback.py` — test `auto`/`go`/`python` modes, test `GherkinGoNotAvailable` in each mode, test env var parsing
- [x] T014 [US2] Implement `PYTEST_BDD_GHERKIN_BACKEND` env var parsing, backend mode enum, and strict mode enforcement (`go` mode raises on failure) in `src/pytest_bdd/_gherkin_go/__init__.py` and `src/pytest_bdd/collector_batch.py` — using TDD: make T013 tests pass

**Checkpoint**: Users can explicitly control parser backend via environment variable

---

## Phase 5: User Story 3 - Build pytest-bdd Wheel with Go Parser Embedded (Priority: P3)

- [x] T015 [P] [US3] Write build tests for `BuildGoCommand` in `tests/build/test_gherkin_go_build.py` — test with Go installed (verify `.so` created), test without Go (verify warning and skip), test hash cache (verify skip on no changes)
- [x] T016 [US3] Verify `build_go` Command handles all platforms (`.so`/`.dll`/`.dylib` naming), caching, and package-data inclusion correctly in `src/pytest_bdd/_gherkin_go/_build.py` — using TDD: make T015 tests pass

**Checkpoint**: Wheels build correctly on all platforms with and without Go toolchain

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, documentation, CI configuration

- [ ] T017 [P] Write cross-backend comparison test against all `gherkin/testdata/good/` fixtures — verify Go and Python produce identical `GherkinDocument` dicts — in `tests/feature/test_gherkin_go_parity.py`
- [ ] T018 [P] Add Go installation step to CI matrix (Linux, Windows, macOS) for wheel build and cross-backend tests
- [ ] T019 Verify all existing tests pass without modification (backward compatibility gate from spec SC-004)
- [ ] T020 [P] Run quickstart.md validation — verify all documented commands work end-to-end
- [ ] T021 Performance benchmark: measure collection time with 100+ feature files, verify 2x+ speedup vs Python-only

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on US1 (builds on parse pipeline and backend selection logic)
- **User Story 3 (Phase 5)**: Depends on Foundational (uses build command from T005)
- **Polish (Phase 6)**: Depends on US1, US2, US3 completion

### User Story Dependencies

- **US1 (P1)**: Start after Foundational. No dependencies on US2/US3.
- **US2 (P2)**: Depends on US1 (extends `_gherkin_go` and `collector_batch.py` modifications)
- **US3 (P3)**: Depends on Foundational only (build command from T005). Can run in parallel with US1/US2.
- **US3 can be dispatched in parallel with US1** — different files, no shared code dependency beyond T005

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Bridge layer before public API before integration
- Core implementation before integration into collector_batch.py
- Story complete with checkpoint verification before moving on

### Parallel Opportunities

- T001, T002, T003 can run in parallel (Phase 1)
- T005, T006 can run in parallel within Phase 2
- T007, T008 can run in parallel within US1 tests
- T015 can run in parallel with US1/US2 (US3 is independent)
- T017, T018, T020 can run in parallel within Phase 6

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T007 Write unit tests for ctypes bridge in tests/unit/test_gherkin_go_bridge.py"
Task: "T008 Write unit tests for parse() function in tests/unit/test_gherkin_go_parse.py"

# After tests fail, implement in order:
Task: "T009 Implement ctypes bridge in src/pytest_bdd/_gherkin_go/_bridge.py"
Task: "T010 Implement parse() API in src/pytest_bdd/_gherkin_go/__init__.py"
Task: "T011 Integrate into collector_batch.py"
```

## Parallel Example: US1 + US3

```bash
# US3 is independent of US1/US2 core — build command is in Foundational (T005)
# Dispatch in parallel with US1:
Task: "T015 Write build tests in tests/build/test_gherkin_go_build.py"
# (while US1 implementation proceeds in parallel)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. Complete Phase 3: User Story 1 (T007-T012)
4. **STOP and VALIDATE**: Run test suite, verify Go parser parses features, verify Python fallback
5. MVP delivers: faster parsing with automatic fallback

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Go parsing with fallback (MVP!)
3. Add US2 → Explicit backend control
4. Add US3 → Build integration verified
5. Polish → Cross-backend parity, CI, benchmarks

### Parallel Team Strategy

With multiple subagents:
1. Subagents complete Setup + Foundational together
2. Once Foundational is done:
   - Agent A: User Story 1 (T007-T012)
   - Agent B: User Story 3 (T015-T016) — independent build testing
3. After US1 complete: Agent A takes User Story 2 (T013-T014)
4. Final: Polish tasks in parallel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All implementation tasks MUST use `test-driven-development` superpower (Red-Green-Refactor)
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Go code tests (`go test`) run separately from pytest suite
- CI must include `setup-go@v5` with `go-version: '1.21'` for platforms that build with Go
