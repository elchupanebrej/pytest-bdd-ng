# Spike Conventions

Patterns and stack choices established across spike sessions. New spikes follow these unless the question requires otherwise.

## Stack

- **Makefiles** with GNU Make 4.4+ for cross-platform test orchestration
- **MinGW/Git Bash sh.exe** as SHELL on Windows (via Git for Windows)
- **Docker** for non-native platform test targets (Alpine Linux, Windows Server Core)
- **PowerShell** for Windows-native CLI interaction (but NOT as Make SHELL)
- **Python/pytest** as the test runner (project's own stack)

## Structure

- **Makefile variables**: `UNAME_S` for platform detection, `PLATFORM` for routing
- **Short DOS paths** on Windows: `C:/PROGRA~1/...` to avoid spaces in Makefile paths
- **`ifdef OS`** for Windows-only blocks (OS=Windows_NT), `uname -s` for detailed detection
- **`export PATH`** in Makefile for Docker bin visibility on Windows

## Patterns

- **SHELL override**: Set `SHELL := C:/PROGRA~1/Git/bin/sh.exe` on Windows (short DOS path, no spaces)
- **PATH fix**: Prepend `C:/PROGRA~1/Docker/Docker/resources/bin` to PATH for Docker CLI
- **Platform conditional**: `ifeq/else ifeq/else` chain on `UNAME_S` for target routing
- **Pre-flight checks**: `env-check` validates prerequisites read-only, fails with descriptive error
- **Docker availability**: `env-check-docker` validates docker + daemon + compose before Docker targets

## Tools & Libraries

- **GNU Make 4.4.1** (Chocolatey package on Windows)
- **Git for Windows** (provides `sh.exe` at `C:\Program Files\Git\bin\`)
- **Docker Desktop 4.10.1+** (provides `docker.exe` at `C:\Program Files\Docker\Docker\resources\bin\`)
- **Windows Server Core** base image for Windows Docker containers (Python doesn't run on Nano Server)
- **Alpine Linux** base image for Linux Docker containers (lightweight)
