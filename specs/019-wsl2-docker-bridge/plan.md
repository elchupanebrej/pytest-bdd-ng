# Implementation Plan: WSL2 Docker Bridge for Windows

**Branch**: `019-wsl2-docker-bridge` | **Date**: 2026-04-15 | **Spec**: [specs/019-wsl2-docker-bridge/spec.md](../spec.md)
**Input**: Feature specification from `/specs/019-wsl2-docker-bridge/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Adapt Windows Docker test infrastructure to run via WSL2 Alpine dist with Docker Desktop auto-start. The test framework detects Docker availability, starts Docker Desktop via PowerShell if needed, routes Docker Compose commands through `wsl -d Alpine`, uses relative bind mounts, and auto-installs Docker CLI in Alpine via `apk`. All 3 remote xdist modes (socket, via, ssh) are included. Linux/macOS behavior is preserved unchanged.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `subprocess`, `pytest`, `pytest-xdist`, `docker compose`, WSL2
**Storage**: N/A (test infrastructure, no persistent storage)
**Testing**: pytest via tox environments (`py314-pytestlatest-xdist-remote-{socket,via,ssh}-win`)
**Target Platform**: Windows 10/11 with WSL2 (Alpine dist) + Docker Desktop; Linux/macOS unchanged
**Project Type**: Test infrastructure / CI tooling
**Performance Goals**: Docker Desktop auto-start within per-step timeout; test overhead <30s for CLI install
**Constraints**: WSL2 Alpine dist must be available; Docker Desktop must be installed; relative bind mounts only (fixture dir + artifact volume)
**Scale/Scope**: 3 remote modes (socket, via, ssh); 4 files modified; backward compatible with Linux/macOS

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Pure BDD Integration)**: N/A — This is test infrastructure, not BDD feature code. No impact.
- **Principle II (Realistic Runtime Evidence)**: N/A — No changes to reporter or runtime evidence collection.
- **Principle III (Explicit Returns & Determinism)**: PASS — All new functions will use explicit return values or raise deterministic exceptions. No `None` returns outside pytest hooks.
- **Principle IV (Broad Compatibility)**: PASS — Python 3.10-3.14 compatibility maintained. No new Python version requirements. Changes are platform-specific (Windows only via tox platform filter).
- **Principle V (Quality & Formatting Discipline)**: PASS — All code follows existing `ruff` and `pre-commit` standards. Documentation in English.
- **Development Practice (Docker for non-native)**: PASS — This feature *enables* Docker-based testing on Windows via WSL2, aligning with the requirement that "non-native platform test environments must use the Docker skill (Windows targets exempt)."

## Agentic Implementation Strategy

**Superpowers**:
- `test-driven-development` — All code changes follow RED-GREEN-REFACTOR cycle
- `systematic-debugging` — For any test failures during implementation

**Subagent Dispatch**:
- Task 1: WSL2-aware Docker detection (`tests/support/docker.py`) — dispatch with TDD
- Task 2: WSL2-aware Docker Compose orchestration (`tests/support/docker_cluster.py`) — dispatch with TDD
- Task 3: Docker Compose relative path mounts (`docker-compose.yml` + entrypoint refactoring) — dispatch with TDD
- Task 4: Tox environment additions (`tox.ini`) — simple config change, no subagent needed
- Task 5: Alpine Docker CLI auto-install — integrated into Task 1 or 2

## Project Structure

### Documentation (this feature)

```text
specs/019-wsl2-docker-bridge/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
tests/
├── support/
│   ├── docker.py              # WSL2-aware Docker detection + Desktop startup
│   └── docker_cluster.py      # WSL2-aware Docker Compose orchestration
└── e2e/
    └── fixtures/
        └── remote_xdist/
            ├── docker-compose.yml    # Relative path mounts
            ├── controller_entrypoint.py  # Self-contained (no repo root imports)
            └── worker_entrypoint.py      # Self-contained
tox.ini                          # New -win tox environments
```

**Structure Decision**: Single project layout. Only test support files and fixture configuration are modified. No new source directories created. The existing `tests/support/` and `tests/e2e/fixtures/remote_xdist/` directories are extended with WSL2-aware behavior.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. All principles pass.
