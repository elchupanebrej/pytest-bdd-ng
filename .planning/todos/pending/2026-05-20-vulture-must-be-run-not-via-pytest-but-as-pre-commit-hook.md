---
created: 2026-05-20T14:23:11
title: Vulture must be run not via pytest but as pre-commit hook
area: tooling
files:
  - pyproject.toml (pre-commit config)
  - .pre-commit-config.yaml
---

## Problem

Vulture (dead code detection) is currently run through pytest but should be executed as a pre-commit hook instead. Running it via pytest mixes concerns and is not the standard approach for dead code detection tooling.

## Solution

Move Vulture execution from pytest integration to a pre-commit hook. Remove any pytest-based Vulture invocation and add a proper pre-commit hook entry in the project's pre-commit configuration.
