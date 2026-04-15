# Quickstart: WSL2 Docker Bridge for Windows

## Prerequisites

1. **Windows 10/11** with WSL2 enabled
2. **Docker Desktop for Windows** installed
3. **WSL2 Alpine dist** installed (e.g., `wsl --install -d Alpine`)
4. **Docker Desktop WSL2 integration** enabled (Settings → Resources → WSL Integration → enable Alpine)

## Setup Alpine in WSL2

```powershell
# Install Alpine dist (if not already installed)
wsl --install -d Alpine

# Enable Docker Desktop integration for Alpine
# (Open Docker Desktop → Settings → Resources → WSL Integration → toggle Alpine on)
```

## Running the Tests

```powershell
# Activate your virtual environment
.\.windows_venv\Scripts\activate

# Run remote xdist tests for a specific mode
uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-socket-win
uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-via-win
uvx --with tox-uv tox -e py314-pytestlatest-xdist-remote-ssh-win
```

## What Happens

1. Test detects Docker availability (native → WSL2 Alpine)
2. If Docker Desktop is not running, it starts automatically via PowerShell
3. Docker CLI is auto-installed in Alpine if missing (`apk add docker-cli`)
4. Docker Compose starts the controller/worker cluster
5. Tests execute inside the container via `docker compose exec`
6. Results are copied back and verified
7. Cluster is cleaned up

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "WSL2 Alpine dist not found" | Alpine not installed | `wsl --install -d Alpine` |
| "Docker Desktop not installed" | Docker Desktop missing | Install from docker.com |
| "Docker Desktop did not start within timeout" | Docker Desktop failed to start | Check Docker Desktop logs, restart |
| "Failed to install docker-cli in Alpine" | Network or package issue | Run `wsl -d Alpine -u root -- apk update` manually |
| "docker compose up failed" | Bind mount or port conflict | Check Docker Desktop file sharing settings |
