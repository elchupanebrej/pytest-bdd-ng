---
title: Cross-platform test entrypoint architecture
date: 2026-05-21
context: /gsd-explore — entrypoint for running full test suite on MacOS, Linux, Windows
---

## Decision

Makefile + MinGW (Git Bash) `sh` as the single cross-platform entrypoint.
`make test-all` across all three platforms.

## Platform matrix

| Host    | Linux suite | Windows suite | MacOS suite |
|---------|------------|---------------|-------------|
| Linux   | native     | Docker        | —           |
| Windows | Docker     | native        | —           |
| MacOS   | Docker     | Docker        | native      |

MacOS containers don't exist (Apple licensing). MacOS is only native.

## Docker images

- Linux target: Alpine-based image from Docker Hub
- Windows target: lightweight Windows Server Core container (image not yet defined)

## Windows gaps (to fix)

1. `sh.exe` from Git for Windows (`C:\Program Files\Git\bin`) is not on system PATH — make can't find it, recipes fail
2. Docker Desktop bin (`C:\Program Files\Docker\Docker\resources\bin`) is user PATH only — MinGW inherits machine PATH, can't see `docker`

## Pattern

`env-check-*` targets remain read-only validation. `env-install-*` targets do explicit one-time provisioning.
Test targets depend on `env-check`, not `env-install`.
