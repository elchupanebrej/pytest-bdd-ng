---
created: 2026-05-20T14:48:01
title: Improve library typing using best practices from awesome-python-typing
area: general
files:
  - src/pytest_bdd/** (all library source)
  - pyproject.toml (mypy config)
---

## Problem

Library typing needs improvement. Current typing practices may be outdated or incomplete. Additionally, `typing.cast` and `Any` should be treated as soft-deprecations — they weaken type safety and should be reviewed and minimized where possible.

## Solution

1. Review libraries from https://github.com/typeddjango/awesome-python-typing for best practices applicable to this project
2. Incorporate best approaches into the codebase (e.g., protocols, generics, TypeGuard, TypedDict, Literal, etc.)
3. Audit all usages of `Any` and `cast` — consider each as soft-deprecated, replace with stricter types where feasible
4. Update mypy configuration to enforce stricter typing rules
