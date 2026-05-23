---
title: Fix Makefile SHELL for cross-platform (Win/Mac/Linux)
date: 2026-05-21
priority: medium
---

## Goal

Makefile works as single entrypoint (`make test-all`) on Windows (PowerShell + MinGW), macOS, and Linux.

## Tasks

- [ ] Set `SHELL` in Makefile to auto-detect Git Bash `sh.exe` on Windows, default `sh` elsewhere
- [ ] Fix `env-check` for Windows: validate `sh.exe` and `docker.exe` are on PATH
- [ ] Create `env-install` for Windows: add Git bin + Docker bin to machine PATH
- [ ] Create per-platform Docker image pull scripts (Alpine Linux, lightweight Windows)
- [ ] Document per-platform setup in DEVELOPMENT.rst
- [ ] Verify `make test-all` works on Windows (Git Bash), macOS, and Linux
