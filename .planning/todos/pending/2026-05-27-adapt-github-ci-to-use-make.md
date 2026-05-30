---
created: 2026-05-27T20:00:29.315Z
title: Adapt GitHub CI to use make and validate with act
area: tooling
files:
  - .github/workflows/main.yml
  - Makefile
---

## Problem

GitHub Actions workflow logic duplicates local development commands instead of using the Makefile as the canonical test and validation interface. This makes CI drift easier and leaves workflow syntax unvalidated locally.

## Solution

Adapt `.github/workflows/main.yml` to call Makefile targets, add any missing Makefile targets needed by CI, and validate the workflow with `act --validate`.

Tasks:

- [ ] Add `GITHUB_ACTIONS` check in `Makefile` so CI tox runs include `tox-gh-actions`.
- [ ] Add `tox` target to `Makefile`.
- [ ] Add `check-message-schemas` target to `Makefile`.
- [ ] Add `env-install-npm` target to `Makefile`.
- [ ] Update `.github/workflows/main.yml` to set up `uv` via `astral-sh/setup-uv`.
- [ ] Replace custom install and run scripts in `main.yml` with Makefile commands:
  - `make env-install-npm`
  - `make tox`
  - `make check-message-schemas`
  - `make dist-check`
- [ ] Validate changes with `act --validate`.
