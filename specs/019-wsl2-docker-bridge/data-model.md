# Data Model: WSL2 Docker Bridge

## Entities

### DockerBackend

**Description**: Represents the detected Docker execution backend. Determines how Docker commands are routed.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Backend identifier: `"native"` or `"wsl2"` |
| `distro` | `str \| None` | WSL2 distro name (only when `name == "wsl2"`, hardcoded `"Alpine"`) |
| `available` | `bool` | Whether the backend is accessible |

**Validation rules**:
- `name` must be one of `"native"`, `"wsl2"`
- If `name == "wsl2"`, `distro` must be a non-empty string
- `available` must be `True` for the backend to be used

**State transitions**:
- Detection: `available=False` → `available=True` (after successful `docker info`)
- Startup: `available=False` → attempt Docker Desktop start → poll → `available=True` or `pytest.fail()`

---

### DockerTimeouts

**Description**: Per-operation and overall timeout configuration for Docker operations.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `startup_poll` | `int` | 60 | Max seconds for Docker Desktop startup polling |
| `compose_up` | `int` | 120 | Max seconds for `docker compose up` |
| `compose_exec` | `int` | 300 | Max seconds for `docker compose exec` (test run) |
| `compose_cp` | `int` | 30 | Max seconds for `docker compose cp` |
| `compose_down` | `int` | 30 | Max seconds for `docker compose down` |
| `alpine_install` | `int` | 60 | Max seconds for `apk add docker-cli` |
| `overall_session` | `int` | 600 | Max seconds for entire test session |

**Validation rules**:
- All values must be positive integers
- `overall_session` must be >= sum of all per-step timeouts

---

### DockerClusterManager

**Description**: Orchestrates Docker Compose lifecycle with awareness of the Docker backend.

| Field | Type | Description |
|-------|------|-------------|
| `backend` | `DockerBackend` | Detected Docker backend |
| `compose_file` | `Path` | Path to docker-compose.yml |
| `artifact_dir` | `Path` | Directory for test artifacts |
| `timeouts` | `DockerTimeouts` | Timeout configuration |
| `session_start` | `float \| None` | Timestamp when session started (for overall timeout tracking) |

**Methods**:
- `get_cluster() -> None` — Runs `docker compose up -d --build`
- `run_in_controller(cmd: list[str]) -> CompletedProcess` — Runs `docker compose exec controller <cmd>`
- `copy_from_container(src: str, dst: Path) -> None` — Runs `docker compose cp`
- `cleanup() -> None` — Runs `docker compose down --volumes`
- `_run_docker_cmd(args: list[str], timeout: int) -> CompletedProcess` — Internal: routes command through native or WSL2 backend

**State transitions**:
- `None` → `get_cluster()` → cluster running
- cluster running → `run_in_controller()` → test results
- cluster running → `cleanup()` → cluster stopped
- Any state → timeout exceeded → `pytest.fail()`

---

## Relationships

```
DockerClusterManager
  ├── backend: DockerBackend (1:1)
  ├── timeouts: DockerTimeouts (1:1)
  └── compose_file: Path (references docker-compose.yml)
```

## External Interfaces

### WSL2 CLI Interface

| Command | Purpose | Exit Code 0 Means |
|---------|---------|-------------------|
| `wsl -l -v` | List WSL dists | Command succeeded |
| `wsl -d Alpine -- which docker` | Check Docker CLI | Docker CLI is installed |
| `wsl -d Alpine -u root -- apk add --no-cache docker-cli` | Install Docker CLI | Installation succeeded |
| `wsl -d Alpine -- docker info` | Check Docker daemon | Docker daemon is running |
| `wsl -d Alpine -- docker compose up -d --build` | Start cluster | Cluster started |
| `wsl -d Alpine -- docker compose exec controller <cmd>` | Run command in container | Command succeeded |
| `wsl -d Alpine -- docker compose cp <src> <dst>` | Copy artifacts | Copy succeeded |
| `wsl -d Alpine -- docker compose down --volumes` | Stop cluster | Cluster stopped |

### PowerShell Interface

| Command | Purpose |
|---------|---------|
| `Start-Process "docker-desktop" -WindowStyle Hidden` | Launch Docker Desktop |

### Docker Compose Volume Mounts

| Source | Target | Type |
|--------|--------|------|
| `.` (fixture dir) | `/workspace` | bind |
| `${ARTIFACT_DIR:-./artifacts}` | `/artifacts` | bind |
