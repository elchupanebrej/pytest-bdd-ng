# Spike Manifest

## Idea

Cross-platform test suite entrypoint using Makefile + MinGW sh as single interface.
`make test-all` runs native tests on host platform + Docker-backed tests for non-native
platforms on Windows, Linux, and macOS.

## Requirements

- [REQ-001] Single entrypoint (`make test-all`) across Windows, macOS, Linux
- [REQ-002] env-check read-only validation; env-install explicit one-time provisioning
- [REQ-003] Docker images from public registries (Alpine Linux, Windows Server Core)
- [REQ-004] Per-platform setup documented in DEVELOPMENT.rst
- [REQ-005] Windows: Git for Windows `sh.exe` as Make SHELL, Docker Desktop daemon accessible
- [REQ-006] No wrapper scripts — all logic in the Makefile itself

## Spikes

| # | Name | Type | Validates | Verdict | Tags |
|---|------|------|-----------|---------|------|
| 001 | win-docker-minimal-image | standard | Given a Windows Docker container with Python 3.10+, when pytest-bdd test suite runs, then tests pass in reasonable time | PARTIAL | docker, windows, python |
| 002 | mingw-make-integration | standard | Given MinGW sh as Make SHELL with Docker bin on PATH, when `make env-check-docker` runs, then docker detected and test-docker executes | VALIDATED | make, mingw, windows, docker |
| 003 | makefile-cross-platform | standard | Given a Makefile with OS-conditional SHELL and target routing, when `make test-all` runs on Win/Linux/Mac, then correct native+Docker targets fire | VALIDATED | make, cross-platform |
| 004 | vulture-pre-commit-hook | standard | Given the existing vulture dead-code pytest gate, when it is moved to a separate pre-commit hook, then it runs outside pytest and still allows known false positives while failing unknown dead code | VALIDATED | pre-commit, vulture, quality-gate, pytest |
