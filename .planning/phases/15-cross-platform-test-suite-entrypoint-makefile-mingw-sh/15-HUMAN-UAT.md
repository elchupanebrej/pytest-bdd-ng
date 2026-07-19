---
status: partial
phase: 15-cross-platform-test-suite-entrypoint-makefile-mingw-sh
source: [VERIFICATION.md]
started: 2026-05-24T00:34:56+03:00
updated: 2026-05-27T22:46:13+03:00
---

# Phase 15 Human UAT

## Current Test

[testing paused - 1 item outstanding]

## Tests

### 1. Windows real backend run

expected: Run `make test-all` from Git Bash on Windows with WSL2 and Docker Desktop available. PowerShell native Windows tox, WSL2 Linux tox, Docker/external work, and report rendering follow documented collect/fail-fast behavior.
result: pass

### 2. Linux/macOS real backend run

expected: Run `make test-all` on Linux and macOS hosts with Docker configured for requested non-native backends. Linux/macOS route Windows tox through validated Windows Docker or equivalent VM-like backend and route Linux/macOS native tox as documented.
result: skipped

## Summary

total: 2
passed: 1
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps
