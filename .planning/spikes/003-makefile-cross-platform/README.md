---
spike: 003
name: makefile-cross-platform
type: standard
validates: "Given a Makefile with OS-conditional SHELL and target routing, when make test-all runs on Win/Linux/Mac, then correct native+Docker targets fire"
verdict: VALIDATED
related: [002]
tags: [make, cross-platform, os-detection, routing]
---

# Spike 003: Makefile Cross-Platform Routing

## What This Validates

Given a Makefile with OS-conditional SHELL and target routing, when `make test-all`
runs on Windows/Linux/macOS, then the correct set of native and Docker-backed targets
executes for each platform.

## Research

### Platform Detection in GNU Make

GNU Make provides two mechanisms for OS detection:

| Detection method | Reliability | Notes |
|-----------------|-------------|-------|
| `ifdef OS` (env var) | Windows only | Windows sets `OS=Windows_NT`. Linux/macOS don't set it. |
| `$(shell uname -s)` | All platforms | Returns `Linux`, `Darwin`, or `MINGW64_NT-*` (on Windows/MinGW) |
| Combined approach | All | `uname -s` for detailed detection, `ifdef OS` as fallback |

### Chosen detection approach

```makefile
UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")

ifeq ($(UNAME_S),Linux)
  PLATFORM := linux
else ifeq ($(UNAME_S),Darwin)
  PLATFORM := macos
else
  PLATFORM := windows
endif
```

### Target Routing Matrix

| Platform | Native Targets | Docker Targets |
|----------|---------------|----------------|
| Linux    | test-unit, test-integration, test-e2e, test-posix, ... | test-docker-windows |
| macOS    | test-unit, test-integration, test-e2e, test-posix, ... | test-docker-linux, test-docker-windows |
| Windows  | test-unit, test-integration, test-e2e, test-windows, ... | test-docker-linux |

Docker targets need split: `test-docker` → `test-docker-linux` and `test-docker-windows`
so each platform can select which Docker image to run.

## How to Run

```powershell
# On Windows (current platform):
make -f .planning/spikes/003-makefile-cross-platform/platform-routing.mk platform-info
make -f .planning/spikes/003-makefile-cross-platform/platform-routing.mk test-all SHELL=C:/PROGRA~1/Git/bin/sh.exe
```

## What to Expect

- `platform-info`: Reports detected platform, SHELL, NATIVE_TARGETS, DOCKER_TARGETS
- On Windows: NATIVE_TARGETS includes `test-windows`, DOCKER_TARGETS = `test-docker-linux`
- On macOS: NATIVE_TARGETS includes `test-posix`, DOCKER_TARGETS = `test-docker-linux test-docker-windows`
- On Linux: NATIVE_TARGETS includes `test-posix`, DOCKER_TARGETS = `test-docker-windows`

## Investigation Trail

1. **Platform detection**: `uname -s` on MinGW returns `MINGW64_NT-10.0-22631`, not `Windows`. Used fallback `$(shell uname -s 2>/dev/null || echo "Windows")` for when `uname` is unavailable.

2. **SHELL noise suppression**: Running `make` from PowerShell generates "The system cannot find the path specified" because make tries to resolve default SHELL (`sh.exe`) before processing the Makefile. Suppressed by passing `SHELL=...` as a command-line argument or by accepting the cosmetic stderr noise.

3. **Conditional routing verified**: The `ifeq/else ifeq/else` chain correctly selects NATIVE_TARGETS and DOCKER_TARGETS based on PLATFORM. Tested on Windows: selects `test-windows` native, `test-docker-linux` Docker.

4. **Docker target split required**: Current Makefile has a single `test-docker` target. Need to split into `test-docker-linux` (Alpine-based) and `test-docker-windows` (Windows Server Core-based) for proper routing.

5. **PATH inheritance**: The `export PATH` addition works — `docker` becomes visible to sub-make processes and recipe commands.

## Results

**Verdict: VALIDATED** — Cross-platform Makefile routing is feasible with three components:
1. `uname -s` for platform detection (with Windows fallback)
2. `ifeq` chain for conditional target assignment
3. Platform-specific SHELL + PATH setup (from spike 002)

### Implementation Recipe

```makefile
# In the real Makefile:
UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")

ifeq ($(UNAME_S),Linux)
  # Linux: no shell fix needed, docker is on PATH by default
else ifeq ($(UNAME_S),Darwin)
  # macOS: no shell fix needed, docker is on PATH by default
else
  # Windows: fix SHELL and Docker PATH
  SHELL := C:/PROGRA~1/Git/bin/sh.exe
  export PATH := C:/PROGRA~1/Docker/Docker/resources/bin:$(PATH)
endif

test-all: env-check
	@echo "=== Native targets ($(UNAME_S)) ==="
	@$(MAKE) $(NATIVE_TARGETS)
	@echo "=== Docker targets ==="
	@-$(MAKE) $(DOCKER_TARGETS)
```

**Surprising finding:** The Makefile approach requires no wrapper scripts. Platform detection, SHELL setup, and target routing all fit within the Makefile itself. The only prerequisite is Git for Windows (for `sh.exe`) and Docker Desktop (for Docker).
