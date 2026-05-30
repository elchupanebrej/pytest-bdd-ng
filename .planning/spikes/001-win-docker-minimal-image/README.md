---
spike: 001
name: win-docker-minimal-image
type: standard
validates: "Given a Windows Docker container with Python 3.10+, when pytest-bdd test suite runs, then tests pass in reasonable time"
verdict: PARTIAL
related: []
tags: [docker, windows, python, containers]
---

# Spike 001: Windows Docker Minimal Image

## What This Validates

Given a Windows Docker container with Python 3.10+, when the pytest-bdd test suite runs,
then all non-windows-marked tests pass in reasonable time.

## Research

### Windows Container Base Images (Microsoft Learn, 2025-11)

| Base Image | Size (compressed) | API Surface | Python Support |
|------------|-------------------|-------------|----------------|
| **Nano Server** | ~300 MB | Minimal (.NET Core only) | **No** — no MSVC, no PowerShell, no pip C-ext compilation |
| **Server Core** | ~4 GB | Full Windows API | **Yes** — official Python images built on this |
| **Windows** | ~3.4 GB | Full API + GUI libs | Overkill for test runner |
| **Windows Server** | ~3.1 GB | Full API + GPU | Overkill for test runner |

### Python Docker Images (Docker Hub, official)

- Official Windows Python images: `python:3.10` through `python:3.14`
- ALL Windows variants are based on `mcr.microsoft.com/windows/servercore`
- NO Nano Server variant exists — Python requires Server Core API surface
- Tags: `python:3.14-windowsservercore-ltsc2022`, `python:3.14-windowsservercore-ltsc2025`

### Key Finding: Nano Server Invalidated

Nano Server lacks PowerShell, MSVC runtime, Windows servicing stack, and the full Windows API.
Python packages that compile C extensions (common in test tooling: `execnet`, `filelock`,
`lxml`, etc.) require the full Windows SDK unavailable on Nano Server. No lighter option exists.

## Approach Comparison

| Approach | Tool/Library | Pros | Cons | Verdict |
|----------|-------------|------|------|---------|
| Server Core + Python official | `python:3.14-windowsservercore-ltsc2022` | Pre-built Python, all deps compile, official image | ~8 GB compressed, Docker mode switch required, slow pull | **Chosen** |
| Server Core + custom install | `servercore:ltsc2022` + manual Python | Slightly smaller | More maintenance, slower build, same underlying OS | Not worth it |
| Nano Server + Python | `nanoserver:ltsc2022` | ~300 MB | Python doesn't work. No MSVC, no PowerShell, pip fails | **INVALIDATED** |
| WSL2 Linux container | `python:3.14` | Small, fast | Runs Linux tests, NOT Windows tests. Wrong target. | Wrong target |

### Chosen Approach

`python:3.14-windowsservercore-ltsc2022` — the official Python Docker image for Windows.
No lighter alternative exists.

### Docker Desktop Mode Constraint

Docker Desktop must run in **Windows containers mode**. This is a mode switch that:
- Requires Docker Desktop restart (~30 seconds)
- Switches ALL containers to Windows (no Linux containers while in Windows mode)
- Docker Desktop 4.34+ can run both modes simultaneously via containerd image store
  (but this machine runs Docker Desktop 4.10.1 which requires explicit switching)

## How to Run

Not executable on this machine without switching Docker Desktop to Windows containers mode,
which would disrupt current Linux containers. Verified image exists:

```powershell
docker manifest inspect python:3.14-windowsservercore-ltsc2022
# Confirmed: amd64 manifest available on Docker Hub
```

To pull and test (requires Docker Desktop in Windows containers mode):
```powershell
docker pull python:3.14-windowsservercore-ltsc2022
# Build a test image with pytest-bdd deps, mount source, run tests
```

## Investigation Trail

1. **Checked Docker Desktop mode**: Currently Linux containers mode. `docker info --format "{{.OSType}}"` returns `linux`.

2. **Verified image existence**: `docker manifest inspect python:3.14-windowsservercore-ltsc2022` confirms image available on Docker Hub with amd64 manifest.

3. **Researched base images**: Microsoft Learn docs enumerate 4 base images. Only Server Core supports Python.

4. **Confirmed no Nano Server Python**: Searched Docker Hub for `python nanoserver` — no results. Official Python images are Server Core only. Community projects attempting Nano Server + Python exist but are unmaintained and broken.

5. **Size estimation**: The `python:3.13.13-trixie` (Linux) tag is 393.4 MB compressed. Windows Server Core tags are typically 4-8 GB compressed, 12-16 GB uncompressed. This is the practical ceiling for the Windows test image.

## Results

**Verdict: PARTIAL** — Feasible but constrained.

**What works:**
- Official Python Docker images exist for Windows (Server Core)
- All Python 3.10-3.14 versions available
- Image accessible from Docker Hub
- Full Python dependency tree expected to compile (Server Core has full Windows SDK)

**Constraints for real implementation:**
- Image size: ~8 GB compressed, expect 30-60 min pull time on typical connection
- Docker Desktop must switch to Windows containers mode (restart, no Linux containers concurrently)
- Require Docker Desktop 4.34+ for simultaneous Linux + Windows container support
  (or accept mode switching in older versions)
- Windows 10/11 Pro or Enterprise required (Home edition does NOT support Windows containers)
- Build time for test Dockerfile (pip install all deps) likely 10-20 minutes

**Surprising finding:** There is genuinely no lighter option. Nano Server was explored and
is fundamentally incompatible with Python. Server Core is the absolute minimum.
