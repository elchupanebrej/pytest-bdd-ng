# Feature Specification: WSL2 Docker Bridge for Windows

**Feature Branch**: `019-wsl2-docker-bridge`
**Created**: 2026-04-15
**Status**: Draft
**Input**: User description: "Adapt Windows Docker tests to run via WSL2 with Alpine dist and Docker Desktop auto-start. Docker tests currently fail on Windows because docker CLI is not found. The solution uses WSL2 Alpine dist to run docker commands, auto-starts Docker Desktop via PowerShell if not running, and uses relative paths for Docker Compose mounts."

## Clarifications

### Session 2026-04-15

- Q: Should Docker CLI be pre-installed in Alpine or auto-installed if missing? → A: Auto-install Docker CLI in Alpine if missing (adds ~30s to first test run).
- Q: Should Docker Compose bind mount include entire repo root or only fixture + artifact paths? → A: Mount only fixture directory + artifact volume (smaller mount, requires path changes in entrypoints).
- Q: Should SSH mode be included in initial Windows implementation or deferred? → A: Include SSH mode in initial Windows implementation (all 3 modes: socket, via, ssh).
- Q: Should the Docker Desktop startup timeout be hardcoded or configurable? → A: Two-tier timeout: independent timeout per step/command, conservative overall timeout for the entire test.
- Q: How should Docker CLI be installed in Alpine dist? → A: Install via `apk add docker-cli` (standard Alpine package, handles dependencies).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run remote xdist tests on Windows via WSL2 Docker (Priority: P1)

A developer on Windows runs the remote xdist tox environment (`py314-pytestlatest-xdist-remote-socket-win`). The test framework detects Docker Desktop is not running, starts it automatically via PowerShell, then uses WSL2 Alpine dist to execute Docker Compose commands. The remote xdist tests (socket, via, ssh modes) pass successfully.

**Why this priority**: This is the core functionality — enabling Docker-dependent tests to run on Windows, which is currently broken.

**Independent Test**: Can be fully tested by running `uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-socket-win` on a Windows machine with Docker Desktop installed and WSL2 Alpine dist configured.

**Acceptance Scenarios**:

1. **Given** Docker Desktop is not running, **When** the test starts, **Then** Docker Desktop is started automatically and the test proceeds
2. **Given** Docker Desktop is running, **When** the test starts, **Then** Docker is detected immediately and the test proceeds without startup delay
3. **Given** WSL2 Alpine dist is configured, **When** Docker commands are needed, **Then** they execute via `wsl -d Alpine docker ...`

---

### User Story 2 - Docker detection fails gracefully when prerequisites missing (Priority: P2)

A developer on Windows without Docker Desktop or without WSL2 Alpine dist runs the remote xdist tests. The test framework provides a clear failure message explaining what is missing rather than a cryptic error.

**Why this priority**: Developers need actionable feedback when prerequisites are missing, not silent skips or confusing tracebacks.

**Independent Test**: Can be tested by running the tests on a Windows machine without Docker Desktop installed.

**Acceptance Scenarios**:

1. **Given** Docker Desktop is not installed, **When** the test starts, **Then** the test fails with "Docker Desktop not installed"
2. **Given** WSL2 Alpine dist does not exist, **When** the test starts, **Then** the test fails with "WSL2 Alpine dist not found"
3. **Given** Docker Desktop starts but fails to initialize, **When** the per-step timeout expires, **Then** the test fails with "Docker Desktop did not start within timeout"

---

### User Story 3 - Linux and macOS behavior unchanged (Priority: P3)

A developer on Linux or macOS runs the same remote xdist tests. The tests behave exactly as before — using native `docker` commands with no WSL2 involvement.

**Why this priority**: Backward compatibility ensures the change doesn't break existing CI/CD pipelines on Linux/macOS.

**Independent Test**: Can be tested by running the Linux tox environments on a Linux machine.

**Acceptance Scenarios**:

1. **Given** Linux environment with native `docker`, **When** Docker detection runs, **Then** native docker is used (no WSL2 fallback attempted)
2. **Given** macOS environment with native `docker`, **When** Docker detection runs, **Then** native docker is used

---

### Edge Cases

- Docker Desktop is running but `docker info` returns an error (e.g., daemon crash) → retry logic handles transient failures
- WSL2 Alpine dist exists but docker CLI is not installed inside it → Docker CLI is auto-installed before proceeding
- Docker Compose bind mount fails due to file sharing restrictions → test fails with Docker Compose error
- Controller entrypoint and worker scripts must be self-contained (no imports from repo root outside fixture directory)
- PowerShell execution policy blocks `Start-Process` → fail with clear message
- Multiple WSL2 dists exist → only Alpine dist is used (hardcoded)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect Docker availability by trying native `docker info` first, then falling back to `wsl -d Alpine docker info`
- **FR-002**: System MUST attempt to start Docker Desktop via PowerShell `Start-Process "docker-desktop" -WindowStyle Hidden` when not running
- **FR-003**: System MUST apply independent timeout per Docker operation (startup poll, compose up, compose exec, compose cp) and a conservative overall timeout for the entire test run
- **FR-004**: System MUST fail (not skip) when any Docker operation exceeds its per-step timeout or when the overall test timeout expires
- **FR-005**: System MUST fail (not skip) when WSL2 Alpine dist is not found
- **FR-006**: System MUST route all Docker Compose commands through `wsl -d Alpine docker compose ...` when the backend is WSL2
- **FR-007**: System MUST use relative paths in Docker Compose bind mounts, mounting only the fixture directory and artifact volume (not the entire repo root)
- **FR-008**: System MUST preserve native Docker behavior on Linux and macOS (no WSL2 involvement)
- **FR-009**: System MUST provide clear failure messages for each prerequisite (Docker Desktop, WSL2 Alpine, Docker CLI inside Alpine)
- **FR-010**: New tox environments with `-win` suffix MUST be added for socket, via, and ssh remote modes
- **FR-011**: System MUST auto-install Docker CLI inside WSL2 Alpine dist via `apk add docker-cli` if not present, before executing Docker commands

### Key Entities

- **DockerBackend**: The detected Docker execution backend — either `"native"` (direct docker CLI) or `"wsl2"` (docker CLI inside WSL2 Alpine dist)
- **DockerClusterManager**: Orchestrates Docker Compose lifecycle (up, exec, cp, down) with awareness of the Docker backend

## Agentic Validation Constraints

- **TDD Contract**: The specifications detailed here form the "WHAT" defined by Speckit. They must be rigid enough to drive automated RED-GREEN-REFACTOR cycles by subagents leveraging Superpowers.
- **Validation**: All acceptance scenarios must be mechanically verifiable without human intuition to serve as strict unit-test targets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 3 remote xdist test modes (socket, via, ssh) pass on Windows when Docker Desktop and WSL2 Alpine are available
- **SC-002**: Docker Desktop auto-start completes within the per-step timeout in 95% of cases on a typical Windows development machine
- **SC-003**: Tests fail with actionable error messages (not tracebacks) within 5 seconds when prerequisites are missing
- **SC-004**: Linux and macOS tox environments pass with zero behavioral changes (same test results as before this feature)

## Assumptions

- Docker Desktop for Windows is installed on the target machine
- WSL2 is enabled on Windows with an Alpine dist available
- The Alpine dist does not require Docker CLI pre-installed; it will be auto-installed on first use
- Docker Desktop's WSL2 integration is enabled (allows WSL2 dists to access the Docker daemon)
- Repository root is accessible from WSL2 via `/mnt/c/...` path for bind mounts
- PowerShell execution policy allows `Start-Process` (default on Windows)
- The existing Docker Compose fixture files (docker-compose.yml, Dockerfiles, entrypoints) are reused with modifications to use relative paths and self-contained entrypoints
