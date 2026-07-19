---
created: 20260712T144244
title: Fix Doc generation and move it inside act tool job for local runs
area: tooling
files:
  - .github/workflows/docs.yml
  - docs/conf.py
  - docs/
---

## Problem

Documentation generation currently lacks a reliable local development story. The `docs.yml` workflow exists for GitHub Actions/Act but:
1. `docs/conf.py` broke after the `__init__.py` cleanup — `pytest_bdd.__version__` no longer exists (resolved with a temporary `importlib.metadata` workaround)
2. No project-local skill or command exists for easily generating and viewing docs during development
3. The docs build requires `sphinx-build` with specific extras (`doc-gen`) but there's no documented local invocation

## Solution

1. Fix `docs/conf.py` properly (not just the temp workaround) to get version info from the package metadata
2. Ensure `docs.yml` works with `act` for local runs by validating the workflow
3. Create a local project skill (under `.agents/skills/`) that wraps the doc generation + server launch flow so it can be invoked during development without remembering CLI flags
4. Test end-to-end: `skill → sphinx-build → http.server`
