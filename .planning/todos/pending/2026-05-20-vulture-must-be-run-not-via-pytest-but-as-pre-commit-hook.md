---
created: 2026-05-20T14:23:11
title: Vulture must be run not via pytest but as pre-commit hook
area: tooling
files:
  - pyproject.toml (pre-commit config)
  - .pre-commit-config.yaml
  - .planning/spikes/004-vulture-pre-commit-hook/README.md
  - tests/cases/unit/unit/test_dead_code.py
---

## Problem

Vulture (dead code detection) is currently run through pytest but should be executed as a pre-commit hook instead. Running it via pytest mixes concerns and is not the standard approach for dead code detection tooling.

Spike 004 validated that vulture can move out of pytest. Current pytest gate also carries a file/line/message allowlist and stale-allowlist checks, but native vulture config plus whitelist is the preferred production path to avoid extra wrapper code.

## Solution

Implement native vulture setup first:

- Add `[tool.vulture]` config in `pyproject.toml` with `paths = ["src/pytest_bdd", "vulture_whitelist.py"]` and `min_confidence = 80`.
- Add native `jendrikseipp/vulture` pre-commit hook to `.pre-commit-config.yaml`.
- Convert current `KNOWN_FALSE_POSITIVES` from `tests/cases/unit/unit/test_dead_code.py` into `vulture_whitelist.py`.
- Remove pytest-based vulture test, or keep only minimal helper tests if needed.
- Ensure CI runs `pre-commit run vulture --all-files`.

Fallback only if native whitelist cannot model project false positives cleanly: use wrapper script from `.planning/spikes/004-vulture-pre-commit-hook/`.
