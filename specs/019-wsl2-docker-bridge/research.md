# Research: WSL2 Docker Bridge for Windows

**Date**: 2026-04-15
**Feature**: 019-wsl2-docker-bridge

## Decision 1: WSL2 Alpine Dist Detection

**Context**: Need to detect if WSL2 Alpine dist exists and is accessible from Windows Python subprocess.

**Decision**: Use `wsl -l -v` output parsing to check for Alpine dist with version 2.

**Rationale**:
- `wsl -l -v` lists all WSL distributions with their versions
- Parse output for line starting with `*` (default) or containing `Alpine`
- Check version column equals `2`
- This works from Windows Python via `subprocess.run(["wsl", "-l", "-v"], capture_output=True, text=True)`

**Alternatives considered**:
- `wsl -d Alpine echo test` — simpler but conflates dist existence with dist accessibility
- Registry query — more complex, may not reflect actual WSL2 state

**Implementation**:
```python
def _alpine_wsl2_available() -> bool:
    result = subprocess.run(
        ["wsl", "-l", "-v"],
        capture_output=True, text=True, timeout=10
    )
    for line in result.stdout.splitlines():
        if "Alpine" in line and "2" in line.split()[-1]:
            return True
    return False
```

---

## Decision 2: WSL2 Command Execution Pattern

**Context**: Need to run Docker commands inside WSL2 Alpine dist from Windows Python subprocess.

**Decision**: Use `wsl -d Alpine -- <command>` pattern for all Docker operations.

**Rationale**:
- `wsl -d Alpine` specifies the target distro
- `--` separates WSL flags from the command to execute
- Command runs inside the Alpine dist's default user context
- Stdout/stderr are captured and returned to Windows caller
- Exit code propagates correctly

**Alternatives considered**:
- `wsl --exec <command>` — same behavior, `--` is more standard
- `bash -c` wrapper — unnecessary complexity

**Implementation**:
```python
def _run_wsl_cmd(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    cmd = ["wsl", "-d", "Alpine", "--"] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
```

---

## Decision 3: Docker CLI Auto-Install in Alpine

**Context**: Need to install `docker-cli` in Alpine via `apk` if not present.

**Decision**: Check `wsl -d Alpine -- which docker` first, then run `wsl -d Alpine -- apk add --no-cache docker-cli` if missing.

**Rationale**:
- `which docker` is fast check (no install needed if present)
- `apk add --no-cache` avoids downloading package index cache (faster, less disk)
- Requires root or sudo in Alpine — use `wsl -d Alpine -u root --` for elevated commands
- `docker-cli` package is the correct Alpine package name (not `docker`)

**Alternatives considered**:
- Install via Docker's official static binary — more complex, no package management
- Pre-bake Docker CLI into Alpine image — requires user to rebuild image

**Implementation**:
```python
def _ensure_docker_cli_in_alpine(timeout: int = 60) -> None:
    check = subprocess.run(
        ["wsl", "-d", "Alpine", "--", "which", "docker"],
        capture_output=True, text=True, timeout=10
    )
    if check.returncode != 0:
        install = subprocess.run(
            ["wsl", "-d", "Alpine", "-u", "root", "--",
             "apk", "add", "--no-cache", "docker-cli"],
            capture_output=True, text=True, timeout=timeout
        )
        if install.returncode != 0:
            pytest.fail(f"Failed to install docker-cli in Alpine: {install.stderr}")
```

---

## Decision 4: Docker Compose Relative Path Mounts

**Context**: Current docker-compose.yml uses `REPO_ROOT` env var for absolute path bind mount. Need to use relative paths.

**Decision**: Use Docker Compose's `--project-directory` flag or relative `source` paths in volumes section.

**Rationale**:
- Docker Compose resolves relative paths from the compose file's directory
- The compose file is at `tests/e2e/fixtures/remote_xdist/docker-compose.yml`
- Fixture directory contains: `controller_entrypoint.py`, `worker_entrypoint.py`, `Dockerfiles`
- Bind mount only the fixture directory: `source: .` → `target: /workspace`
- Artifact directory stays as a named volume or separate bind mount
- Controller entrypoint must be self-contained (no `import sys; sys.path.append(...)` for repo root)

**Alternatives considered**:
- Mount entire repo root via `../../..` — larger mount, unnecessary for self-contained entrypoints
- Use Docker build context to COPY files into image — loses ability to edit fixtures without rebuild

**Implementation** (docker-compose.yml):
```yaml
services:
  controller:
    volumes:
      - type: bind
        source: .
        target: /workspace
      - type: bind
        source: ${ARTIFACT_DIR:-./artifacts}
        target: /artifacts
```

---

## Decision 5: Self-Contained Controller Entrypoint

**Context**: Current `controller_entrypoint.py` may import from repo root (`tests/`, `src/`). With fixture-only mount, these imports fail.

**Decision**: Refactor entrypoint to be fully self-contained — no imports from outside the fixture directory.

**Rationale**:
- Entrypoint needs: pytest, pytest-xdist, subprocess, socket, time, json, pathlib
- All are standard library or installed in Docker image via `pip install pytest pytest-xdist`
- The entrypoint orchestrates pytest execution inside the container — it doesn't need pytest-bdd source code
- NDJSON report verification can be done with standard library `json` module
- Fake formatter telemetry reading uses standard `pathlib` and `json`

**Alternatives considered**:
- Mount entire repo root — simpler but violates the "fixture-only mount" decision
- COPY pytest-bdd into Docker image — loses ability to test against local source changes

**Implementation**:
- Remove `from tests.support.cucumber_formatters import ...` imports
- Inline the needed helper functions (read_fake_formatter_telemetry, etc.)
- Or move needed helpers into the fixture directory itself

---

## Decision 6: Docker Desktop Startup via PowerShell

**Context**: Need to start Docker Desktop from Python subprocess on Windows.

**Decision**: Use `powershell -Command "Start-Process 'docker-desktop' -WindowStyle Hidden"` via subprocess.

**Rationale**:
- `Start-Process` launches the Docker Desktop application
- `-WindowStyle Hidden` prevents a visible window
- Docker Desktop executable is registered in Windows Start Menu / Program Files
- Polling `docker info` (or `wsl -d Alpine docker info`) every 2 seconds detects readiness
- 60-second overall timeout for startup is sufficient for typical machines

**Alternatives considered**:
- Direct path to `docker-desktop.exe` — path varies by installation
- `os.startfile("docker-desktop:")` — URI protocol may not be registered

**Implementation**:
```python
def _start_docker_desktop() -> None:
    subprocess.run(
        ["powershell", "-Command", "Start-Process", "docker-desktop", "-WindowStyle", "Hidden"],
        timeout=10
    )
```

---

## Decision 7: Two-Tier Timeout Strategy

**Context**: Spec requires independent timeout per step and conservative overall timeout.

**Decision**: Define timeout constants per operation type, plus an overall session timeout.

**Rationale**:
- Per-step timeouts:
  - Docker Desktop startup poll: 60s total (2s interval)
  - `docker compose up`: 120s (build + start)
  - `docker compose exec`: 300s (test execution)
  - `docker compose cp`: 30s (artifact copy)
  - `docker compose down`: 30s (cleanup)
  - Alpine CLI install: 60s
- Overall session timeout: 600s (10 minutes)
- Each operation tracks elapsed time; if any single operation exceeds its timeout, fail immediately
- If total elapsed time exceeds session timeout, fail with "overall test timeout exceeded"

**Implementation**:
```python
@dataclass
class DockerTimeouts:
    startup_poll: int = 60
    compose_up: int = 120
    compose_exec: int = 300
    compose_cp: int = 30
    compose_down: int = 30
    alpine_install: int = 60
    overall_session: int = 600
```
