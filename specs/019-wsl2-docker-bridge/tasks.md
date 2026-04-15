# Tasks: WSL2 Docker Bridge for Windows

**Input**: Design documents from `/specs/019-wsl2-docker-bridge/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: REQUIRED — Feature specification mandates TDD Contract. All implementation tasks MUST instruct subagents to utilize the `test-driven-development` superpower with Red-Green-Refactor cycles.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **[Agent Requirement]**: All implementation tasks MUST be designed for delegation to subagents armed with Superpowers (e.g., `test-driven-development`). Explicitly mandate Red-Green-Refactor cycles in the task description.
- Include exact file paths in descriptions

## Path Conventions

- `tests/support/` — Test support utilities
- `tests/e2e/fixtures/remote_xdist/` — Docker Compose fixtures
- `tox.ini` — Tox configuration at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup needed — existing pytest-bdd repository.

- [x] T001 Review existing `tests/support/docker.py` (26 lines) and `tests/support/docker_cluster.py` (115 lines) to understand current Docker detection and cluster management behavior

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This includes WSL2-aware Docker detection, timeout configuration, and Docker Desktop auto-start.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] [Agent Requirement: Use `test-driven-development` superpower] Add `_alpine_wsl2_available()` function to `tests/support/docker.py` that detects if WSL2 Alpine dist exists by parsing `wsl -l -v` output. Write test first that mocks `subprocess.run` output showing Alpine with version 2, verify it fails, then implement. Return `bool`.

- [X] T003 [P] [Agent Requirement: Use `test-driven-development` superpower] Add `_start_docker_desktop()` function to `tests/support/docker.py` that launches Docker Desktop via `powershell -Command "Start-Process 'docker-desktop' -WindowStyle Hidden"`. Write test first that mocks `subprocess.run`, verify it fails, then implement. Return `None`. Raise `RuntimeError` if subprocess fails.

- [X] T004 [Agent Requirement: Use `test-driven-development` superpower] Add `_wait_for_docker(backend: str, timeout: int = 60)` function to `tests/support/docker.py` that polls `docker info` (native) or `wsl -d Alpine docker info` (wsl2) every 2 seconds until ready or timeout. Write test first with mocked subprocess that returns failure then success, verify it fails, then implement. Return `bool`.

- [X] T005 [Agent Requirement: Use `test-driven-development` superpower] Add `_ensure_docker_cli_in_alpine(timeout: int = 60)` function to `tests/support/docker.py` that checks `wsl -d Alpine -- which docker` and runs `wsl -d Alpine -u root -- apk add --no-cache docker-cli` if missing. Write test first with mocked subprocess, verify it fails, then implement. Return `None`. Call `pytest.fail()` on installation failure.

- [X] T006 Refactor `docker_daemon_available()` in `tests/support/docker.py` to return `tuple[bool, str | None]` (available, backend). Try native `docker info` first, then fall back to WSL2 Alpine. If both fail, call `_start_docker_desktop()` then `_wait_for_docker()`. Update `@lru_cache` to cache the tuple. Update all callers to unpack the tuple.

- [X] T007 Refactor `require_docker_daemon()` in `tests/support/docker.py` to return `str` (backend name). Call `docker_daemon_available()`. If not available, call `pytest.fail()` with descriptive message (not `pytest.skip()`). Messages: "Docker Desktop not installed", "WSL2 Alpine dist not found", "Docker Desktop did not start within timeout".

- [X] T008 [P] Add `DockerTimeouts` dataclass to `tests/support/docker_cluster.py` with fields: `startup_poll=60`, `compose_up=120`, `compose_exec=300`, `compose_cp=30`, `compose_down=30`, `alpine_install=60`, `overall_session=600`. Write test first that validates default values and that `overall_session >= sum(per-step)`, verify it fails, then implement.

**Checkpoint**: Foundation ready — Docker detection, Desktop startup, Alpine CLI install, and timeout configuration are working. User story implementation can now begin.

---

## Phase 3: User Story 1 — Run remote xdist tests on Windows via WSL2 Docker (Priority: P1) 🎯 MVP

**Goal**: Enable Docker Compose commands to route through WSL2 Alpine dist, allowing remote xdist tests to run on Windows.

**Independent Test**: Run `uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-socket-win` on Windows with Docker Desktop + WSL2 Alpine. All 3 remote modes (socket, via, ssh) pass.

### Tests for User Story 1

- [X] T009 [P] [US1] [Agent Requirement: Use `test-driven-development` superpower] Write test for `_run_wsl_cmd()` helper in `tests/support/docker_cluster.py` that verifies `wsl -d Alpine -- <args>` is constructed correctly. Mock `subprocess.run`, verify command list matches expected format.

- [X] T010 [US1] [Agent Requirement: Use `test-driven-development` superpower] Write integration test in `tests/support/test_docker_wsl2.py` that verifies `DockerClusterManager` with `backend="wsl2"` routes `get_cluster()` through WSL2 commands. Mock all subprocess calls. Verify `wsl -d Alpine docker compose` is called instead of bare `docker compose`.

### Implementation for User Story 1

- [X] T011 [P] [US1] [Agent Requirement: Use `test-driven-development` superpower] Add `_run_wsl_cmd(args: list[str], timeout: int) -> subprocess.CompletedProcess` helper to `tests/support/docker_cluster.py`. Constructs `["wsl", "-d", "Alpine", "--"] + args` and runs via `subprocess.run`. Write test first (T009), verify it fails, then implement.

- [X] T012 [US1] [Agent Requirement: Use `test-driven-development` superpower] Refactor `DockerClusterManager.__init__()` to accept `backend: str` parameter (default `"native"`). Store as instance attribute. When `backend == "wsl2"`, use `_run_wsl_cmd()` for all Docker operations. When `backend == "native"`, use existing `subprocess.run()` behavior. Write test first (T010), verify it fails, then implement.

- [X] T013 [US1] [Agent Requirement: Use `test-driven-development` superpower] Refactor `DockerClusterManager.get_cluster()` to use `_run_wsl_cmd()` when `backend == "wsl2"`. Replace direct `subprocess.run(["docker", "compose", ...])` with backend-aware routing. Add per-step timeout (`compose_up`) and overall session timeout tracking. Write test first, verify it fails, then implement.

- [X] T014 [US1] [Agent Requirement: Use `test-driven-development` superpower] Refactor `DockerClusterManager.run_in_controller()` to use `_run_wsl_cmd()` when `backend == "wsl2"`. Add per-step timeout (`compose_exec`). Write test first, verify it fails, then implement.

- [X] T015 [US1] [Agent Requirement: Use `test-driven-development` superpower] Refactor `DockerClusterManager.cleanup()` to use `_run_wsl_cmd()` when `backend == "wsl2"`. Add per-step timeout (`compose_down`). Write test first, verify it fails, then implement.

- [X] T016 [US1] [Agent Requirement: Use `test-driven-development` superpower] Refactor `docker-compose.yml` in `tests/e2e/fixtures/remote_xdist/docker-compose.yml` to use relative bind mounts instead of `${REPO_ROOT}` env var. Change `build.context` from `${REPO_ROOT}` to `.` (compose file directory). Change volume mount from `${ARTIFACT_DIR}:/artifacts` to relative path. Update service definitions to work with fixture-only mount. Write test first that validates YAML structure, verify it fails, then implement.

- [X] T017 [US1] [Agent Requirement: Use `test-driven-development` superpower] Refactor `controller_entrypoint.py` in `tests/e2e/fixtures/remote_xdist/controller_entrypoint.py` to be self-contained — no imports from repo root outside fixture directory. Inline any needed helper functions from `tests/support/cucumber_formatters.py`. Use only standard library + pytest + pytest-xdist. Write test first that verifies no external imports, verify it fails, then implement.

- [X] T018 [US1] [Agent Requirement: Use `test-driven-development` superpower] Refactor `worker_entrypoint.py` in `tests/e2e/fixtures/remote_xdist/worker_entrypoint.py` to be self-contained. Same approach as T017. Write test first, verify it fails, then implement.

- [X] T019 [US1] [Agent Requirement: Use `test-driven-development` superpower] Update `controller.Dockerfile` and `worker.Dockerfile` in `tests/e2e/fixtures/remote_xdist/` to use relative build context (compose file directory) instead of `${REPO_ROOT}`. Update `COPY` paths accordingly. Verify Dockerfiles build successfully with new context.

**Checkpoint**: At this point, User Story 1 should be fully functional — remote xdist tests run on Windows via WSL2 Alpine with Docker Desktop auto-start, relative mounts, and self-contained entrypoints.

---

## Phase 4: User Story 2 — Docker detection fails gracefully when prerequisites missing (Priority: P2)

**Goal**: Provide clear, actionable failure messages when Docker Desktop, WSL2 Alpine, or Docker CLI are unavailable.

**Independent Test**: Run tests on a Windows machine without Docker Desktop installed. Tests fail with "Docker Desktop not installed" (not traceback or skip).

### Tests for User Story 2

- [X] T020 [P] [US2] [Agent Requirement: Use `test-driven-development` superpower] Write test in `tests/support/test_docker_wsl2.py` that verifies `require_docker_daemon()` calls `pytest.fail("Docker Desktop not installed")` when `docker info` and `wsl docker info` both fail and `_start_docker_desktop()` is not available. Mock all subprocess calls.

- [X] T021 [P] [US2] [Agent Requirement: Use `test-driven-development` superpower] Write test in `tests/support/test_docker_wsl2.py` that verifies `require_docker_daemon()` calls `pytest.fail("WSL2 Alpine dist not found")` when native docker fails and `_alpine_wsl2_available()` returns `False`.

- [X] T022 [US2] [Agent Requirement: Use `test-driven-development` superpower] Write test in `tests/support/test_docker_wsl2.py` that verifies `require_docker_daemon()` calls `pytest.fail("Docker Desktop did not start within timeout")` when `_start_docker_desktop()` succeeds but `_wait_for_docker()` returns `False` after timeout.

### Implementation for User Story 2

- [X] T023 [US2] Implement the failure paths in `require_docker_daemon()` (already partially done in T007). Ensure each failure scenario produces the exact expected message. Ensure `pytest.fail()` is called (not `pytest.skip()`). Tests T020-T022 should pass.

- [X] T024 [US2] [Agent Requirement: Use `test-driven-development` superpower] Add timeout exceeded handling to `DockerClusterManager` methods. When any Docker operation exceeds its per-step timeout from `DockerTimeouts`, raise `RuntimeError` with descriptive message including operation name and timeout value. Write test first that mocks subprocess timeout, verify it fails, then implement.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — core functionality delivers tests on Windows, and missing prerequisites produce clear failure messages.

---

## Phase 5: User Story 3 — Linux and macOS behavior unchanged (Priority: P3)

**Goal**: Ensure backward compatibility — Linux/macOS tox environments pass with zero behavioral changes.

**Independent Test**: Run `uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-socket-lin` on Linux. Same test results as before this feature.

### Tests for User Story 3

- [X] T025 [P] [US3] [Agent Requirement: Use `test-driven-development` superpower] Write test in `tests/support/test_docker_wsl2.py` that verifies `docker_daemon_available()` returns `("native", "native")` when native `docker info` succeeds (no WSL2 fallback attempted). Mock `shutil.which("docker")` to return a path and `subprocess.run(["docker", "info"])` to return 0.

- [X] T026 [P] [US3] [Agent Requirement: Use `test-driven-development` superpower] Write test in `tests/support/test_docker_wsl2.py` that verifies `DockerClusterManager` with `backend="native"` uses direct `subprocess.run()` (not `_run_wsl_cmd()`). Mock both `subprocess.run` and `_run_wsl_cmd`, verify only `subprocess.run` is called.

### Implementation for User Story 3

- [X] T027 [US3] Verify that when `backend == "native"`, all `DockerClusterManager` methods use the original `subprocess.run()` code path (no WSL2 routing). This should already be true from T012-T015, but add explicit test coverage (T025-T026) and verify existing Linux tox environments pass.

- [X] T028 [US3] Run existing Linux tox environments (`py314-pytestlatest-xdist-remote-{socket,via,ssh}-lin`) to verify zero behavioral changes. Document results.

**Checkpoint**: All user stories should now be independently functional. US1 delivers Windows Docker support, US2 delivers graceful failures, US3 preserves Linux/macOS compatibility.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tox environments, documentation, and final validation.

- [X] T029 [P] Add 3 new tox environments to `tox.ini`: `py314-pytestlatest-xdist-remote-socket-win`, `py314-pytestlatest-xdist-remote-via-win`, `py314-pytestlatest-xdist-remote-ssh-win`. Each uses `platform = win: win32` filter and sets `PYTEST_REMOTE_MODE` env var. Same commands as Linux variant.

- [X] T030 [P] Update `tests/e2e/conftest.py` BDD step "Docker is available" to use new `require_docker_daemon()` return value (backend name) for logging. No behavioral change.

- [X] T031 [P] Update `tests/e2e/docker_support.py` re-export shim if `require_docker_daemon()` signature changed (now returns `str` instead of `None`).

- [X] T032 Run `quickstart.md` validation — follow the quickstart guide end-to-end on a Windows machine with Docker Desktop + WSL2 Alpine. Verify all 3 remote modes pass.

- [X] T033 Run full tox test suite for Windows (`py314-pytest90-coverage-win`) to verify no regressions in non-Docker tests.

- [X] T034 Run `uvx pre-commit run --all-files` to verify linting and formatting compliance.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Depends on T007 (require_docker_daemon refactor) from Foundational
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Depends on T012-T015 (backend-aware routing) from US1

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Helper functions before refactoring existing code
- Core refactoring before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003, T004, T005, T008 can run in parallel (different functions, different files)
- T009, T010 can run in parallel (different test files)
- T011, T016, T017, T018, T019 can run in parallel after T012 (different files)
- T020, T021, T022 can run in parallel (different test cases)
- T025, T026 can run in parallel (different test cases)
- T029, T030, T031 can run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T009: "Test _run_wsl_cmd() helper in tests/support/docker_cluster.py"
Task T010: "Integration test for DockerClusterManager with WSL2 backend"

# After T012 completes, launch parallel implementation tasks:
Task T011: "Add _run_wsl_cmd() helper in tests/support/docker_cluster.py"
Task T016: "Refactor docker-compose.yml for relative mounts"
Task T017: "Refactor controller_entrypoint.py to be self-contained"
Task T018: "Refactor worker_entrypoint.py to be self-contained"
Task T019: "Update Dockerfiles for relative build context"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (1 task — review)
2. Complete Phase 2: Foundational (7 tasks — Docker detection, startup, timeouts)
3. Complete Phase 3: User Story 1 (11 tasks — WSL2 routing, relative mounts, self-contained entrypoints)
4. **STOP and VALIDATE**: Run `uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-socket-win`
5. If passing: MVP is complete — Windows Docker tests work

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP delivers Windows Docker support
3. Add User Story 2 → Test independently → Graceful failure messages
4. Add User Story 3 → Test independently → Linux/macOS backward compatibility verified
5. Phase 6: Polish → Tox environments, documentation, full test suite

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (WSL2 routing + relative mounts)
   - Developer B: User Story 2 (graceful failures) — can start after T007
   - Developer C: User Story 3 (backward compat) — can start after T012-T015
3. Phase 6: Polish tasks run in parallel

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- ALL implementation tasks require `test-driven-development` superpower — write test first, watch it fail, write minimal code to pass, refactor
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Total tasks: 34
  - Phase 1: 1 task
  - Phase 2: 7 tasks
  - Phase 3 (US1): 11 tasks
  - Phase 4 (US2): 5 tasks
  - Phase 5 (US3): 4 tasks
  - Phase 6 (Polish): 6 tasks
