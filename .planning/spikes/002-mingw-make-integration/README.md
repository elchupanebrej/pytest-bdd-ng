---
spike: 002
name: mingw-make-integration
type: standard
validates: "Given MinGW sh as Make SHELL with Docker bin on PATH, when make env-check-docker runs, then docker detected and test targets execute"
verdict: VALIDATED
related: [003]
tags: [make, mingw, windows, docker, shell]
---

# Spike 002: MinGW Make Integration on Windows

## What This Validates

Given MinGW `sh` as Make SHELL with Docker bin on PATH, when `make env-check-docker`
runs, then docker daemon is detected and test targets execute correctly.

## Research

### Make SHELL Resolution on Windows

GNU Make for Windows (Chocolatey 4.4.1) defaults to `SHELL := sh.exe`. This shell
must exist on PATH for recipes to execute. If SHELL is invalid, make falls back to
`cmd.exe` which cannot parse POSIX shell syntax (`{...}`, `command -v`, `||`, etc).

Key finding: make resolves SHELL **at startup before processing PATH exports**.
Adding Git bin to PATH in the Makefile doesn't help — SHELL must point to a valid
absolute path using a syntax make can parse.

### Docker Visibility from MinGW

Docker Desktop installs to `C:\Program Files\Docker\Docker\resources\bin\docker.exe`.
This directory is added to USER PATH (via Docker Desktop installer) but NOT to
MACHINE PATH. MinGW/MSYS2 shells inherit the machine PATH but may not see user PATH.

### Short DOS Path

Windows short file names (8.3) avoid spaces that break Makefile variable expansion.
`C:\Program Files\Git\bin\sh.exe` → `C:\PROGRA~1\Git\bin\sh.exe`

### Approach Comparison

| Approach | SHELL setting | Works? | Notes |
|----------|--------------|--------|-------|
| Default `sh.exe` | (none) | ✗ | sh.exe not on PATH, falls back to cmd.exe |
| Simple name `sh` | `SHELL := sh` | ✗ | Make can't find `sh` on PATH at startup |
| MSYS2 path `/usr/bin/bash` | `SHELL := /usr/bin/bash` | ✗ | Make ignores MSYS2 paths as invalid |
| Short DOS path + PATH fix | `SHELL := C:/PROGRA~1/Git/bin/sh.exe` + Docker in PATH | ✓ | Verified with test6.mk and integration-test.mk |

### Chosen Approach

```makefile
ifdef OS
  SHELL := C:/PROGRA~1/Git/bin/sh.exe
  export PATH := C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)
endif
```

`ifdef OS` — Windows sets `OS=Windows_NT`, Linux/macOS don't set `OS`.

## How to Run

```powershell
# Test specific targets from the integration test Makefile
make -f .planning/spikes/002-mingw-make-integration/test6.mk env-check
make -f .planning/spikes/002-mingw-make-integration/test6.mk env-check-docker

# Run actual test suite via make
make -f .planning/spikes/002-mingw-make-integration/integration-test.mk test-unit
```

## What to Expect

- `env-check`: uv and pytest detected, exits 0
- `env-check-docker`: docker, docker daemon, docker compose all detected, exits 0
- `test-unit`: 835+ tests pass (some pre-existing failures in vulture dead code tests)

## Investigation Trail

1. **Confirmed sh.exe location**: `C:\Program Files\Git\bin\sh.exe` (Git for Windows). Not on system PATH. `C:\Program Files\Git\cmd` is on PATH but contains only `git.exe`.

2. **Tested direct SHELL override**: `SHELL := sh` fails — make resolves SHELL at startup, can't find `sh` on PATH. `SHELL := /usr/bin/bash` fails — make ignores MSYS2 paths.

3. **Discovered short DOS path key**: `SHELL := C:/PROGRA~1/Git/bin/sh.exe` is the only format that works. Make accepts it as a valid Windows path and resolves it.

4. **Verified Docker PATH fix**: Adding `C:/PROGRA~1/Docker/Docker/resources/bin` to PATH inside the Makefile makes `docker` and `docker compose` visible to the shell.

5. **End-to-end test**: `make test-unit` ran 835 tests successfully via MinGW shell → uv → pytest. Shell syntax (||, {}, command -v, >/dev/null) all work.

6. **Docker compose compatibility**: `docker compose version` works — Docker Desktop 4.10.1 includes compose plugin.

## Results

**Verdict: VALIDATED** — MinGW make integration works with two fixes:
1. `SHELL := C:/PROGRA~1/Git/bin/sh.exe`
2. Docker bin added to PATH

**Surprising finding:** The fix is simpler than expected. No need for separate PowerShell scripts or complex wrappers. Two lines in the Makefile (wrapped in `ifdef OS`) and documentation of prerequisites (Git for Windows, Docker Desktop) are sufficient.

**Constraint:** The short DOS path `C:/PROGRA~1` assumes Git is on the C: drive and Windows has 8.3 filenames enabled. On systems with Git on D: or with 8.3 disabled, a fallback to `C:/Program Files/Git/bin/sh.exe` (quoted) or a wildcard-based find may be needed.
